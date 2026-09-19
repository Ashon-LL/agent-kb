# -*- coding: utf-8 -*-
"""Trae / ZCode 平台 Hook 适配器。

## 平台
Trae（CN 版，ByteDance）与 ZCode —— 两者 hooks 契约**完全一致**，共用一个适配器。

## Hook 文档
- Trae hooks 文档：https://docs.trae.ai/ide/hooks
- 配置位置：`~/.trae-cn/hooks.json`（Trae）/ `~/.zcode/hooks.json`（ZCode），
  注册在**顶层 `hooks` 键**下。本仓库 `templates/trae-hooks.json` /
  `templates/zcode-hooks.json` 可直接落盘。

## 与 Claude/Codex 的关键差异（本文件存在的理由）

1. **命令是 PowerShell 调用式**：hooks.json 里写
   `"& 'PYTHON_EXECUTABLE' 'HOOKS_DIR\\trae_zcode_adapter.py'"`。
   Windows 下 Trae/ZCode 用 PowerShell 起进程，**不是** POSIX 风格
   （对比 WorkBuddy 走 Git Bash，要用 `python3 xxx.py`）。

2. **事件名 `SessionStart` / `UserPromptSubmit`，均无 matcher** ——
   触发词过滤靠适配器内部正则补位。

3. **stdin 字段名是 `hook_event_name`**（与 Claude 家族一致）。

4. **stdout 走 `hookSpecificOutput.additionalContext`**，`hookEventName` 需回填。

5. **hooks.json 顶层带 `"version": 1`** —— 这是 Trae/ZCode 特有字段，
   Claude/CodeBuddy 的 settings.json 格式里没有。

## stdin 字段映射表

| 本适配器读取 | Trae/ZCode 原始字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | SessionStart / UserPromptSubmit |
| 用户输入 | `prompt`          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`      | 本适配器不使用 |
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
        emit(EVENT_SESSION_START, session_start_reminder(str(kb_path)))
    elif event == EVENT_USER_PROMPT:
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(EVENT_USER_PROMPT, user_prompt_reminder())
    return 0


if __name__ == "__main__":
    sys.exit(run_adapter(main))
