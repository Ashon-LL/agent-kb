#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_audit.py — 只读库审计：同族重复、零入链、过期待复核、topic 分布。

**只产出报告，不修改任何条目**。重复/合并/删条目必须人工确认后按
`skill/SKILL.md` 的合并规程执行，并跑 `kb_validate.py`。

设计参考：A-MEM 的 Zettelkasten 双链、Zep 的事实时效、Basic Memory 的可检查本地库。

用法：
    python kb_audit.py                     # 默认库，阈值 0.55
    python kb_audit.py --threshold 0.45    # 更宽松的同族候选
    python kb_audit.py --stale-days 180    # 超过 180 天未复核的条目
    python kb_audit.py --json audit.json
"""
import argparse
import json
import math
import re
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_core import resolve_kb_path  # noqa: E402
from kb_search import _load_entries, _tokens  # noqa: E402

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
STATUS_RE = re.compile(r"版本|现行|已失效|已删除|已下线|迁移到|改用")


def _strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _date(value):
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except Exception:
        return None


def _docs(entries):
    out = []
    for rel, title, _hook, fm, text in entries:
        body = _strip_frontmatter(text)
        # 标题/描述重复一次提高权重；正文只取前 800 字，避免长文稀释相似度。
        tokens = set(_tokens(f"{title} {title} {fm.get('description', '')} "
                             f"{fm.get('description', '')} {body[:800]}"))
        out.append({"rel": rel, "title": title, "fm": fm, "body": body,
                    "tokens": tokens})
    return out


def duplicate_pairs(entries, threshold=0.55, top=30):
    """按 token 余弦相似度找同族候选（不自动合并）。"""
    docs = _docs(entries)
    pairs = []
    for i in range(len(docs)):
        a = docs[i]
        if not a["tokens"]:
            continue
        for j in range(i + 1, len(docs)):
            b = docs[j]
            if not b["tokens"]:
                continue
            overlap = a["tokens"] & b["tokens"]
            if not overlap:
                continue
            cos = len(overlap) / math.sqrt(len(a["tokens"]) * len(b["tokens"]))
            if cos >= threshold:
                pairs.append({
                    "cos": round(cos, 3),
                    "a": a["rel"], "a_title": a["title"],
                    "b": b["rel"], "b_title": b["title"],
                    "shared": "、".join(sorted(overlap, key=len, reverse=True)[:8]),
                })
    pairs.sort(key=lambda x: -x["cos"])
    return pairs[:top]


def orphan_entries(entries):
    """没有任何其他条目 [[链接]] 指向的条目。"""
    docs = _docs(entries)
    names = {}
    for d in docs:
        name = str(d["fm"].get("name") or Path(d["rel"]).stem)
        names[name] = d["rel"]
        names[d["title"]] = d["rel"]
    inlinks = Counter()
    for d in docs:
        for target in LINK_RE.findall(d["body"]):
            target = target.split("|", 1)[0].strip()
            dest = names.get(target)
            if dest:
                inlinks[dest] += 1
    return [{"rel": d["rel"], "title": d["title"]}
            for d in docs if inlinks[d["rel"]] == 0]


def stale_entries(entries, stale_days=180):
    """verified/date 超过 stale_days 未复核的条目；含状态词的单独标记。"""
    today = date.today()
    out = []
    for rel, title, _hook, fm, text in entries:
        d = _date(fm.get("verified") or fm.get("date"))
        if not d:
            continue
        age = (today - d).days
        if age <= stale_days:
            continue
        out.append({
            "rel": rel,
            "title": title,
            "verified": str(fm.get("verified") or fm.get("date")),
            "age_days": age,
            "volatile": bool(STATUS_RE.search(_strip_frontmatter(text))),
        })
    out.sort(key=lambda x: -x["age_days"])
    return out


def link_suggestions(entries, orphans, top=3, threshold=0.20):
    """为孤儿条目给出入链建议（只建议，不自动写入）。"""
    docs = _docs(entries)
    by_rel = {d["rel"]: d for d in docs}
    out = []
    for o in orphans:
        src = by_rel.get(o["rel"])
        if not src or not src["tokens"]:
            continue
        scored = []
        for d in docs:
            if d["rel"] == src["rel"] or not d["tokens"]:
                continue
            overlap = src["tokens"] & d["tokens"]
            if not overlap:
                continue
            cos = len(overlap) / math.sqrt(len(src["tokens"]) * len(d["tokens"]))
            if cos >= threshold:
                scored.append((cos, d["rel"], d["title"]))
        scored.sort(reverse=True)
        if scored:
            out.append({
                "rel": src["rel"],
                "title": src["title"],
                "suggestions": [
                    {"cos": round(c, 3), "rel": r, "title": t}
                    for c, r, t in scored[:top]
                ],
            })
    return out


def topic_distribution(entries):
    cnt = Counter()
    for _rel, _title, _hook, fm, _text in entries:
        for t in str(fm.get("topic", "")).split(","):
            t = t.strip()
            if t:
                cnt[t] += 1
    return dict(cnt.most_common())


def render_markdown(kb, entries, pairs, orphans, links, stale, topics, meta):
    lines = [
        "# kb 库审计报告",
        "",
        "> **只读报告，未修改任何条目**。重复/合并/删除必须人工确认后按 SKILL 规程执行。",
        "",
        f"- 库：`{kb}`",
        f"- 条目：{len(entries)}",
        f"- 生成：{meta['generated']}",
        f"- 同族阈值：{meta['threshold']}｜过期阈值：{meta['stale_days']} 天",
        "",
        f"## 1. 同族重复候选（{len(pairs)} 对）",
        "",
        "| 相似度 | A | B | 共享词 |",
        "|---|---|---|---|",
    ]
    if pairs:
        for p in pairs:
            lines.append(f"| {p['cos']:.3f} | `{p['a']}` — {p['a_title']} | "
                         f"`{p['b']}` — {p['b_title']} | {p['shared']} |")
    else:
        lines.append("| — | — | — | （无） |")

    lines += [
        "",
        f"## 2. 孤儿入链建议（{len(links)} 条孤儿有候选）",
        "",
        "> 只建议，不自动写入；只补真实同族关系，禁止为凑指标硬拉。",
        "",
        "| 孤儿 | 建议链到 | 相似度 |",
        "|---|---|---|",
    ]
    if links:
        for item in links:
            for s in item["suggestions"]:
                lines.append(f"| `{item['rel']}` | `{s['rel']}` — {s['title']} | {s['cos']:.3f} |")
    else:
        lines.append("| — | — | — |")

    lines += [
        "",
        f"## 3. 零入链条目（{len(orphans)} 条）",
        "",
        "> 只能靠 INDEX 文本命中找到，无法从相关条目跳转。补真实关联，不要为凑指标硬拉。",
        "",
    ]
    lines += [f"- `{o['rel']}` — {o['title']}" for o in orphans] or ["- （无）"]

    lines += [
        "",
        f"## 4. 过期/待复核（{len(stale)} 条）",
        "",
        "| 条目 | verified | 天数 | 含状态词 |",
        "|---|---|---|---|",
    ]
    if stale:
        for s in stale:
            lines.append(f"| `{s['rel']}` | {s['verified']} | {s['age_days']} | "
                         f"{'是' if s['volatile'] else '否'} |")
    else:
        lines.append("| — | — | — | — |")

    lines += [
        "",
        "## 5. topic 分布",
        "",
        "| topic | 条数 |",
        "|---|---|",
    ]
    lines += [f"| `{t}` | {c} |" for t, c in topics.items()] or ["| — | — |"]

    lines += [
        "",
        "## 下一步",
        "",
        "1. 同族候选逐对读全文，确认是否同一事实；合并按 SKILL「合并既有条目」执行。",
        "2. 入链建议只补真实同族关系，禁止硬拉。",
        "3. 过期条目先复核再改结论；无法确认的标为待验证，不删。",
        "4. 全部改动后跑 `python ~/.agents/kb/kb_validate.py`，见 `[PASS]` 才算完。",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 库审计（只读，不改条目）")
    ap.add_argument("--kb", default=None, help="库路径，默认 $AGENT_KB_PATH 或 ~/.agents/kb")
    ap.add_argument("--threshold", type=float, default=0.55, help="同族相似度阈值（默认 0.55）")
    ap.add_argument("--top", type=int, default=30, help="同族候选最多输出多少对")
    ap.add_argument("--stale-days", type=int, default=180, help="超过多少天未复核算过期")
    ap.add_argument("--out", default=None, help="Markdown 报告路径")
    ap.add_argument("--json", default=None, help="额外输出 JSON 路径")
    args = ap.parse_args(argv)

    kb = resolve_kb_path(args.kb)
    if not kb.is_dir():
        print(f"[FAIL] 库目录不存在：{kb}", file=sys.stderr)
        return 2
    entries = _load_entries(kb)
    if not entries:
        print(f"[FAIL] 库内没有条目：{kb}", file=sys.stderr)
        return 2

    pairs = duplicate_pairs(entries, args.threshold, args.top)
    orphans = orphan_entries(entries)
    links = link_suggestions(entries, orphans)
    stale = stale_entries(entries, args.stale_days)
    topics = topic_distribution(entries)
    meta = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "threshold": args.threshold,
        "stale_days": args.stale_days,
    }
    report = render_markdown(kb, entries, pairs, orphans, links, stale, topics, meta)

    out = Path(args.out) if args.out else kb / "AUDIT-REPORT.md"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    except Exception as exc:
        print(f"[FAIL] 报告写入失败：{exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {"meta": meta, "entries": len(entries), "duplicates": pairs,
                   "orphans": orphans, "links": links, "stale": stale, "topics": topics}
        try:
            Path(args.json).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            print(f"[WARN] JSON 写入失败：{exc}", file=sys.stderr)

    print(f"[OK] 审计报告 -> {out}")
    print(f"     条目 {len(entries)}｜同族 {len(pairs)} 对｜零入链 {len(orphans)}｜"
          f"入链建议 {len(links)}｜过期 {len(stale)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())