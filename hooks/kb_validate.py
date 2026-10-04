#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb 库校验器：在写入当下/收尾时拦住坏数据，不依赖事后人工体检。

检查项（对应任务书 P0-3 验收）：
  1) 条目 frontmatter 必填字段齐全：name / description / type / source / date / verified / topic
  2) type ∈ {tool, workflow, pitfall}，且与所在目录一致（tools/ workflow/ pitfalls/）
  3) [[双链]] 指向存在的条目（按文件名 slug 或 frontmatter.name 解析）
  4) 索引行数 == 磁盘 .md 条目数
  5) 索引路径集合 == 磁盘条目路径集合（新增/删除条目后漏更新索引，双向）
  6) 沉淀触发词副本一致（kb_core.py 为唯一真相源，核对 config.json matcher、钩子、
     以及全机 5 处部署副本是否仍与真源一致——断链或内容漂移都会报）

设计：与读库逻辑同源 —— 复用 hooks/kb_core.py 的 INDEX_FILENAME、_INDEX_ENTRY_RE、
count_index_entries，避免校验器与契约方对「什么是索引行」产生分歧。

退出码：0 = 通过；1 = 有 ERROR；2 = 用法/环境错误。
用法：
    python3 kb_validate.py [--kb PATH]          # 全量校验（1-6 项）
    python3 kb_validate.py --check-triggers     # 只校验触发词副本是否与唯一真相源一致
默认 kb 路径取 AGENT_KB_PATH 环境变量，否则 ~/.agents/kb。
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kb_core import (  # noqa: E402  （同目录 import）
    INDEX_FILENAME,
    _INDEX_ENTRY_RE,
    _fence_mark,
    count_index_entries,
    index_entry_lines,
    resolve_kb_path,
)

CONTENT_DIRS = ("pitfalls", "tools", "workflow")
TYPE_TO_DIR = {"pitfall": "pitfalls", "tool": "tools", "workflow": "workflow"}
DIR_TO_TYPE = {v: k for k, v in TYPE_TO_DIR.items()}
REQUIRED_FIELDS = ("name", "description", "type", "source", "date", "verified", "topic")

# P3-1 受控领域词表（正交于 type；type 只回答「怎么用」，topic 回答「属于哪个领域」）
TOPIC_VOCAB = (
    "api-gateway", "agent-orchestration", "browser", "ci", "cnb", "container",
    "database", "sqlite", "delivery", "git", "llm", "mcp", "methodology", "office",
    "powershell", "preference", "python", "security", "tauri", "windows", "zcode",
)

_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_PATH_IN_LINE_RE = re.compile(r"\(([^)]+)\)")

