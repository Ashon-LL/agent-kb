# -*- coding: utf-8 -*-
"""Claude Desktop / Claude Code hook 适配器。

hook 输出格式（已核对官方 Hooks reference，https://docs.claude.com/en/docs/claude-code/hooks）：
  - 配置位置：~/.claude/settings.json（用户级）或 .claude/settings.json（项目级）
    —— 用 "hooks" 顶层键注册，不是独立的 hooks 文件
  - stdout 返回 JSON：
      SessionStart      -> hookSpecificOutput.additionalContext（注入上下文，不阻塞）
      UserPromptSubmit  -> hookSpecificOutput.additionalContext（注入上下文，不阻塞）
  - 退出码：0 成功；2 阻塞（UserPromptSubmit 会拦下这条 prompt）。本项目永不阻塞，
    任何异常静默 exit 0。
"""
import sys
import json
from pathlib import Path

KB_PATH = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else Path.home() / ".agents" / "kb"
)

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
from kb_core import (  # noqa: E402
    session_start_reminder,
    user_prompt_reminder,
    should_trigger_user_prompt,
)


def emit(event_name: str, context: str) -> None:
    """Claude hook 输出格式：hookSpecificOutput.additionalContext 注入上下文。

    不返回 decision 字段 —— 保持"增强而非阻塞"语义。
    """
    out = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    ev = data.get("hook_event_name", "")

    if ev == "SessionStart":
        emit(ev, session_start_reminder(str(KB_PATH)))
    elif ev == "UserPromptSubmit":
        prompt = data.get("prompt")
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(ev, user_prompt_reminder())
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
