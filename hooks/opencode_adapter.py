# -*- coding: utf-8 -*-
"""OpenCode hook 适配器（插件桥接模式）。

## 平台
OpenCode（sst/opencode CLI，原 opencode-ai/opencode）。

## Hook 文档
- 插件文档：https://opencode.ai/docs/plugins/
- 仓库：https://github.com/sst/opencode
- 配置位置：
  - 全局插件目录 `~/.config/opencode/plugin/`（注意官方目录名是单数 `plugin`）
  - 项目级 `.opencode/plugin/`

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

OpenCode **没有 stdin/stdout JSON hook 协议**。它的扩展点是 **JS/TS 插件**：

```js
export const KbPlugin = async ({ $, client }) => ({
  event: async ({ event }) => { /* 所有事件都走这一个入口 */ },
  "tui.toast.show": async () => {},
})
```

因此：
1. **单一 `event` 入口，事件名带命名空间且为 snake/dot 风格**：
   `session.created`（新会话）/ `tui.prompt.append`（用户提交）等。
   **不存在** `SessionStart` / `UserPromptSubmit` 这两个名字。
2. **回调参数是嵌套对象**：`{ event: { type, properties } }`，
   载荷在 `properties` 里，不在顶层。本适配器同时认嵌套与扁平两种形状。
3. **stdout 无原生消费方**：本适配器定位为**子进程桥** —— 插件用
   `Bun.$` / `child_process` shell 调起本脚本，读 stdout JSON 后由插件自行注入
   （如塞进 `chat.params` 的 system 段，或 `tui.toast.show` 展示）。

## stdin 字段映射表

| 本适配器读取 | OpenCode 原始位置 | 说明 |
|---|---|---|
| 事件名   | `event.type`（嵌套）或顶层 `hook_event_name` | 归一化见下 |
| 用户输入 | `event.properties.prompt.text` / `properties.text` / `prompt` | 逐级兜底 |
| 会话 id  | `event.properties.info.id` / `session_id` | 本适配器不使用 |
| 工作目录 | `properties.cwd` / `cwd` | 本适配器不使用 |

事件名归一化：
- `session.created` / `session.start` / `session_start` → `SessionStart`
- `tui.prompt.append` / `before_prompt_build` / `user_prompt.submit` → `UserPromptSubmit`

## stdout 格式说明

桥接约定，回 `hookSpecificOutput.additionalContext`：

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
```

插件侧从 `additionalContext` 取文本自行注入 prompt / toast。

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
    first_present,
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
    """桥接输出：hookSpecificOutput.additionalContext，由调用方 JS 插件消费。"""
    emit_json(claude_style_payload(event_name, context))


def _flatten(data: dict) -> dict:
    """把 OpenCode 的嵌套事件对象摊平成统一形状。

    OpenCode 回调形如 {"event": {"type": "session.created", "properties": {...}}}；
    插件桥也可能送来扁平 {"hook_event_name": ..., "prompt": ...}。两者都认。
    """
    raw_event = data.get("event")
    if isinstance(raw_event, dict):
        props = raw_event.get("properties")
        props = props if isinstance(props, dict) else {}
        merged = dict(props)
        merged["_event_type"] = raw_event.get("type")
        return merged
    return data


def main() -> int:
    data = _flatten(read_stdin_json())

    # 事件名：嵌套 event.type 优先，兜底扁平字段
    raw_event = first_present(
        data,
        ("_event_type", "hook_event_name", "event", "type", "name"),
    )
    event = normalize_event(raw_event)

    # prompt：OpenCode 藏在 properties.prompt.text / properties.text
    prompt = None
    prompt_obj = data.get("prompt")
    if isinstance(prompt_obj, dict):
        text = prompt_obj.get("text")
        prompt = text if isinstance(text, str) else None
    if prompt is None:
        value = first_present(data, ("text", "content", "message", "prompt"))
        prompt = value if isinstance(value, str) else None

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