# --- P1-2 作用域标记机制 -------------------------------------------------
# 约定：结论若只对某网关/模型/平台成立，description 要么写 【作用域=<…>】，
#       要么**在描述里直接点名那个平台**——后者同样满足要求，不必加标记。
# 保守强制：仅当 description 出现**强签名**（产品版本 rc.N / 带前缀的模型名）
#       且**没有点名平台**时才要求标记，以免误伤通用规律。
#
# ⚠️ 触发数天然很低，这是**正确行为**，不是"检查空转"（2026-10-02 的一次误判）：
#    本库收录标准就是"跨项目可复用"，绝大多数条目本就是通用规律（git / docker /
#    bash / YAML 之类），压根不该有作用域标记；而真正带厂商指纹的条目
#    （New API 14018、CNB 7200000、Cloudflare 1010）都已在描述里点名了平台。
#    ⇒ 判定合规与否请用本检查，**不要用"【作用域】标记覆盖率"当指标**，
#      那个口径会把通用规律全部误判为不合规。
_SCOPE_MARK_RE = re.compile(r"作用域")
_SCOPE_TAG_RE = re.compile(r"【作用域=([^】]*)】")
_STRONG_SIG_RE = re.compile(
    r"\brc[.\-]?\d+\b"
    r"|\b(?:qwen\d[\w.\-]*|gpt-\d[\w.\-]*|claude-[\w.\-]+|gemini-[\w.\-]+"
    r"|deepseek-[\w.\-]+|stepfun-[\w.\-]+|doubao-[\w.\-]+|glm-\d[\w.\-]*)",
    re.I,
)
# 点名平台即豁免——这份名单越全，误报越少。2026-10-02 补了此前漏掉的
# Cloudflare / 阿里 / 字节 / segno 等（漏掉会导致「已点名却仍被要求加标记」的误报）。
_SCOPE_NAME_RE = re.compile(
    r"New API|AstrBot|ZCode|Qoder|DSH|StepFun|qwen|gpt|claude|Tauri|PowerShell"
    r"|Windows|Ubuntu|webkit|electron|uvx|mcp|CNB|GitHub|docker|sqlite|gtk|NSIS"
    r"|pptx|PowerPoint|openclaw|workbuddy|kimi"
    r"|Cloudflare|阿里|字节|火山|腾讯|百度|segno|qrcode|Pillow|ffmpeg|git\b",
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


def disk_key(rel_path):
    """把磁盘相对路径归一成以 `/` 分隔的字符串。

    关键：Windows 上 `Path.relative_to()` 产出 `pitfalls\\x.md`，而 INDEX.md 里写的是
    `pitfalls/x.md`；若直接 `str()` 二者永远不等（全库误报）。`PurePath.as_posix()`
    把两种平台都归一到 `/`。可对 PurePosixPath / PureWindowsPath 直接测试，不依赖 Windows 环境。
    """
    return rel_path.as_posix()


def index_path_key(raw):
    """索引里的路径归一（防手抖写成反斜杠）。"""
    return str(raw).replace("\\", "/")


def collect_entries(kb):
    """返回 {相对路径(/ 分隔): text}。"""
    entries = {}
    for d in CONTENT_DIRS:
        for f in sorted((kb / d).glob("*.md")):
            entries[disk_key(f.relative_to(kb))] = f.read_text(encoding="utf-8")
    return entries


def index_entry_paths(kb):
    """按 kb_core 同款口径提取索引行路径（围栏处理与计数共用同一实现）。

    顺带检测路径含空格的坏链接形状：regex 能 MATCH、集合比对也能一致通过，
    但 markdown 渲染必断链——这种「全绿但链接死了」的形状在这里报出来。
    """
    index = kb / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return None
    paths = []
    for line in index_entry_lines(text):
        m = _PATH_IN_LINE_RE.search(line)
        if m:
            paths.append(m.group(1).strip())
    return paths


def index_fence_open(kb):
    """INDEX.md 结束时是否仍处于未闭合的代码围栏内。

    未闭合围栏会把其后所有条目行静默吞掉（count 少数 → 检索不到 →
    SessionStart 可能显示「尚无条目」），必须显式报出来。
    """
    index = kb / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return False
    fence = None
    for line in text.splitlines():
        mark = _fence_mark(line.strip())
        if fence is None:
            if mark:
                fence = mark
        elif mark == fence:
            fence = None
    return fence is not None


def index_paths_with_spaces(kb):
    """INDEX 条目行里「(路径 内有空格)」的坏链接形状（regex 认、渲染必断）。"""
    index = kb / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return []
    bad = []
    for line in index_entry_lines(text):
        m = _PATH_IN_LINE_RE.search(line)
        if m and re.search(r"\s", m.group(1)):
            bad.append(line.strip()[:120])
    return bad


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
                f"（P1-1：应加 【作用域=…】 或点名网关/模型/平台）")

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
        idx_set = {index_path_key(p) for p in idx_paths}
        disk_set = set(entries)  # collect_entries 已用 disk_key 归一为 / 形式
        for p in sorted(disk_set - idx_set):
            err(f"[index] 磁盘有条目但索引缺行：{p}")
        for p in sorted(idx_set - disk_set):
            err(f"[index] 索引有行但磁盘无对应文件（死链/已删）：{p}")

    # 5b) 围栏与链接形状：regex 全绿但实际检索不到/打不开的形状
    if index_fence_open(kb):
        err(f"[index] {INDEX_FILENAME} 存在未闭合的代码围栏——其后所有条目行会被静默跳过（检索不到），请补闭合围栏")
    for bad_line in index_paths_with_spaces(kb):
        err(f"[index] 条目行路径含空格（markdown 渲染必断链）：{bad_line}")

    return problems


