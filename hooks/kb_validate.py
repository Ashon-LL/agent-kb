#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb 库校验器：在写入当下/收尾时拦住坏数据，不依赖事后人工体检。

检查项（对应任务书 P0-3 验收）：
  1) 条目 frontmatter 必填字段齐全：name / description / type / source / date
  2) type ∈ {tool, workflow, pitfall}，且与所在目录一致（tools/ workflow/ pitfalls/）
  3) [[双链]] 指向存在的条目（按文件名 slug 或 frontmatter.name 解析）
  4) 索引行数 == 磁盘 .md 条目数
  5) 索引路径集合 == 磁盘条目路径集合（新增/删除条目后漏更新索引，双向）

设计：与读库逻辑同源 —— 复用 hooks/kb_core.py 的 INDEX_FILENAME、_INDEX_ENTRY_RE、
count_index_entries，避免校验器与契约方对「什么是索引行」产生分歧。

退出码：0 = 通过；1 = 有 ERROR；2 = 用法/环境错误。
用法：
    python3 hooks/kb_validate.py [--kb PATH]
默认 kb 路径取 AGENT_KB_PATH 环境变量，否则 ~/.agents/kb。
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kb_core import (  # noqa: E402  （同目录 import）
    INDEX_FILENAME,
    _INDEX_ENTRY_RE,
    count_index_entries,
    resolve_kb_path,
)

CONTENT_DIRS = ("pitfalls", "tools", "workflow")
TYPE_TO_DIR = {"pitfall": "pitfalls", "tool": "tools", "workflow": "workflow"}
DIR_TO_TYPE = {v: k for k, v in TYPE_TO_DIR.items()}
REQUIRED_FIELDS = ("name", "description", "type", "source", "date", "verified", "topic")

# P3-1 受控领域词表（正交于 type；type 只回答「怎么用」，topic 回答「属于哪个领域」）
TOPIC_VOCAB = (
    "api-gateway", "agent-orchestration", "browser", "ci", "cnb", "container",
    "database", "delivery", "git", "llm", "mcp", "methodology", "office",
    "powershell", "python", "security", "tauri", "windows", "zcode",
)

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_PATH_IN_LINE_RE = re.compile(r"\(([^)]+)\)")

# --- P1-2 作用域标记机制 -------------------------------------------------
# 约定：结论若只对某网关/模型/平台成立，description 必须写 【作用域=<网关/模型/平台>】。
# 保守强制：仅当 description 出现**强签名**（产品版本 rc.N / 带前缀的模型名）时才要求标记，
# 以免像「source 含任意版本号」那样误伤通用规律（本库多数条目本就是通用规律）。
_SCOPE_MARK_RE = re.compile(r"作用域")
_SCOPE_TAG_RE = re.compile(r"【作用域=([^】]*)】")
_STRONG_SIG_RE = re.compile(
    r"\brc[.\-]?\d+\b"
    r"|\b(?:qwen\d[\w.\-]*|gpt-\d[\w.\-]*|claude-[\w.\-]+|gemini-[\w.\-]+"
    r"|deepseek-[\w.\-]+|stepfun-[\w.\-]+|doubao-[\w.\-]+|glm-\d[\w.\-]*)",
    re.I,
)
_SCOPE_NAME_RE = re.compile(
    r"New API|AstrBot|ZCode|Qoder|DSH|StepFun|qwen|gpt|claude|Tauri|PowerShell"
    r"|Windows|Ubuntu|webkit|electron|uvx|mcp|CNB|GitHub|docker|sqlite|gtk|NSIS"
    r"|pptx|PowerPoint|openclaw|workbuddy|kimi",
    re.I,
)


