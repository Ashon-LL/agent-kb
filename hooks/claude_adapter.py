# -*- coding: utf-8 -*-
"""Claude Code / Claude Desktop hook 适配器。

## 平台
Anthropic Claude Code（CLI）与 Claude Desktop（复用同一 hooks 实现）。

## Hook 文档
- 官方 Hooks reference：https://docs.claude.com/en/docs/claude-code/hooks
- 配置位置：用户级 `~/.claude/settings.json`，项目级 `.claude/settings.json`。
  hook 注册在 settings.json 的**顶层 `hooks` 键**下 —— 不是独立的 hooks.json 文件。
  本仓库的 `templates/claude-hooks.json` 是需要**合并**进 settings.json 的片段。

## 与 Trae/ZCode 模板的关键差异（本文件存在的理由）

1. **配置载体是 settings.json 的 `hooks` 子树**，不是 `hooks.json`。
   安装器必须做「合并」而非「覆盖」，否则会清掉用户已有的 permissions/statusLine 等设置。

2. **`SessionStart` 事件带 `source` 字段**，取值 `startup` / `resume` / `clear` / `compact`。
   本适配器**不区分** source —— 只要会话开始就给开工提醒（resume/compact 后同样需要
   知道库里有什么）。注意 `SessionStart` 与 `UserPromptSubmit` 都**不支持 matcher**，
   事件名即唯一键。

3. **stdout 走 `hookSpecificOutput.additionalContext`**，且 `hookEventName`
   必须与触发事件**完全一致**（Claude 会校验，不匹配则该输出被忽略）。
   这是与 Codex 用 `systemMessage` 的最大区别。

4. **退出码 2 会阻塞**：SessionStart 下 2 = 拦下会话启动；UserPromptSubmit 下
   2 = 拦下这条 prompt 并把 stderr 回显给用户。本项目**永不阻塞**，恒 exit 0。

## stdin 字段映射表

| 本适配器读取 | Claude 原始字段 | 说明 |
|---|---|---|
| 事件名   | `hook_event_name` | 与 Codex 的 `event` 不同 |
| 用户输入 | `prompt`          | UserPromptSubmit 才有 |
| 会话 id  | `session_id`      | 本适配器不使用 |
| 会话来源 | `source`          | 仅 SessionStart 有（startup/resume/clear/compact） |
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

`hookEventName` 必须回填触发事件名；`additionalContext` 会被追加进模型上下文。
不返回 `decision` / `continue` 字段，保持"增强而非阻塞"。

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
    """Claude hook 输出：hookSpecificOutput.additionalContext 注入上下文。"""
    emit_json(claude_style_payload(event_name, context))


def main() -> int:
    data = read_stdin_json()

    raw_event = data.get("hook_event_name") or data.get("event")
    event = normalize_event(raw_event)
    prompt = extract_prompt(data)
    kb_path = resolve_kb_path()
    debug_log(event or str(raw_event), prompt, kb_path)

    if event == EVENT_SESSION_START:
        # SessionStart 的 source(startup/resume/clear/compact) 不影响我们的行为
        emit(EVENT_SESSION_START, session_start_reminder(str(kb_path)))
    elif event == EVENT_USER_PROMPT:
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(EVENT_USER_PROMPT, user_prompt_reminder())
    return 0


if __name__ == "__main__":
    sys.exit(run_adapter(main))