# --- 触发词副本一致性 ---------------------------------------------------
# 沉淀触发词如今只有**一处源码**：kb_core.py 的 TRIGGER_PATTERN。
# 另外两处是它的下游消费方：
#   ① kb_hooks.py —— import kb_core，**不存副本**（导入失败退化成一句极短提示，不退回旧文案）
#   ② config.json 的 hooks.events.UserPromptSubmit[].matcher —— ZCode 侧过滤，平台要求写死字符串
# 本检查核对 ①②③ 是否仍与源一致；任一处"文件在但解析不出"也算 ERROR——
# 那正是变量改名/写法漂移导致钩子静默失灵的情形（2026-10-04 修正，早先版本误当"非 ZCode 环境"跳过）。

_HOOKS_REL = Path(__file__).resolve().parent / "kb_hooks.py"
_ZCODE_CONFIG = Path.home() / ".zcode" / "cli" / "config.json"

# ③ 的比对对象：全机 kb_core.py 已知部署副本（2026-10-04 统一为硬链接，同 inode；
# 同日 Kimi Code 卸载，其副本随 ~/.kimi-code 一并移除，不再列）。
# git checkout / reset 会重写文件从而断链，静默回到多版本漂移 —— 本检查按内容兜底。
_KB_CORE_COPIES = (
    Path.home() / ".codebuddy" / "hooks" / "kb_core.py",
    Path.home() / ".qoder" / "hooks" / "kb_core.py",
    Path.home() / ".trae-cn" / "hooks" / "agent-kb" / "kb_core.py",
    Path.home() / "Downloads" / "Project" / "trae" / "trae_huanjing"
    / "agent-kb" / "hooks" / "kb_core.py",
)
_TRIGGER_RE = re.compile(
    r'(?:BUILTIN_TRIGGER|TRIGGER_PATTERN)\s*=\s*.{0,60}?re\.compile\(\s*r?["\']([^"\']+)["\']',
    re.S,
)


def _norm_trigger(raw):
    """归一：去空白 + 按 | 切分 + 排序，让 'a|b' 与 'b | a' 视为一致。"""
    return sorted(x.strip() for x in raw.split("|") if x.strip())


