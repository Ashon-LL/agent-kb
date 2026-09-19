# -*- coding: utf-8 -*-
"""Codex CLI hook 适配器。

## 平台
Codex CLI（OpenAI）—— 配置位置 `~/.codex/hooks.json`。

## Hook 文档
- 官方 hooks 文档：https://platform.openai.com/docs/codex/cli/hooks
- 配置样例：`templates/codex-hooks.json`

## 与 Trae/ZCode/Claude 的关键差异（本文件存在的理由）

Codex 的 stdin / stdout 契约**和其他平台不同**，不能照搬模板：

1. **事件名字段是 `event`，不是 `hook_event_name`**。
   Codex 回调 JSON 形如：
       {"event": "SessionStart", "session_id": "...", "cwd": "...", "prompt": "..."}
   所以这里读 `event`（兜底也认 `hook_event_name`，防版本漂移）。

2. **事件名取值**：`SessionStart` / `UserPromptSubmit`（与 Claude 家族一致）。

3. **stdout 格式是 `systemMessage` 顶层字段**（纯 JSON），不是
   `hookSpecificOutput.additionalContext`：
       {"systemMessage": "<注入到 system message 的文本>"}
   `decision` 字段可用于控制流（本适配器**不使用**，坚持"增强而非阻塞"）。

## stdin 字段映射表

| 本适配器读取 | Codex 原始字段 | 说明 |
|---|---|---|
| 事件名   | `event`（兜底 `hook_event_name`） | 本平台用 `event` |
| 用户输入 | `prompt`                          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`                      | 本适配器不使用，仅透传语义 |
| 工作目录 | `cwd`                             | 本适配器不使用 |

## stdout 格式说明

```json
{"systemMessage": "【kb 开工钩子】..."}
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
    claude_style_payload,  # noqa: F401  (保留导出，便于对照)
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


def emit(msg: str) -> None:
    """Codex 消费 systemMessage 顶层字段。"""
    emit_json({"systemMessage": msg})


def main() -> int:
    data = read_stdin_json()

    # Codex 用 `event`；兜底 `hook_event_name` 防平台版本漂移
    raw_event = data.get("event") or data.get("hook_event_name")
    event = normalize_event(raw_event)
    prompt = extract_prompt(data)
    kb_path = resolve_kb_path()
    debug_log(event or str(raw_event), prompt, kb_path)

    if event == EVENT_SESSION_START:
        emit(session_start_reminder(str(kb_path)))
    elif event == EVENT_USER_PROMPT:
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(user_prompt_reminder())
    return 0


if __name__ == "__main__":
    sys.exit(run_adapter(main))
