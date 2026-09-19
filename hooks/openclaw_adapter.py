# -*- coding: utf-8 -*-
"""OpenClaw hook 适配器（插件桥接模式）。

## 平台
OpenClaw（开源 Agent 运行时）。

## Hook 文档
- Hooks reference：https://github.com/openclaw/openclaw/blob/main/docs/plugins/hooks/reference.md
- 插件入口：`package.json` 的 `openclaw.extensions` 指向 `index.ts`，
  用 `definePluginEntry({ register(api) { api.on("<hook>", handler) } })` 注册。

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

1. **hook 名是 snake_case，不是 `SessionStart` / `UserPromptSubmit`**。
   与本项目最贴合的两个 typed hook：
   - `session_start`        （Observe 型）—— 会话边界，注入开工提醒
   - `before_prompt_build`  （Modify 型）—— 可 **Add prompt context**，注入沉淀规程
   其他常用 hook：`message_received`、`agent_end`、`tool_call`（本项目不用）。

2. **hook 分 Observe / Modify 两型**：
   - Observe（如 `session_start`）**不能改数据**，只能产生副作用（发通知等）。
   - Modify（如 `before_prompt_build`）能**返回结构改数据**，这才是注入通道。
   本适配器两种事件都支持，由插件侧决定怎么消费。

3. **原生 hook 是 TS 回调，不读 stdin**。因此本适配器是**子进程桥**：
   插件 `shell` 调起本脚本 → stdin 喂 `{"hook_event_name","prompt"}` →
   读 stdout `additionalContext` → `before_prompt_build` 返回它注入 prompt 上下文。

## stdin 字段映射表

| 本适配器读取 | OpenClaw 桥接约定 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | 接受原生 `session_start` / `before_prompt_build`，也接受规范名 |
| 用户输入 | `prompt`（兜底 `message` / `text`） | before_prompt_build 时由插件传入 |
| 会话 id  | `session_id` / `sessionId` | 本适配器不使用 |
| 工作目录 | `cwd` | 本适配器不使用 |

事件名归一化：
- `session_start` / `sessionStart` → `SessionStart`
- `before_prompt_build` / `message_received` → `UserPromptSubmit`

## stdout 格式说明

桥接约定，回 `hookSpecificOutput.additionalContext`：

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
```

插件侧：`before_prompt_build` 的 handler 返回 `{ context: additionalContext }`
（OpenClaw 的 "Add prompt context" 返回值），即可注入 prompt。

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
    """桥接输出：hookSpecificOutput.additionalContext，由调用方 TS 插件消费。"""
    emit_json(claude_style_payload(event_name, context))


def main() -> int:
    data = read_stdin_json()

    raw_event = data.get("hook_event_name") or data.get("event") or data.get("hook")
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
