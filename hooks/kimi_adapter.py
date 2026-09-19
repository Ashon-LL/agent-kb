# -*- coding: utf-8 -*-
"""Kimi Code CLI hook 适配器（纯文本注入模式）。

## 平台
Kimi Code CLI（Moonshot AI）。

## Hook 文档
- 官方 hooks 文档：
  https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/hooks.md
- 配置位置：`~/.kimi-code/config.toml` 的 `[[hooks]]` 数组。
  **注意是 TOML 不是 JSON** —— 本仓库 `templates/kimi-hooks.json` 只是结构化占位，
  安装器/用户需按下述形式转写进 config.toml：

```toml
[[hooks]]
event   = "SessionStart"
matcher = "startup|resume"
command = "python3 <HOOKS_DIR>/kimi_adapter.py"
timeout = 10
```

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

1. **配置是 TOML**：`[[hooks]]` 数组，每条只有 4 个字段：`event` / `matcher` /
   `command` / `timeout`（1–600 秒，默认 30）。**没有** `type: "command"` 这层嵌套，
   也**没有** hooks.json。README 的"hooks.json"表述对 Kimi 不适用。

2. **stdout 是纯文本，不要 JSON 包装**。Kimi 把 hook 的 **stdout 文本直接追加进
   上下文** —— 这正是我们的注入通道。若输出 Claude 风格 JSON，用户会在上下文里
   看到一串原始 JSON，属于错误格式。

3. **判定主要看退出码**：0 放行 / 2 拦截 / 其他视为脚本错误（按放行处理）。
   本项目恒 exit 0。

## stdin 字段映射表

| 本适配器读取 | Kimi 原始字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | SessionStart / UserPromptSubmit |
| 用户输入 | `prompt`          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`      | 本适配器不使用 |
| 会话标题 | `session_title`   | 本适配器不使用 |
| 客户端类型 | `client_type`   | 本适配器不使用 |
| 工作目录 | `cwd`             | 本适配器不使用 |

## stdout 格式说明

**纯文本**（无 JSON）。为便于在 transcript 里分辨来源，加事件前缀：

    [kb:SessionStart] 【kb 开工钩子】...

## 环境变量

- `AGENT_KB_PATH`  —— 覆盖默认 `~/.agents/kb`，优先级高于 `sys.argv[1]`
- `AGENT_KB_DEBUG` —— 置 `1` 时向 stderr 打印 `[agent-kb debug] ...`
  （debug 走 stderr，不会污染注入上下文）

## 退出码

0 成功（放行）；本项目永不阻塞，任何异常静默 exit 0。
"""
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from adapter_base import (  # noqa: E402
    EVENT_SESSION_START,
    EVENT_USER_PROMPT,
    debug_log,
    emit_text,
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
    """Kimi 输出纯文本；stdout 会被直接追加进上下文（不做 JSON 包装）。"""
    emit_text(f"[kb:{event_name}] {context}\n")


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