def parse_frontmatter(text):
    """返回 (frontmatter dict, error)。仅解析顶层 key（不缩进）。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "缺少开头 --- frontmatter 分隔线"
    fm = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("\"'")
    if not closed:
        return None, "frontmatter 未闭合（缺结尾 ---）"
    return fm, None


def collect_entries(kb):
    """返回 {相对路径: text}。"""
    entries = {}
    for d in CONTENT_DIRS:
        for f in sorted((kb / d).glob("*.md")):
            entries[str(f.relative_to(kb))] = f.read_text(encoding="utf-8")
    return entries


def index_entry_paths(kb):
    """按 kb_core 同款口径提取索引行路径（跳过代码块）。"""
    index = kb / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return None
    paths = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _INDEX_ENTRY_RE.match(line):
            m = _PATH_IN_LINE_RE.search(line)
            if m:
                paths.append(m.group(1).strip())
    return paths


def validate(kb_path=None):
    """返回问题列表；空列表 = 通过。"""
    kb = resolve_kb_path(kb_path)
    problems = []

    def err(msg):
        problems.append(msg)

    if not kb.is_dir():
        return [f"库目录不存在：{kb}"]

    entries = collect_entries(kb)

    # 收集 slug 与 name，供链接解析
    slugs = {Path(p).stem for p in entries}
    names = set()
    fm_by_path = {}
    for p, text in entries.items():
        fm, ferr = parse_frontmatter(text)
        fm_by_path[p] = fm
        if fm and fm.get("name"):
            names.add(fm["name"])

    # 1) schema 必填字段 + 2) type 值与目录一致
    for p, text in entries.items():
        fm, ferr = parse_frontmatter(text)
        if fm is None:
            err(f"[schema] {p}: {ferr}")
            continue
        missing = [k for k in REQUIRED_FIELDS if not fm.get(k)]
        if missing:
            err(f"[schema] {p}: 缺必填字段 {', '.join(missing)}")
        t = fm.get("type", "").strip()
        if t and t not in TYPE_TO_DIR:
            err(f"[type] {p}: type='{t}' 不在 {sorted(TYPE_TO_DIR)}（是否写成复数或串了 memory 体系？）")
        else:
            want_dir = TYPE_TO_DIR.get(t)
            actual_dir = p.split("/", 1)[0]
            if want_dir and actual_dir in CONTENT_DIRS and actual_dir != want_dir:
                err(f"[type] {p}: type='{t}' 应在 {want_dir}/ 下，实际在 {actual_dir}/")

    # 2b) topic 受控词表（P3-1）
    for p, text in entries.items():
        fm = fm_by_path.get(p) or {}
        raw = fm.get("topic", "")
        vals = [x.strip() for x in raw.split(",") if x.strip()]
        bad = [x for x in vals if x not in TOPIC_VOCAB]
        if bad:
            err(f"[topic] {p}: 领域值不在受控词表 {bad}（合法值：{', '.join(TOPIC_VOCAB)}）")

    # 3) 双链死链
    for p, text in entries.items():
        for m in _LINK_RE.finditer(text):
            target = m.group(1).strip()
            if target not in slugs and target not in names:
                err(f"[link] {p}: [[{target}]] 指向不存在的条目")

    # 3b) 作用域标记（P1-2）：单来源/版本绑定结论须在 description 点名边界
    for p, text in entries.items():
        fm = fm_by_path.get(p) or {}
        desc = fm.get("description", "")
        if "【作用域" in desc:
            m = _SCOPE_TAG_RE.search(desc)
            if not m or not m.group(1).strip():
                err(f"[scope] {p}: description 的 【作用域=…】 标记不完整，须为【作用域=网关/模型/平台】")
        elif _STRONG_SIG_RE.search(desc) and not _SCOPE_MARK_RE.search(desc) \
                and not _SCOPE_NAME_RE.search(desc):
            err(f"[scope] {p}: description 引用了具体版本/模型但未点名作用域"
                f"（P1-2：应加 【作用域=…】 或点名网关/模型/平台）")

    # 4) 索引行数 == 磁盘条目数
    idx_count = count_index_entries(kb)
    if idx_count != len(entries):
        err(f"[index] 索引行数 {idx_count} ≠ 磁盘条目数 {len(entries)}"
            f"（新增/删除条目后是否忘了更新 {INDEX_FILENAME}？）")

    # 5) 索引路径集合 == 磁盘路径集合（双向）
    idx_paths = index_entry_paths(kb)
    if idx_paths is None:
        err(f"[index] 无法读取 {INDEX_FILENAME}")
    else:
        idx_set = set(idx_paths)
        disk_set = set(entries)
        for p in sorted(disk_set - idx_set):
            err(f"[index] 磁盘有条目但索引缺行：{p}")
        for p in sorted(idx_set - disk_set):
            err(f"[index] 索引有行但磁盘无对应文件（死链/已删）：{p}")

    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 库校验器（schema/type/双链/索引一致性）")
    ap.add_argument("--kb", default=None, help="库路径，默认 $AGENT_KB_PATH 或 ~/.agents/kb")
    args = ap.parse_args(argv)

    kb = resolve_kb_path(args.kb)
    problems = validate(args.kb)
    if problems:
        print(f"[FAIL] kb 校验未通过（{len(problems)} 项）—— 库：{kb}")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"[PASS] kb 校验通过 —— 库：{kb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
