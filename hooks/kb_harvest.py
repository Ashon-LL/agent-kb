#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_harvest.py — 只读收割候选生成器（ZCode / OpenCode 会话库 + 当前工作区）。

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
    python kb_harvest.py --no-zcode             # 跳过 ZCode 会话库
    python kb_harvest.py --no-opencode          # 跳过 OpenCode 会话库
    python kb_harvest.py --no-jsonl             # 跳过各平台 JSONL 会话
    python kb_harvest.py --extra-sessions DIR   # 追加任意会话根（可重复）
    python kb_harvest.py --include-weak         # 连弱信号一起看（噪声较高）

会话来源**平台无关**：自动发现 DSH（~/.dsh/sessions）、Claude Code（~/.claude/projects）、
Codex（~/.codex/sessions）的 JSONL 会话，以及 --extra-sessions 指定的任意目录；
ZCode 与 OpenCode 各走自己的 SQLite 库。用户与助手的文本都会看，子代理与系统注入按各自格式排除。
"""
import argparse
import json
import re
import sqlite3
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


def collect_opencode_candidates(days=7, limit=100, db_path=None, include_weak=False):
    """从 OpenCode 会话库提取沉淀意图候选；返回 (候选列表, since_ts)。

    只读打开 ~/.local/share/opencode/opencode.db；取顶层会话的 user 消息，
    优先用 metadata.displayText（干净的用户输入），没有才退回 data.text。
    """
    since = int(time.time() * 1000) - max(1, int(days)) * 86400000
    db = Path(db_path).expanduser() if db_path else Path.home() / ".local/share/opencode/opencode.db"
    if not db.is_file():
        return [], since
    out = []
    seen = set()
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT m.time_created, m.data, s.title "
            "FROM session_message m LEFT JOIN session_v2 s ON s.id = m.session_id "
            "WHERE m.type = 'user' AND m.time_created > ? "
            "AND (s.parent_id IS NULL OR s.parent_id = '') "
            "ORDER BY m.time_created",
            (since,),
        )
        for ts, raw, title in rows:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            text = (data.get("metadata") or {}).get("displayText") or data.get("text") or ""
            text = str(text).strip()
            if not text or text in seen:
                continue
            strong = bool(TRIGGER_PATTERN.search(text))
            weak = bool(HEURISTIC.search(text))
            if not strong and not (include_weak and weak):
                continue
            seen.add(text)
            out.append({
                "source": "opencode-session",
                "platform": "opencode",
                "role": "user",
                "signal": "strong" if strong else "weak",
                "ts": ts,
                "time": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts / 1000)),
                "suggest_dir": _suggest_dir(text),
                "reason": _reason(text),
                "text": _excerpt(text),
                "session": title or "",
            })
            if len(out) >= limit:
                break
    finally:
        con.close()
    return out, since


# ── 平台无关的会话发现 ─────────────────────────────────────────────
# (平台名, 根目录解析, 文件匹配)。新平台按需追加；也可用 --extra-sessions 指定任意根。
SESSION_PLATFORM_ROOTS = (
    ("dsh", lambda home: home / ".dsh" / "sessions",
     lambda base: base.glob("*/session-*/session.v4.jsonl.zstd")),
    ("claude-code", lambda home: home / ".claude" / "projects",
     lambda base: base.glob("*/*.jsonl")),
    ("codex", lambda home: home / ".codex" / "sessions",
     lambda base: base.glob("**/*.jsonl")),
)


def _read_jsonl(path):
    """读 plain / zstd 压缩的 JSONL，返回文本（zstd 缺失时抛 ImportError）。"""
    raw = Path(path).read_bytes()
    if str(path).endswith(".zstd"):
        import zstandard
        import io
        raw = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)).read()
    return raw.decode("utf-8", "replace")


def _text_of(content):
    """从字符串或内容块数组里取纯文本（只取 text 块，跳过 reasoning 等）。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def _to_ms(value):
    """把毫秒 / 秒 / ISO 时间统一成毫秒；解析失败返回 0。"""
    if isinstance(value, (int, float)):
        return int(value * 1000) if value and value < 1e12 else int(value or 0)
    if isinstance(value, str) and value:
        try:
            from datetime import datetime
            return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
        except Exception:
            return 0
    return 0


def iter_dsh_messages(path):
    """DSH session.v4.jsonl(.zstd)：顶层会话的 user / assistant 文本。"""
    depth = 0
    for line in _read_jsonl(path).splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        kind = event.get("type")
        if kind == "session":
            depth = event.get("delegationDepth") or 0
            continue
        if depth:
            continue
        data = event.get("data") or {}
        if kind == "user/message":
            if (data.get("source") or {}).get("kind") != "user":
                continue
            yield "user", event.get("time") or 0, _text_of(data.get("content"))
        elif kind == "assistant/message":
            yield "assistant", event.get("time") or 0, _text_of((data.get("message") or {}).get("content"))


