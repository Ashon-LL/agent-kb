# -*- coding: utf-8 -*-
"""WorkBuddy / CodeBuddy hook 适配器。

hook 输出格式（已核对官方文档，https://www.codebuddy.ai/docs/cli/hooks）：
  - 配置位置（多 scope 合并）：~/.codebuddy/settings.json（用户级）
    或 <project>/.codebuddy/settings.json（项目级，另可 settings.local.json）
  - 事件：SessionStart（无 matcher）/ UserPromptSubmit（无 matcher）
  - stdin 收到事件 JSON（含 session_id、transcript_path、cwd、hook_event_name、prompt 等）
  - stdout 返回 JSON：
      SessionStart:
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<ctx>"}}
      UserPromptSubmit:
        {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "<ctx>"}}
        （若要拦截 prompt：continue=false + reason，本项目不用，保持"增强而非阻塞"）
  - WorkBuddy IDE 复用同一 hooks 实现（官方文档站为 CLI 与 WorkBuddy 并列）。
  - 退出码：0 成功；2 阻塞。本项目永不阻塞，任何异常静默 exit 0。
  - 注意：Windows 下 CodeBuddy 强制走 Git Bash 执行 hook 命令，Python 脚本显式用 python3 调起。
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
    """CodeBuddy/WorkBuddy hook 输出格式：hookSpecificOutput.additionalContext 注入上下文。"""
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
