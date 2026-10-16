#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb 触发词挖掘器：让关键词表能持续自我更新（2026-10-16）。

背景：TRIGGER_PATTERN 是写死的正则（hook 是同步脚本、不能调 LLM），
此前新词靠人工扫会话挖掘。本工具把「扫 → 判 → 汇总」自动化：

  1. 从 ZCode 会话库提取**新增的**真用户消息（按状态文件的时间戳增量）
  2. 用现有 TRIGGER_PATTERN 过滤（已命中的跳过——无需再挖）
  3. 宽启发式预筛（含记忆/经验类词的消息），控制 Jev 调用量
  4. 用 **Jev** 逐条判定「是否在要求记录/纠正经验或规则」（noul 类型）
  5. 汇总判为 yes 的消息，提取高频 n-gram 作为**候选词**
  6. 产出报告（含样本与候选词）→ 人工过目后加入 TRIGGER_PATTERN

设计要点：Jev 只做**筛选**（把 5 万条消息缩到几十条候选），**确认仍由人做**——
候选词进词表前必须过目，避免误报词进入（用户 2026-10-16：「关键词应该能不断增加更新」）。

用法：
    python kb_trigger_miner.py                # 增量挖掘（用状态文件）
    python kb_trigger_miner.py --all           # 全量（重扫所有会话）
    python kb_trigger_miner.py --limit 200     # 本次最多判多少条（控 Jev 调用量）
    python kb_trigger_miner.py --out report.md # 报告输出路径
