# -*- coding: utf-8 -*-
"""OpenCode hook 适配器。

hook 输出格式（已核对官方文档，https://opencode.ai/docs/plugins/）：
  - OpenCode 的扩展点是 **JS/TS 插件**（不是 stdin/stdout JSON hook）：
      全局 ~/.config/opencode/plugins/  项目 .opencode/plugins/
      插件导出 async 函数，返回 hooks 对象（如 "session.created"、"tui.toast.show"）。
  - 无原生 "SessionStart / UserPromptSubmit → 注入上下文" 的 JSON 字段。
  - 因此本适配器定位为 **子进程桥**：由 JS 插件 shell 调用，stdin 收 {"hook_event_name","prompt"}，
    stdout 回 {"hookSpecificOutput": {"hookEventName","additionalContext"}}，
    插件读到 additionalContext 后自行注入（如放进 system prompt / toast 展示）。
  - 对应模板 templates/opencode-hooks.json 描述的是这个桥接约定，不是 OpenCode 原生 hook 文件。
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
    """桥接输出：hookSpecificOutput.additionalContext，由调用方 JS 插件消费。"""
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