def _read_trigger_from_source(path):
    """三态返回：(state, value)。state ∈ {missing, unreadable, nomatch, ok}。

    ⚠️ 刻意区分 nomatch 与 missing（2026-10-04 修正）：
       早先版本两者都返回 None 一律跳过，把「文件在、但正则没匹配上」这种
       **正是要抓的格式漂移**当成了「非 ZCode 环境，跳过」。
       nomatch 必须报错，否则改坏触发词反而显示 PASS。
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return "missing", None
    except Exception:
        return "unreadable", None
    m = _TRIGGER_RE.search(text)
    return ("ok", m.group(1)) if m else ("nomatch", None)


def _read_trigger_from_config(path=None):
    """同上三态。path 默认取全局 _ZCODE_CONFIG；显式传路径供测试注入。"""
    cfg_path = _ZCODE_CONFIG if path is None else Path(path)
    try:
        import json
        raw = cfg_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "missing", None
    except Exception:
        return "unreadable", None
    try:
        cfg = json.loads(raw)
        grps = cfg.get("hooks", {}).get("events", {}).get("UserPromptSubmit", [])
    except Exception:
        return "unreadable", None
    for grp in grps:
        if isinstance(grp, dict) and grp.get("matcher"):
            return "ok", grp["matcher"]
    return "nomatch", None


def _read_hooks_enabled(path=None):
    """读 ZCode 配置的 hooks 开关状态：(state, detail)。

    state ∈ {missing, unreadable, master-off, entry-off, ok}：
    - master-off：hooks.enabled=false（全部钩子死，SessionStart 也无）
    - entry-off：UserPromptSubmit 的某个 hook 条目 enabled=false（只死沉淀注入）
    实测缺口（2026-10-04）：matcher 完好而开关关闭时旧版直接全绿——开关是
    config.json:21 与 :74 都真实在用的字段，不查等于漏掉一整类静默死亡。
    """
    cfg_path = _ZCODE_CONFIG if path is None else Path(path)
    try:
        import json
        raw = cfg_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "missing", None
    except Exception:
        return "unreadable", None
    try:
        cfg = json.loads(raw)
        hooks_root = cfg.get("hooks", {})
        if hooks_root.get("enabled") is False:
            return "master-off", "hooks.enabled=false（SessionStart 与沉淀注入全部不生效）"
        for grp in hooks_root.get("events", {}).get("UserPromptSubmit", []):
            if not isinstance(grp, dict):
                continue
            for h in grp.get("hooks", []):
                if isinstance(h, dict) and h.get("enabled") is False:
                    return "entry-off", "UserPromptSubmit 里存在 enabled=false 的 hook 条目（沉淀注入不生效）"
    except Exception:
        return "unreadable", None
    return "ok", None


def check_triggers(hooks_rel=None, zcode_config=None, copies=None, source=None):
    """返回 (problems, notes)：唯一真相源是 kb_core.TRIGGER_PATTERN；核对 config.json matcher 与钩子是否残留副本。

    参数默认值即真实部署路径（模块常量）；显式传入用于测试注入。
    """
    problems, notes = [], []
    src = Path(__file__).resolve().parent / "kb_core.py" if source is None else Path(source)
    src_state, src_val = _read_trigger_from_source(src)
    if src_state != "ok":
        # 2026-10-04 升级：真源解析不出触发词曾是「跳过比对仍 PASS」的盲区——
        # 而此时 hooks 调 get_trigger_pattern 也在同一文件上死掉，两道防线同时失效。
        problems.append(
            f"[trigger] 唯一真相源 {src} 解析不出触发词（{src_state}）——"
            "钩子与校验器同时失效，请立即修复 kb_core.py 的 TRIGGER_PATTERN 定义")
        return problems, notes

    base = _norm_trigger(src_val)

    # ① kb_hooks.py：它 import kb_core，不存副本 —— "没有正则定义"是**正确状态**
    hooks_path = _HOOKS_REL if hooks_rel is None else Path(hooks_rel)
    hook_state, hook = _read_trigger_from_source(hooks_path)

    # ② config.json：平台要求写死字符串，必须与源一致；解析不出是真故障
    cfg_path = _ZCODE_CONFIG if zcode_config is None else Path(zcode_config)
    cfg_state, cfg = _read_trigger_from_config(zcode_config)
    if cfg_state == "missing":
        notes.append(f"未找到 {cfg_path}（非 ZCode 环境属正常），跳过配置比对")
        if hook_state == "missing":
            notes.append(f"kb_hooks.py 不在 {hooks_path}（该适配器未部署？），跳过比对")
        elif hook_state == "unreadable":
            problems.append(f"[trigger] kb_hooks.py 存在但读不出（{hooks_path}），请检查权限/编码")
        elif hook_state == "nomatch":
            notes.append("kb_hooks.py 未存触发词副本（预期：它 import kb_core）——正确")
        elif _norm_trigger(hook) != base:
            problems.append(
                f"[trigger] kb_hooks.py 里存了一份触发词副本且与 kb_core 不一致"
                f"（源：{'|'.join(base)}｜该处：{'|'.join(_norm_trigger(hook))}）"
                "——⛔ 副本就是漂移源，删掉它改用 kb_core.should_trigger_user_prompt()")
    elif cfg_state == "unreadable":
        problems.append(f"[trigger] config.json 存在但读不出（{cfg_path}）")
    else:
        # config.json 在且结构可读 = ZCode 部署环境。ok = 有 matcher；nomatch = 无 matcher
        # （2026-10-04 用户删掉 matcher 后的合法形态：平台不过滤、每条消息都调钩子，
        #   触发词由 kb_core 正则全权决定——词表只剩一处真相源，双副本同步死结消失；
        #   真源解析失败已单独报 FAIL，此处无需再判。）
        if cfg_state == "ok":
            if _norm_trigger(cfg) != base:
                problems.append(
                    f"[trigger] config.json:UserPromptSubmit.matcher 与 kb_core.TRIGGER_PATTERN 不一致"
                    f"（源：{'|'.join(base)}｜该处：{'|'.join(_norm_trigger(cfg))}）"
                    "——改 kb_core.py 的 TRIGGER_PATTERN 后必须同步这里")
        else:
            notes.append("config.json 未设 matcher——平台不过滤，触发词由 kb_core 正则全权决定（单真相源合法形态）")
        if hook_state == "missing":
            problems.append(
                f"[trigger] ZCode 环境但 kb_hooks.py 不在 {hooks_path}"
                "——钩子入口丢失，开工提醒与沉淀注入全部失效，请重新部署入口脚本")
        elif hook_state == "unreadable":
            problems.append(f"[trigger] kb_hooks.py 存在但读不出（{hooks_path}），请检查权限/编码")
        elif hook_state == "nomatch":
            notes.append("kb_hooks.py 未存触发词副本（预期：它 import kb_core）——正确")
        elif cfg_state == "ok" and _norm_trigger(hook) != base:
            problems.append(
                f"[trigger] kb_hooks.py 里存了一份触发词副本且与 kb_core 不一致"
                f"（源：{'|'.join(base)}｜该处：{'|'.join(_norm_trigger(hook))}）"
                "——⛔ 副本就是漂移源，删掉它改用 kb_core.should_trigger_user_prompt()")
        # ②b) hooks 开关：matcher 在不在都查——enabled 关闭时钩子全死（实测盲区）
        en_state, en_detail = _read_hooks_enabled(zcode_config)
        if en_state == "master-off":
            problems.append(f"[trigger] config.json hooks 总开关已关闭：{en_detail}（{cfg_path}）")
        elif en_state == "entry-off":
            problems.append(f"[trigger] config.json 钩子条目已停用：{en_detail}（{cfg_path}）")
        elif en_state == "unreadable":
            problems.append(f"[trigger] config.json 存在但读不出（{cfg_path}）")

    # ③ 全机部署副本：统一为硬链接后若被 git 等重写断链，内容漂移必须报出来
    try:
        canon_bytes = src.read_bytes()
    except Exception:
        canon_bytes = None
    if canon_bytes is None:
        notes.append(f"真源 {src} 读不出字节，跳过副本比对")
        return problems, notes
    for p in (_KB_CORE_COPIES if copies is None else copies):
        p = Path(p)
        if not p.is_file():
            notes.append(f"副本不存在（该工具未部署？跳过）: {p}")
            continue
        if os.path.samefile(p, src):
            continue  # 同 inode = 硬链 intact，最理想状态，不刷屏
        if p.read_bytes() == canon_bytes:
            notes.append(f"副本内容一致但硬链已断（建议重建链接防将来漂移）: {p}")
        else:
            problems.append(
                f"[trigger] kb_core 副本与库根真源内容不一致: {p}"
                "——⛔ 漂移源。删掉该副本后重建硬链指向库根"
                "（Windows: cmd /c mklink /H 副本 真源）")
    return problems, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 库校验器（schema/type/双链/索引一致性/触发词副本）")
    ap.add_argument("--kb", default=None, help="库路径，默认 $AGENT_KB_PATH 或 ~/.agents/kb")
    ap.add_argument("--check-triggers", action="store_true",
                    help="只校验沉淀触发词副本是否与唯一真相源一致")
    args = ap.parse_args(argv)

    kb = resolve_kb_path(args.kb)

    if args.check_triggers:
        t_problems, t_notes = check_triggers()
        for n in t_notes:
            print(f"[info] {n}")
        if t_problems:
            print(f"[FAIL] 触发词一致性未通过（{len(t_problems)} 项）")
            for p in t_problems:
                print("  - " + p)
            return 1
        print("[PASS] 触发词副本与唯一真相源一致")
        return 0

    problems = validate(args.kb)
    t_problems, t_notes = check_triggers()
    problems += t_problems
    if problems:
        print(f"[FAIL] kb 校验未通过（{len(problems)} 项）—— 库：{kb}")
        for p in problems:
            print("  - " + p)
        return 1
    for n in t_notes:
        print(f"[info] {n}")
    print(f"[PASS] kb 校验通过 —— 库：{kb}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