"""
import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_core import TRIGGER_PATTERN  # noqa: E402

# Jev 调用器位置探测（技能目录；仓库内为 skills/agent-jev/）
_THIS = Path(__file__).resolve().parent
for _cand in (Path.home() / ".agents/skills/agent-jev",
              _THIS.parent / "skills/agent-jev",
              _THIS.parent.parent / "agent-jev/skills/agent-jev"):
    if (_cand / "jev.py").is_file():
        sys.path.insert(0, str(_cand))
        break

DB = Path.home() / ".zcode/cli/db/db.sqlite"
STATE = Path.home() / ".agents/kb/.trigger-miner-state.json"

# 宽启发式预筛（只为压 Jev 调用量，误筛掉的由下一轮补）
HEURISTIC = re.compile(
    r"记|忘|经验|教训|知识|沉淀|规矩|纪律|规范|原则|约定|以后|下次|别再|注意|"
    r"希望|要求|必须|一律|不要|改|更新|纠正|订正|错|对不上|应该")

JEV_Q = ("is_precipitate",
         {"type": "noul",
          "instructions": "这条用户消息是否在要求：记录/沉淀经验教训、记住某条规则或偏好、"
                          "纠正此前记错的内容？只回答是不是（普通任务指令、闲聊、提问事实都不算）。"})


def load_since():
    try:
        return json.loads(STATE.read_text(encoding="utf-8")).get("since_ts", 0)
    except Exception:
        return 0


def save_since(ts):
    STATE.write_text(json.dumps({"since_ts": ts}, ensure_ascii=False), encoding="utf-8")


def extract_user_msgs(since_ts=0):
    """只读提取 real_user 顶层会话消息。"""
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    cur = con.cursor()
    keep = {}
    for mid, sid, data in cur.execute("SELECT id, session_id, data FROM message"):
        if not re.match(r"^sess_[0-9a-f]{8}-", sid or ""):
            continue
        try:
            d = json.loads(data)
        except Exception:
            continue
        if d.get("role") != "user" or (d.get("semantics") or {}).get("origin") != "real_user":
            continue
        ts = (d.get("time") or {}).get("created", 0)
        if ts < since_ts:
            continue
        keep[mid] = ts
    out = []
    for mid, data in cur.execute("SELECT message_id, data FROM part"):
        if mid not in keep:
            continue
        try:
            pd = json.loads(data)
        except Exception:
            continue
        if pd.get("type") == "text" and pd.get("text"):
            out.append((keep[mid], pd["text"]))
    con.close()
    # 去重（用户常重复发同一句）
    seen, uniq = set(), []
    for ts, text in sorted(out):
        if text not in seen:
            seen.add(text)
            uniq.append((ts, text))
    return uniq


def jev_judge(text, timeout=12):
    """用 Jev 判定是否沉淀意图；失败返回 None（不计入）。"""
    try:
        import jev
        out = jev.call({"state": text[:1500],
                        "questions": {JEV_Q[0]: JEV_Q[1]}},
                       retries=2, timeout=6, deadline=timeout)
        a = (out.get("answers") or {}).get(JEV_Q[0]) or {}
        p = a.get("noul")
        return float(p) if isinstance(p, (int, float)) else None
    except Exception:
        return None


def ngrams(text, n=3):
    """中文 n-gram（候选词来源）。"""
    out = []
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        for i in range(len(run) - n + 1):
            out.append(run[i:i + n])
    return out


def main():
    ap = argparse.ArgumentParser(description="kb 触发词挖掘器（Jev 筛选 + 人工确认）")
    ap.add_argument("--all", action="store_true", help="重扫全部会话（忽略状态文件）")
    ap.add_argument("--limit", type=int, default=150, help="本次最多判多少条（控 Jev 调用量）")
    ap.add_argument("--threshold", type=float, default=0.6, help="Jev 判定阈值")
    ap.add_argument("--out", default=None, help="报告路径")
    args = ap.parse_args()

    since = 0 if args.all else load_since()
    rows = extract_user_msgs(since)
    print(f"新增真用户消息（去重后）{len(rows)} 条" + (f"（自 ts>{since}）" if since else "（全量）"))

    # 已命中现有词表的跳过
    todo = [(ts, t) for ts, t in rows if not TRIGGER_PATTERN.search(t)]
    print(f"现有词表已覆盖 {len(rows)-len(todo)} 条；待判 {len(todo)} 条")

    # 宽预筛压量
    cand = [(ts, t) for ts, t in todo if HEURISTIC.search(t)][:args.limit]
    print(f"启发式预筛后送 Jev：{len(cand)} 条（上限 {args.limit}）")

    hits, misses, fail = [], [], 0
    for i, (ts, text) in enumerate(cand, 1):
        p = jev_judge(text)
        if p is None:
            fail += 1
            continue
        if p >= args.threshold:
            hits.append((p, text))
        else:
            misses.append((p, text))
        if i % 20 == 0:
            print(f"  ...已判 {i}/{len(cand)}（命中 {len(hits)}）")

    print(f"\nJev 判定：命中 {len(hits)} / 未命中 {len(misses)} / 失败 {fail}")

    # 候选词：命中消息的 n-gram，剔除已在词表里的
    cnt = Counter()
    for _, text in hits:
        for g in set(ngrams(text)):
            if not TRIGGER_PATTERN.search(g):
                cnt[g] += 1
    # 过滤：≥2 条不同消息 + 不以虚词开头/结尾（n-gram 会切出「的模型」「支持的」这类碎片）
    STOP_CHARS = set("的是了在有和与或就都也而不很太没你要我他她它这那会能把被让对从向以为吧吗呢啊")
    def _good(w):
        return w[0] not in STOP_CHARS and w[-1] not in STOP_CHARS
    cand_words = [(w, c) for w, c in cnt.most_common(200) if c >= 2 and _good(w)][:40]

    report = ["# kb 触发词挖掘报告", "",
              f"生成：{time.strftime('%Y-%m-%d %H:%M')}｜扫描自 ts>{since}｜"
              f"待判 {len(cand)}｜Jev 命中 {len(hits)}｜失败 {fail}", "",
              "## 候选词（出现在 ≥2 条命中消息的 3-gram，人工过目后加入 TRIGGER_PATTERN）", ""]
    report += [f"- `{w}`（{c} 条）" for w, c in cand_words] or ["（无）"]
    report += ["", "## Jev 判为「沉淀意图」但现有词表未命中的消息（抽样）", ""]
    for p, text in sorted(hits, reverse=True)[:40]:
        report.append(f"- [{p:.2f}] {text.strip()[:200]}")
    report += ["", "## 判为「非沉淀意图」的边界样本（校准用，抽样）", ""]
    for p, text in sorted(misses)[:15]:
        report.append(f"- [{p:.2f}] {text.strip()[:150]}")

    out = Path(args.out) if args.out else Path.home() / ".agents/kb/.trigger-miner-report.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print(f"报告 -> {out}")

    if rows:
        save_since(max(ts for ts, _ in rows))
        print(f"状态已更新（下次从此时间戳继续）")


if __name__ == "__main__":
    main()
