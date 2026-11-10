#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_harvest.py — 只读收割候选生成器（ZCode 会话库 + 当前工作区）。

只做「提取候选」，**不调用 LLM、不写入经验库**；确认与落盘仍由人和 kb 规程完成。
设计参考：
  - Mem0：提取事实 → 去重 → 按查询召回（Add / Extract / Recall）
  - LangMem：语义记忆（事实）、情节记忆（经历）、程序记忆（规则）分层
  - Zep：事实带来源与时序失效
  - Basic Memory：本地 Markdown，可检查、可迁移
  - A-MEM：Zettelkasten 式动态索引与双链

用法：
    python kb_harvest.py                       # 最近 7 天 + 当前工作区
    python kb_harvest.py --days 30
    python kb_harvest.py --workspace . --out report.md
    python kb_harvest.py --json candidates.json
    python kb_harvest.py --no-session           # 只扫工作区
    python kb_harvest.py --no-workspace         # 只扫会话库
    python kb_harvest.py --include-weak         # 连弱信号一起看（噪声较高）
"""
import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_core import TRIGGER_PATTERN, index_entry_lines, resolve_kb_path  # noqa: E402
from kb_trigger_miner import HEURISTIC, extract_user_msgs  # noqa: E402

WORKSPACE_HINTS = ("指南", "手册", "上手", "给其他项目", "交接", "总结", "复盘", "教训")
DOC_DIRS = {"docs", "notes", "交付", ".analysis"}
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "library", "library-template", ".pytest_cache", ".codegraph",
}
MAX_FILE_BYTES = 200_000
MAX_TEXT = 400


def _norm(text):
    return unicodedata.normalize("NFKC", str(text)).casefold()


def _excerpt(text, limit=MAX_TEXT):
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _cell(text):
    return _excerpt(text).replace("|", "\\|")


def _suggest_dir(text):
    if re.search(r"坑|失败|报错|挂了|卡死|不生效|踩坑|教训|反模式", text):
        return "pitfalls"
    if re.search(r"流程|规范|方法|指南|手册|原则|约定|以后|下次|协作", text):
        return "workflow"
    return "tools"


def _reason(text):
    if re.search(r"纠正|订正|错|对不上|搞错|臆测|忘了吗", text):
        return "纠错/防复发"
    if re.search(r"经验|教训|复盘|总结|踩坑|坑", text):
        return "教训/复盘"
    if re.search(r"必须|一律|不要|别再|以后|下次|规范|原则|约定", text):
        return "规则/约束"
    return "沉淀意图"


def _index_keys(kb):
    """INDEX.md 中已有的标题与相对路径，用于跳过已收录内容。"""
    keys = set()
    try:
        text = (kb / "INDEX.md").read_text(encoding="utf-8")
    except Exception:
        return keys
    for line in index_entry_lines(text):
        m = re.match(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)]+)\)", line)
        if m:
            keys.add(_norm(m.group(1).strip()))
            keys.add(_norm(m.group(2).strip().replace("\\", "/")))
    return keys


def collect_session_candidates(days=7, limit=100, db_path=None, include_weak=False):
    """从 ZCode 会话库提取沉淀意图候选；返回 (候选列表, since_ts)。

    默认只收**强信号**（TRIGGER_PATTERN 命中：记住/沉淀/以后别/纳入kb 等）。
    include_weak=True 时，把 HEURISTIC 命中但触发词未命中的消息也纳入，
    并标记 signal=weak——这类多是“更新/改/错”等日常词，噪声较高。
    """
    since = int(time.time() * 1000) - max(1, int(days)) * 86400000
    rows = extract_user_msgs(since, db_path)
    out = []
    for ts, text in rows:
        strong = bool(TRIGGER_PATTERN.search(text))
        weak = bool(HEURISTIC.search(text))
        if not strong and not (include_weak and weak):
            continue
        out.append({
            "source": "zcode-session",
            "signal": "strong" if strong else "weak",
            "ts": ts,
            "time": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts / 1000)),
            "suggest_dir": _suggest_dir(text),
            "reason": _reason(text),
            "text": _excerpt(text),
        })
        if len(out) >= limit:
            break
    return out, since


def collect_workspace_candidates(root=".", limit=100, known=None):
    """扫描当前工作区的经验型 Markdown（文件名/目录启发式）。"""
    root = Path(root).resolve()
    known = known or set()
    out = []
    for p in sorted(root.rglob("*.md")):
        try:
            rel_parts = p.relative_to(root).parts
        except ValueError:
            continue
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = "/".join(rel_parts)
        in_doc = bool(rel_parts) and rel_parts[0] in DOC_DIRS
        name_hit = any(h in p.stem for h in WORKSPACE_HINTS)
        if not (in_doc or name_hit):
            continue
        title = p.stem
        for line in text.splitlines():
            if line.strip().startswith("# "):
                title = line.strip()[2:].strip()[:120]
                break
        if _norm(title) in known or _norm(rel) in known:
            continue
        out.append({
            "source": "workspace",
            "path": rel,
            "title": title,
            "suggest_dir": _suggest_dir(f"{title} {text[:500]}"),
            "reason": "位于经验型文档目录" if in_doc else "文件名命中经验型关键词",
            "excerpt": _excerpt(text, 240),
        })
        if len(out) >= limit:
            break
    return out


def render_markdown(session, workspace, meta):
    lines = [
        "# kb 收割候选",
        "",
        "> 只读生成，**未写入经验库**。确认前不要直接落盘。",
        "> 机制参考：Mem0 的提取/去重/召回、LangMem 的语义-情节-程序分层、"
        "Zep 的事实来源与时序、Basic Memory 的本地 Markdown、A-MEM 的双链索引。",
        "",
        f"- 生成：{meta['generated']}",
        f"- 来源：{meta['sources']}",
        f"- 候选：会话 {len(session)} / 工作区 {len(workspace)}",
        "",
        "## 会话候选",
        "",
        "| # | 时间 | 信号 | 建议目录 | 类型 | 片段 |",
        "|---|---|---|---|---|---|",
    ]
    if session:
        for i, c in enumerate(session, 1):
            lines.append(
                f"| {i} | {c['time']} | {c['signal']} | `{c['suggest_dir']}` | {c['reason']} | {_cell(c['text'])} |"
            )
    else:
        lines.append("| — | — | — | — | — | （无） |")

    lines += [
        "",
        "## 工作区候选",
        "",
        "| # | 路径 | 建议目录 | 标题 | 理由 |",
        "|---|---|---|---|---|",
    ]
    if workspace:
        for i, c in enumerate(workspace, 1):
            lines.append(
                f"| {i} | `{c['path']}` | `{c['suggest_dir']}` | {_cell(c['title'])} | {c['reason']} |"
            )
    else:
        lines.append("| — | — | — | — | （无） |")

    lines += [
        "",
        "## 下一步",
        "",
        "1. 人工筛掉项目专属状态、一次性上下文、可从代码/Git 推导的内容。",
        "2. 对保留项跑 `python ~/.agents/kb/kb_search.py --similar \"<候选标题或一句话描述>\"` 查重。",
        "3. 按 `skill/SKILL.md` 的写入规程落盘：七字段 frontmatter、正文三段式、更新 INDEX.md。",
        "4. 跑 `python ~/.agents/kb/kb_validate.py`，看到 `[PASS]` 才算完。",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 收割候选生成器（只读，不写入）")
    ap.add_argument("--days", type=int, default=7, help="会话回看天数（默认 7）")
    ap.add_argument("--limit", type=int, default=100, help="每类候选上限（默认 100）")
    ap.add_argument("--db", default=None, help="ZCode 会话库路径（默认 ~/.zcode/cli/db/db.sqlite）")
    ap.add_argument("--workspace", default=".", help="工作区根目录（默认当前目录）")
    ap.add_argument("--out", default=None, help="Markdown 报告路径（默认 ~/.agents/kb/HARVEST-CANDIDATES.md）")
    ap.add_argument("--json", default=None, help="额外输出 JSON 路径")
    ap.add_argument("--no-session", action="store_true", help="不扫会话库")
    ap.add_argument("--no-workspace", action="store_true", help="不扫工作区")
    ap.add_argument("--include-weak", action="store_true",
                    help="把“更新/改/错”等弱信号也纳入（噪声较高，默认关闭）")
    args = ap.parse_args(argv)

    kb = resolve_kb_path()
    known = _index_keys(kb)
    session, workspace = [], []
    sources = []

    if not args.no_session:
        try:
            session, since = collect_session_candidates(
                args.days, args.limit, args.db, args.include_weak
            )
            sources.append(f"ZCode 会话库（最近 {args.days} 天）")
        except Exception as exc:
            print(f"[WARN] 会话库不可读，降级跳过：{exc}", file=sys.stderr)

    if not args.no_workspace:
        workspace = collect_workspace_candidates(args.workspace, args.limit, known)
        sources.append(f"当前工作区（{Path(args.workspace).resolve()}）")

    meta = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "sources": "；".join(sources) or "（未启用任何来源）",
    }
    report = render_markdown(session, workspace, meta)

    out = Path(args.out) if args.out else kb / "HARVEST-CANDIDATES.md"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    except Exception as exc:
        print(f"[FAIL] 报告写入失败：{exc}", file=sys.stderr)
        return 2

    if args.json:
        payload = {"meta": meta, "session": session, "workspace": workspace}
        try:
            Path(args.json).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:
            print(f"[WARN] JSON 写入失败：{exc}", file=sys.stderr)

    print(f"[OK] 候选报告 -> {out}")
    print(f"     会话 {len(session)} 条 / 工作区 {len(workspace)} 条（未写入经验库）")
    return 0


if __name__ == "__main__":
    sys.exit(main())