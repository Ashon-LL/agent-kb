# -*- coding: utf-8 -*-
"""Qoder（IDE / JetBrains 插件 / CLI）hook 适配器。

hook 输出格式（已核对官方文档，https://docs.qoder.com/extensions/hooks）：
  - 配置位置：~/.qoder/settings.json 的 "hooks" 键（IDE 与 CLI 共用该文件）
  - 事件：SessionStart（无 matcher）/ UserPromptSubmit（无 matcher）
  - stdin 收到事件 JSON（含 hook_event_name、prompt 等）
  - stdout 返回：
      {"hookSpecificOutput": {"hookEventName": "<Event>", "additionalContext": "<ctx>"}}
  - 退出码：0 成功；2 阻塞（stderr 内容展示给用户）。本项目永不阻塞，异常静默 exit 0。
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
    """Qoder hook 输出格式：hookSpecificOutput.additionalContext。"""
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
