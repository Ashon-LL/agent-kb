# -*- coding: utf-8 -*-
"""Codex CLI hook 适配器（.codex/hooks.json 使用）。

Codex hook 输出格式：
  - systemMessage -> 注入到 system message
  - decision -> 可影响控制流（本项目不使用）
"""
import sys
import json
from pathlib import Path

KB_PATH = Path.home() / ".agents" / "kb"

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
from kb_core import (  # noqa: E402
    session_start_reminder,
    user_prompt_reminder,
    should_trigger_user_prompt,
)


def emit(msg: str) -> None:
    """Codex hook 接受 systemMessage 字段。"""
    out = {"systemMessage": msg}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0

    ev = data.get("hook_event_name", "")

    if ev == "SessionStart":
        emit(session_start_reminder(str(KB_PATH)))
    elif ev == "UserPromptSubmit":
        prompt = data.get("prompt")
        if not should_trigger_user_prompt(prompt):
            return 0
        emit(user_prompt_reminder())
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
