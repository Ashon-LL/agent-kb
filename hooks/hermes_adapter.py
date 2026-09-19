# -*- coding: utf-8 -*-
"""Hermes hook 适配器。

## 平台
Hermes（Agent / IDE）。

## 核实状态：⚠️ 未核实（未找到公开官方 hook 文档）
- 检索未找到 Hermes Agent/IDE 的官方 hook 格式文档，因此本文件的
  **事件名 / stdin 字段 / stdout 格式均按本项目通用约定实现，属占位**。
- 不编造官方链接。若日后找到官方文档，只需改本文件 `emit()` 一处。

## 与已验证平台的差异（当前假设）
- 配置位置：**假设**为 `~/.hermes/hooks.json`（顶层 `hooks` 键），
  与 Trae/ZCode 风格一致。`templates/hermes-hooks.json` 是占位结构。
- 事件名：假设 `SessionStart` / `UserPromptSubmit`。
- stdin：假设 `hook_event_name` + `prompt`。
- stdout：假设 `hookSpecificOutput.additionalContext`。

## stdin 字段映射表（假设，待核实）

| 本适配器读取 | 假设的 Hermes 字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | 兼容 `event` |
| 用户输入 | `prompt`          | 兼容 `message` / `text` |
| 会话 id  | `session_id`      | 本适配器不使用 |

## stdout 格式说明（假设，待核实）

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
```

## 环境变量

- `AGENT_KB_PATH`  —— 覆盖默认 `~/.agents/kb`，优先级高于 `sys.argv[1]`
- `AGENT_KB_DEBUG` —— 置 `1` 时向 stderr 打印 `[agent-kb debug] ...`

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
    """Hermes hook 输出格式（未核实，占位）：hookSpecificOutput.additionalContext。"""
    emit_json(claude_style_payload(event_name, context))


def main() -> int:
    data = read_stdin_json()

    raw_event = data.get("hook_event_name") or data.get("event")
    event = normalize_event(raw_event)
    prompt = extract_prompt(data)
    kb_path = resolve_kb_path()
    debug_log(event or str(raw_event), prompt, kb_path)

    if event == EVENT_SESSION_START:
        emit(EVENT_SESSION_START, session_start_reminder(str(kb_path)))
    elif event == EVENT_USER_PROMPT:
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(EVENT_USER_PROMPT, user_prompt_reminder())
    return 0


if __name__ == "__main__":
    sys.exit(run_adapter(main))
