#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb 检索器：关键词+topic+症状词检索，兼作写入前查重——库内此前零检索工具。

为什么存在（2026-10-04 缺陷分析结论）：
  0) 关键词匹配已归一（NFKC 全角转半角 + ASCII 大小写不敏感）；多词命中任一即保留，
     排序先看命中数；无直接命中时自动给 2-gram 近似候选。
  1) 症状词只在正文里：用户搜「挂了/卡死/不生效/黑窗」时，INDEX 钩子全是
     「结论词/修法词」，索引层 0 命中（实测），而规程只让人扫 INDEX——
     本工具默认全文检索，症状词直达正文。
  2) topic 只写不读：受控词表唯一消费点是写入校验，没有任何按领域过滤的
     手段——本工具 --topic 让 topic 字段第一次可读。
  3) 查重靠人肉读 INDEX：同族条目措辞互不重叠（「全量 PUT 事故家族」vs
     「option 写操作六步铁律」），写新条目前跑 --similar 给出同族候选。

用法：
    python kb_search.py <关键词...> [--topic t1,t2] [--dir pitfalls] [--limit 20]
    python kb_search.py --similar "候选标题或一句话描述" [--limit 5]

退出码：0 = 有结果或查重完成；1 = 无结果；2 = 用法/环境错误。
默认库路径取 AGENT_KB_PATH 环境变量，否则 ~/.agents/kb（与 kb_core 同源）。
"""
import argparse
import math
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kb_core import index_entry_lines, resolve_kb_path  # noqa: E402
from kb_validate import parse_frontmatter  # noqa: E402

CONTENT_DIRS = ("pitfalls", "tools", "workflow")
_INDEX_LINE_RE = re.compile(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)]+)\)\s*[—-]?\s*(.*)$")
# 中文按 2-gram 切（词边界未知时最稳的近似），英文/数字按连续词切
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]*")


def _tokens(text):
    """把任意文本切成检索 token：CJK 连续段 → 2-gram，其余 → 小写词。"""
    out = []
    for run in _CJK_RUN_RE.findall(text):
        if len(run) == 1:
            out.append(run)
        else:
            out.extend(run[i:i + 2] for i in range(len(run) - 1))
    out.extend(w.lower() for w in _WORD_RE.findall(text))
    return out


def _norm(text):
    """归一：NFKC（全角→半角）+ casefold（ASCII 大小写不敏感）。"""
    return unicodedata.normalize("NFKC", str(text)).casefold()


def _load_index_hooks(kb):
    """{归一路径: (标题, 钩子)}——钩子是「判断要不要读全文」的一手信息。"""
    index = kb / "INDEX.md"
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return {}
    hooks = {}
    for line in index_entry_lines(text):
        m = _INDEX_LINE_RE.match(line)
        if m:
            hooks[m.group(2).strip().replace("\\", "/")] = (m.group(1).strip(), m.group(3).strip())
    return hooks


def _load_entries(kb, only_dir=None, only_topics=None):
    """返回 [(rel_path, title, hook, frontmatter, body_text)]。

    frontmatter 解析复用 kb_validate.parse_frontmatter（单一实现，不存副本）。
    """
    hooks = _load_index_hooks(kb)
    entries = []
    for d in CONTENT_DIRS:
        if only_dir and d != only_dir:
            continue
        for f in sorted((kb / d).glob("*.md")):
            rel = f"{d}/{f.name}"
            try:
                text = f.read_text(encoding="utf-8")
            except Exception:
                continue  # 读不了的单条跳过，不拖垮整体检索
            fm, _err = parse_frontmatter(text)
            fm = fm or {}
            if only_topics is not None:
                vals = [x.strip() for x in str(fm.get("topic", "")).split(",") if x.strip()]
                if not only_topics.intersection(vals):
                    continue
            title, hook = hooks.get(rel, (f.stem, ""))
            entries.append((rel, title, hook, fm, text))
    return entries


def _score_entry(keywords, title, hook, fm, body):
    """返回 (总分, 命中关键词数, 命中行摘录)。

    权重：INDEX 钩子×3 > description×2 > 正文×1；关键词已归一（NFKC+casefold）。
    多关键词不再对缺词扣分：命中任一即保留，排序先看命中数再看权重。
    """
    desc = str(fm.get("description", ""))
    n_title, n_hook, n_desc, n_body = _norm(title), _norm(hook), _norm(desc), _norm(body)
    total = 0.0
    matched = 0
    excerpts = []
    for kw in keywords:
        s = 0.0
        if kw in n_title:
            s += 3.0
        if kw in n_hook:
            s += 3.0
        if kw in n_desc:
            s += 2.0
        if kw in n_body:
            s += 1.0
            for line in body.splitlines():
                if kw in _norm(line) and len(excerpts) < 3:
                    excerpts.append(line.strip()[:100])
        if s:
            matched += 1
        total += s
    return total, matched, excerpts


def cmd_search(kb, keywords, only_dir=None, only_topics=None, limit=10):
    entries = _load_entries(kb, only_dir, only_topics)
    nks = [_norm(k) for k in keywords if str(k).strip()]
    if not nks:
        return []
    scored = []
    for rel, title, hook, fm, body in entries:
        total, matched, excerpts = _score_entry(nks, title, hook, fm, body)
        if matched:
            scored.append((total, matched, rel, title, hook, excerpts))
    # 命中关键词数优先，其次权重和
    scored.sort(key=lambda x: (-x[1], -x[0]))
    return [(total, rel, title, hook, excerpts)
            for total, _matched, rel, title, hook, excerpts in scored[:limit]]


def cmd_similar(kb, query, limit=5):
    """写入前查重：query 与每条目的 标题+description+正文 做 token 重合度排序。

    指标用余弦相似度的朴素版（token 集合重合），同族措辞不同也能靠共享
    事故名词/方法名词浮上来——这正是「人肉读 INDEX 查重」漏掉的那类。
    """
    q_tokens = set(_tokens(query))
    if not q_tokens:
        return []
    entries = _load_entries(kb)
    scored = []
    for rel, title, hook, fm, body in entries:
        e_tokens = set(_tokens(f"{title} {fm.get('description', '')} {body}"))
        if not e_tokens:
            continue
        overlap = q_tokens & e_tokens
        if not overlap:
            continue
        # 余弦相似度：|交| / sqrt(|q|·|e|)；命中 QUERY 的稀缺 token 更有区分度
        cos = len(overlap) / math.sqrt(len(q_tokens) * len(e_tokens))
        shared = "、".join(sorted(overlap, key=len, reverse=True)[:6])
        scored.append((cos, rel, title, shared))
    scored.sort(key=lambda x: -x[0])
    return scored[:limit]


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 检索器（关键词/症状词/topic 过滤/写入前查重）")
    ap.add_argument("keywords", nargs="*", help="检索关键词（可多个，软 AND）")
    ap.add_argument("--topic", default=None, help="按 frontmatter topic 过滤，逗号分隔多值取并集")
    ap.add_argument("--dir", default=None, choices=CONTENT_DIRS, help="只搜某个目录")
    ap.add_argument("--similar", default=None, metavar="TEXT", help="写入前查重：给候选标题或一句话描述")
    ap.add_argument("--limit", type=int, default=None, help="结果条数上限（默认检索 10 / 查重 5）")
    ap.add_argument("--kb", default=None, help="库路径，默认 $AGENT_KB_PATH 或 ~/.agents/kb")
    args = ap.parse_args(argv)

    kb = resolve_kb_path(args.kb)
    if not kb.is_dir():
        print(f"[FAIL] 库目录不存在：{kb}")
        return 2

    topics = {x.strip() for x in args.topic.split(",") if x.strip()} if args.topic else None

    if args.similar is not None:
        results = cmd_similar(kb, args.similar, args.limit or 5)
        if not results:
            print("[无同族候选] 库内没有 token 重合的条目——大概率可以新建")
            return 1
        print(f"[查重] 与「{args.similar}」最相似的同族候选（写入前请先扩充这些）：")
        for cos, rel, title, shared in results:
            print(f"  {cos:.3f}  {rel} — {title}  ｜共享词：{shared}")
        return 0

    if not args.keywords:
        ap.error("需要至少一个关键词，或用 --similar 查重")
    results = cmd_search(kb, args.keywords, args.dir, topics, args.limit or 20)
    if not results:
        fb = cmd_similar(kb, " ".join(args.keywords), 5)
        if fb:
            print("[无结果] 关键词未直接命中；以下为 2-gram 近似候选（换说法或读全文）：")
            for cos, rel, title, shared in fb:
                print(f"  {cos:.3f}  {rel} — {title}  ｜共享词：{shared}")
            return 1
        print("[无结果] 关键词未直接命中，2-gram 也无重合；换个说法或去掉 --topic/--dir 再试"
              "（症状词：挂了/卡死/不生效 可直接当关键词）")
        return 1
    print(f"[检索] {len(results)} 条（关键词：{' '.join(args.keywords)}）：")
    for total, rel, title, hook, excerpts in results:
        print(f"  {total:5.1f}  {rel} — {title}")
        if hook:
            print(f"        钩子：{hook[:80]}")
        for ex in excerpts:
            print(f"        正文命中：{ex}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
