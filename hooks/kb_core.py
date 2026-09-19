# -*- coding: utf-8 -*-
"""agent-kb Hook 核心逻辑（平台无关）。

被各平台适配器（Trae hooks.json / ZCode hooks.json / Codex .codex/hooks.json）import 后调用。

设计原则：
- 核心逻辑只做一件事：根据事件类型，把一段提醒文本输出到 stdout 或 stderr（适配器决定交给平台哪个通道）
- 任何异常静默放行（exit 0 无输出），绝不阻塞 Agent 会话
- 触发词自过滤：UserPromptSubmit 在 matcher 不生效时，用正则补位

参考：hook 注入链路拆三段 —— ① 平台回调点（hook_event_name）② 执行载体（command 进程）③ 平台消费的数据结构（stdout JSON 字段）
"""
import sys
import re

# 默认库路径，适配器可覆盖
DEFAULT_KB_PATH = "~/.agents/kb"

# 触发词：命中其一即注入沉淀规程
TRIGGER_PATTERN = re.compile(
    r"记住|沉淀|晋升|以后别|下次别|全局经验"
)


def session_start_reminder(kb_path=DEFAULT_KB_PATH) -> str:
    """SessionStart 时注入的开工提醒。"""
    return (
        f"【kb 开工钩子】全局经验库 {kb_path}/ 就绪（条数以 INDEX.md 为准）。"
        "非平凡任务动手前先扫 INDEX.md，命中读条目全文再干。"
    )


def user_prompt_reminder() -> str:
    """UserPromptSubmit 命中触发词时注入的沉淀规程。"""
    return (
        "【kb 沉淀钩子】用户本条消息疑似要求沉淀经验。执行："
        "1) 读 ~/.agents/kb/INDEX.md 查重——同族条目优先扩充现有文件而非新建；"
        "2) 按 kb 技能规程落盘（frontmatter: name/description/type/source/date；正文: 经验/Why/How to apply）；"
        "3) 更新 INDEX.md 并核对索引行数=实际文件数；"
        "4) 回报条目路径与索引行。若用户并非要求沉淀，忽略本提醒正常干活。"
    )


def should_trigger_user_prompt(prompt: str | None) -> bool:
    """自过滤：当平台 matcher 不生效时，用正则判断是否注入沉淀规程。"""
    if prompt is None:
        return True  # 拿不到 prompt 就默认注入一次（保险）
    return bool(TRIGGER_PATTERN.search(prompt))
