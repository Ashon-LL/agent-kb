# -*- coding: utf-8 -*-
"""Qoder（IDE / JetBrains 插件 / CLI）hook 适配器。

## 平台
Qoder（阿里，IDE + JetBrains 插件 + CLI 三形态）。

## Hook 文档
- 官方文档：https://docs.qoder.com/extensions/hooks
- 配置位置：`~/.qoder/settings.json` 的顶层 `hooks` 键
  （IDE 与 CLI **共用**同一份 settings.json，装一次三端生效）。

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

1. **配置载体是 settings.json 的 `hooks` 子树**，不是独立 hooks.json；
   安装器必须**合并**，不能整文件覆盖（settings.json 里还有别的用户配置）。

2. **事件名 `SessionStart` / `UserPromptSubmit`，两者都不支持 matcher** ——
   事件名即唯一键，所以"触发词过滤"必须由**适配器内部正则**补位
   （见 kb_core.should_trigger_user_prompt），这是本项目的核心防御。

3. **stdin 字段名是 `hook_event_name`**（与 Claude/CodeBuddy 同族）。

4. **stdout 走 `hookSpecificOutput.additionalContext`**，`hookEventName` 需回填。

5. **退出码 2 = 阻塞**，且 **stderr 内容会展示给用户**。本项目恒 exit 0，
   绝不用退出码干预会话。

## stdin 字段映射表

| 本适配器读取 | Qoder 原始字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | SessionStart / UserPromptSubmit |
| 用户输入 | `prompt`          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`      | 本适配器不使用 |
| 工作目录 | `cwd`             | 本适配器不使用 |

## stdout 格式说明

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "【kb 沉淀钩子】..."
  }
}
```

## 环境变量

- `AGENT_KB_PATH`  —— 覆盖默认 `~/.agents/kb`，优先级高于 `sys.argv[1]`
- `AGENT_KB_DEBUG` —— 置 `1` 时向 stderr 打印 `[agent-kb debug] ...`

## 退出码

0 成功；2 阻塞（stderr 展示给用户）。本项目永不阻塞，任何异常静默 exit 0。
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
    """Qoder hook 输出格式：hookSpecificOutput.additionalContext。"""
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
