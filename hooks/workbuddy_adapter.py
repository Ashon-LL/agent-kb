# -*- coding: utf-8 -*-
"""WorkBuddy / CodeBuddy hook 适配器。

## 平台
WorkBuddy IDE 与 CodeBuddy CLI（腾讯，共用同一 hooks 实现）。

## Hook 文档
- 官方文档：https://www.codebuddy.ai/docs/cli/hooks
- 配置位置（多 scope 合并，后者覆盖前者）：
  1. 用户级 `~/.codebuddy/settings.json`
  2. 项目级 `<project>/.codebuddy/settings.json`
  3. 本地级 `<project>/.codebuddy/settings.local.json`
  hook 注册在 settings.json 的**顶层 `hooks` 键**下。

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

1. **配置载体是 settings.json 的多 scope 合并**（3 个文件层级），不是单个 hooks.json；
   安装器必须**合并** hooks 子树，不能覆盖整个 settings.json。

2. **事件名与 Claude 家族一致**：`SessionStart`（无 matcher）/ `UserPromptSubmit`
   （无 matcher）。但**stdin 里的字段名是 `hook_event_name`**，
  且**没有** Claude 的 `source`（startup/resume）语义。

3. **stdout 走 `hookSpecificOutput.additionalContext`**，`hookEventName` 需回填。
   若要拦截 prompt，用 `continue: false` + `reason`（本项目**不用**，
   保持"增强而非阻塞"）。

4. **Windows 下 CodeBuddy 强制走 Git Bash 执行 hook 命令** ——
   所以 hooks.json 里的命令要用 POSIX 风格 `python3 <dir>/xxx.py`，
   **不要**用 PowerShell 的 `& '...'` 调用式（Trae/ZCode 才需要那一套）。

## stdin 字段映射表

| 本适配器读取 | CodeBuddy 原始字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | SessionStart / UserPromptSubmit |
| 用户输入 | `prompt`          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`      | 本适配器不使用 |
| 会话文件 | `transcript_path` | 本适配器不使用 |
| 工作目录 | `cwd`             | 本适配器不使用 |

## stdout 格式说明

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "【kb 开工钩子】..."
  }
}
```

## 环境变量

- `AGENT_KB_PATH`  —— 覆盖默认 `~/.agents/kb`，优先级高于 `sys.argv[1]`
- `AGENT_KB_DEBUG` —— 置 `1` 时向 stderr 打印 `[agent-kb debug] ...`

## 退出码

0 成功；2 阻塞。本项目永不阻塞，任何异常静默 exit 0。
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
    """CodeBuddy/WorkBuddy hook 输出：hookSpecificOutput.additionalContext。"""
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
