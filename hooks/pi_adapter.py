# -*- coding: utf-8 -*-
"""PI (Perplexity) hook 适配器。

# TODO: emit format not verified
  - 未找到 Perplexity / PI 官方 Agent hook 输出格式文档（PI 目前公开的 hooks 接口不明确）。
  - 暂按本项目通用约定输出：
      {"hookSpecificOutput": {"hookEventName": "<Event>", "additionalContext": "<ctx>"}}
  - 配置位置待核实（模板 templates/pi-hooks.json 为占位结构）。
  - 若官方文档确认字段不同，只需改本文件 emit() 一处。
  - 退出码：0 成功；本项目永不阻塞，任何异常静默 exit 0。
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
    """PI hook 输出格式（未核实，占位）：hookSpecificOutput.additionalContext。"""
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