def iter_generic_messages(path):
    """通用 JSONL 会话适配：识别 role / message.role / type=user|assistant。"""
    for line in _read_jsonl(path).splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        role = event.get("role")
        message = event.get("message") if isinstance(event.get("message"), dict) else None
        if not role and message:
            role = message.get("role")
        if not role and event.get("type") in ("user", "assistant"):
            role = event["type"]
        if role not in ("user", "assistant"):
            continue
        source = message if message else event
        text = _text_of(source.get("content")) or _text_of(event.get("text")) or _text_of(event.get("content"))
        ts = event.get("time") or event.get("timestamp") or event.get("created_at") or event.get("created")
        yield role, _to_ms(ts), text


def collect_jsonl_candidates(days=7, limit=100, extra_roots=None, include_weak=False):
    """扫描各平台会话文件（DSH / Claude Code / Codex / 通用 JSONL），平台无关。

    只收**强信号**（TRIGGER_PATTERN）或显式打开 include_weak 时的弱信号；
    用户与助手文本都看，子代理与系统注入按各自格式排除。
    """
    since = int(time.time() * 1000) - max(1, int(days)) * 86400000
    home = Path.home()
    files = []
    for name, base_of, globber in SESSION_PLATFORM_ROOTS:
        base = base_of(home)
        if base.exists():
            files.extend((name, p) for p in globber(base))
    for extra in extra_roots or []:
        base = Path(extra)
        if not base.exists():
            continue
        files.extend(("custom", p) for p in base.rglob("*")
                     if p.is_file() and (p.name.endswith(".jsonl") or p.name.endswith(".jsonl.zstd")))
    out = []
    for platform, path in sorted(files, key=lambda item: str(item[1])):
        iterator = iter_dsh_messages(path) if platform == "dsh" else iter_generic_messages(path)
        try:
            for role, ts, text in iterator:
                if ts and ts < since:
                    continue
                text = (text or "").strip()
                if not text:
                    continue
                strong = bool(TRIGGER_PATTERN.search(text))
                weak = bool(HEURISTIC.search(text))
                if not strong and not (include_weak and weak):
                    continue
                out.append({
                    "source": f"{platform}-session",
                    "platform": platform,
                    "role": role,
                    "signal": "strong" if strong else "weak",
                    "ts": ts,
                    "time": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts / 1000)) if ts else "",
                    "suggest_dir": _suggest_dir(text),
                    "reason": _reason(text),
                    "text": _excerpt(text),
                    "session": Path(path).parent.name,
                })
                if len(out) >= limit:
                    return out, since
        except Exception:
            continue
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
        "| # | 时间 | 平台 | 角色 | 信号 | 建议目录 | 类型 | 片段 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    if session:
        for i, c in enumerate(session, 1):
            lines.append(
                f"| {i} | {c['time']} | {c.get('platform', 'zcode')} | {c.get('role', 'user')} | "
                f"{c['signal']} | `{c['suggest_dir']}` | {c['reason']} | {_cell(c['text'])} |"
            )
    else:
        lines.append("| — | — | — | — | — | — | — | （无） |")

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
    ap.add_argument("--opencode-db", default=None, help="OpenCode 会话库路径（默认 ~/.local/share/opencode/opencode.db）")
    ap.add_argument("--extra-sessions", action="append", default=[], metavar="DIR",
                    help="额外会话根目录（可重复；递归找 *.jsonl / *.jsonl.zstd）")
    ap.add_argument("--no-zcode", action="store_true", help="不扫 ZCode 会话库")
    ap.add_argument("--no-opencode", action="store_true", help="不扫 OpenCode 会话库")
    ap.add_argument("--no-jsonl", action="store_true",
                    help="不扫各平台 JSONL 会话（DSH / Claude Code / Codex 等）")
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

    if not args.no_session and not args.no_zcode:
        try:
            session, since = collect_session_candidates(
                args.days, args.limit, args.db, args.include_weak
            )
            sources.append(f"ZCode 会话库（最近 {args.days} 天）")
        except Exception as exc:
            print(f"[WARN] ZCode 会话库不可读，降级跳过：{exc}", file=sys.stderr)

    if not args.no_session and not args.no_opencode:
        try:
            opencode_rows, _ = collect_opencode_candidates(
                args.days, args.limit, args.opencode_db, args.include_weak
            )
            session.extend(opencode_rows)
            if opencode_rows:
                sources.append(f"OpenCode 会话库（最近 {args.days} 天）")
        except Exception as exc:
            print(f"[WARN] OpenCode 会话库不可读，降级跳过：{exc}", file=sys.stderr)

    if not args.no_session and not args.no_jsonl:
        try:
            jsonl_rows, _ = collect_jsonl_candidates(
                args.days, args.limit, args.extra_sessions, args.include_weak
            )
            session.extend(jsonl_rows)
            platforms = sorted({row["platform"] for row in jsonl_rows})
            if platforms:
                sources.append(f"平台会话库 {', '.join(platforms)}（最近 {args.days} 天）")
        except Exception as exc:
            print(f"[WARN] 平台会话库不可读，降级跳过：{exc}", file=sys.stderr)

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
    by_source = {}
    for row in session:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
    detail = " / ".join(f"{k} {v}" for k, v in sorted(by_source.items())) or "0"
    print(f"     会话 {len(session)} 条（{detail}）/ 工作区 {len(workspace)} 条（未写入经验库）")
    return 0


if __name__ == "__main__":
    sys.exit(main())