# -*- coding: utf-8 -*-
"""Trae / ZCode 平台 Hook 适配器。

## 平台
Trae / ZCode —— 配置位置 `~/.trae/hooks.json`（Windows）或 `~/.zcode/hooks.json`。

## Hook 文档
- 配置样例：`templates/trae-hooks.json` / `templates/zcode-hooks.json`

## stdin / stdout 契约

Trae / ZCode 与 Claude Code 家族同形：

stdin（回调 JSON）:

    {"hook_event_name": "SessionStart", "session_id": "...", "prompt": "..."}

stdout（消费 JSON，走 `hookSpecificOutput.additionalContext` 注入上下文）:

    {"hookSpecificOutput": {"hookEventName": "...", "additionalContext": "..."}}

不返回 `decision` 字段 —— 保持"增强而非阻塞"语义。

## 字段映射

| 本适配器读取 | 平台字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name`（兼容 `event` 等，经 normalize_event 归一） | SessionStart / UserPromptSubmit |
| 用户输入 | `prompt`（兼容 `user_prompt` / `message` / `content` / `text`） | UserPromptSubmit 才有 |

## 环境变量

- `AGENT_KB_PATH`   —— 覆盖默认 `~/.agents/kb`，优先级高于 `sys.argv[1]`
- `AGENT_KB_DEBUG`  —— 置 `1` 时向 stderr 打印 `[agent-kb debug] ...`
- `AGENT_KB_TRIGGER` —— 分号分隔的额外触发词正则片段

## 退出码

0 成功；本项目永不阻塞，任何异常静默 exit 0。
"""
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from adapter_base import (  # noqa: E402
    EVENT_SESSION_START,
    EVENT_USER_PROMPT,
    claude_style_payload,
    debug_log,
    emit_json,
    extract_prompt,
    normalize_event,
    read_stdin_json,
    resolve_kb_path,
    run_adapter,
)
from kb_core import (  # noqa: E402
    session_start_reminder,
    should_trigger_user_prompt,
    user_prompt_reminder,
)


def emit(event_name: str, context: str) -> None:
    """Trae/ZCode hook 约定的输出格式：stdout 写 JSON，含 hookSpecificOutput 字段。"""
    emit_json(claude_style_payload(event_name, context))


def main() -> int:
    data = read_stdin_json()

    raw_event = data.get("hook_event_name") or data.get("event")
    event = normalize_event(raw_event)
    prompt = extract_prompt(data)
    kb_path = resolve_kb_path()
    debug_log(event or str(raw_event), prompt, kb_path)

    if event == EVENT_SESSION_START:
        emit(event, session_start_reminder(str(kb_path)))
    elif event == EVENT_USER_PROMPT:
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(event, user_prompt_reminder())
    return 0


if __name__ == "__main__":
    sys.exit(run_adapter(main))
