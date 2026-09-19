# -*- coding: utf-8 -*-
"""Trae / ZCode 平台 Hook 适配器。

stdin 读平台回调的 JSON，stdout 输出平台可消费的 hook 结果 JSON。
任何异常静默 exit 0，不阻塞会话。
"""
import sys
import json
from pathlib import Path

# 允许用户用环境变量或参数覆盖 kb 路径
KB_PATH = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else Path.home() / ".agents" / "kb"
)

# 把同仓库的 hooks/ 目录加到 sys.path，方便 import kb_core
_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
from kb_core import (  # noqa: E402
    session_start_reminder,
    user_prompt_reminder,
    should_trigger_user_prompt,
)


def emit(event_name: str, context: str) -> None:
    """Trae/ZCode hook 约定的输出格式：stdout 写 JSON，含 hookSpecificOutput 字段。"""
    out = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }
    sys.stdout.buffer.write(
        json.dumps(out, ensure_ascii=False).encode("utf-8")
    )


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
