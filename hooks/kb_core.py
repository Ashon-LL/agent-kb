# -*- coding: utf-8 -*-
"""agent-kb Hook 核心逻辑（平台无关）。

被各平台适配器（ZCode hooks.json 等）import 后调用。

⚠️ **本文件是消息文本与触发词的唯一真相源**。适配器（kb_hooks.py）只负责
   把这里的返回值塞进平台协议，**不得自己存一份文案或正则副本**——
   2026-10-02 之前 ZCode 就因为入口里存了文案副本而与本文件分叉。
   `kb_validate.py --check-triggers` 会核对适配器与 config.json 是否仍与本文件一致。

设计原则：
- 核心逻辑只做一件事：根据事件类型，把一段提醒文本输出给适配器
- 任何异常静默放行（exit 0 无输出），绝不阻塞 Agent 会话
- 触发词自过滤：UserPromptSubmit 在平台 matcher 不生效时，用正则补位
- 路径在运行时求值（Path.home()），不硬编码 "~" 字符串，非 POSIX 环境同样可用

参考：hook 注入链路拆三段 —— ① 平台回调点（hook_event_name）② 执行载体（command 进程）③ 平台消费的数据结构（stdout JSON 字段）
"""
import os
import re
from pathlib import Path

# 触发词环境变量：分号分隔的正则片段，与内置触发词取并集
TRIGGER_ENV_VAR = "AGENT_KB_TRIGGER"

# 内置触发词：命中其一即注入沉淀规程
TRIGGER_PATTERN = re.compile(
    r"记住|沉淀|晋升|以后别|下次别|全局经验"
)

# 索引文件名
INDEX_FILENAME = "INDEX.md"

# 索引条目行形状：- [标题](相对路径) —— 一句话钩子
_INDEX_ENTRY_RE = re.compile(r"^\s*[-*]\s+\[[^\]]*\]\([^)]+\)")


def default_kb_path() -> Path:
    """运行时求值默认库路径，避免把 "~" 写死成字符串。

    优先读 AGENT_KB_PATH 环境变量，其次 Path.home() / ".agents" / "kb"。
    """
    env = os.environ.get("AGENT_KB_PATH", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".agents" / "kb"


def resolve_kb_path(kb_path=None) -> Path:
    """把调用方传入的 kb_path（str / Path / None）统一成 Path。"""
    if kb_path is None:
        return default_kb_path()
    return Path(str(kb_path)).expanduser()


def count_index_entries(kb_path=None) -> int:
    """统计 {kb_path}/INDEX.md 里的条目行数。

    索引缺失 / 不可读 / 无条目时返回 0 —— 永不抛异常，hook 不阻塞会话。
    只数条目行（`- [标题](路径)`），不数标题、说明、代码块内的示例。
    """
    index = resolve_kb_path(kb_path) / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return 0

    count = 0
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        # 跳过 ``` 代码块，避免把模板里的示例行算成条目
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _INDEX_ENTRY_RE.match(line):
            count += 1
    return count


def get_trigger_pattern() -> re.Pattern:
    """内置触发词 + AGENT_KB_TRIGGER 环境变量（分号分隔的正则片段）取并集。

    环境变量里的片段直接参与正则拼接；非法片段被忽略，不影响内置触发词。
    """
    fragments = []
    env = os.environ.get(TRIGGER_ENV_VAR, "")
    for frag in env.split(";"):
        frag = frag.strip()
        if frag:
            fragments.append(frag)

    if not fragments:
        return TRIGGER_PATTERN

    try:
        return re.compile(TRIGGER_PATTERN.pattern + "|" + "|".join(fragments))
    except re.error:
        # 环境变量里的正则是坏的 —— 退回内置，别把 hook 拖挂
        return TRIGGER_PATTERN


def session_start_reminder(kb_path=None) -> str:
    """SessionStart 时注入的开工提醒。

    真读 {kb_path}/INDEX.md 统计条目数；库不存在时提示尚未初始化。
    """
    resolved = resolve_kb_path(kb_path)
    count = count_index_entries(resolved)
    # 就绪与否由 count 决定，但**不把数字印进注入文本**：那个数字随增删漂移，
    # 且 2026-10-02 之前两份拷贝正是因它不一致才分叉。需要条数随时查
    # count_index_entries()，kb_validate.py 就在用。
    shown = "~/.agents/kb/" if resolved == default_kb_path() else f"{resolved}/"
    if count:
        head = f"全局经验库 {shown} 就绪。"
    else:
        head = f"全局经验库 {shown} 尚无条目（未找到可读的 INDEX.md）。"
    return (
        f"【kb 开工钩子】{head}"
        "非平凡任务动手前先扫 INDEX.md，命中读条目全文再干。"
    )


def user_prompt_reminder() -> str:
    """UserPromptSubmit 命中触发词时注入的沉淀规程。"""
    return (
        "【kb 沉淀钩子】用户本条消息疑似要求沉淀经验。执行："
        "1) 读 ~/.agents/kb/INDEX.md 查重——同族条目优先扩充现有文件而非新建；"
        "2) 按 kb 技能规程落盘（frontmatter: name/description/type/source/date/verified/topic；正文: 经验/Why/How to apply）；"
        "3) 更新 INDEX.md 并核对索引行数=实际文件数；"
        "4) ⛔ 跑校验器 `python ~/.agents/kb/kb_validate.py`，看到 [PASS] 才算完"
        "（报 [FAIL] 按它列的行逐条修，不要绕过、不要改校验器迁就条目）；"
        "5) 回报条目路径与索引行。若用户并非要求沉淀，忽略本提醒正常干活。"
    )


def should_trigger_user_prompt(prompt: "str | None") -> bool:
    """自过滤：当平台 matcher 不生效时，用正则判断是否注入沉淀规程。

    正则 = 内置触发词 ∪ AGENT_KB_TRIGGER 环境变量片段。
    """
    if prompt is None:
        return True  # 拿不到 prompt 就默认注入一次（保险）
    return bool(get_trigger_pattern().search(prompt))
