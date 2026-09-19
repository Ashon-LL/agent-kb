# -*- coding: utf-8 -*-
"""OpenClaw hook 适配器。

hook 输出格式（已核对官方文档，https://github.com/openclaw/openclaw/blob/main/docs/plugins/hooks/reference.md）：
  - 扩展点是 **原生 JS/TS 插件**（package.json 里 openclaw.extensions 指向 index.ts，
    入口用 definePluginEntry({ register(api){ api.on("<hook>", handler) } })）。
  - 与本项目最贴合的两个 typed hook：
      session_start       (Observe)  —— 会话边界，适合注入开工提醒（本次由桥接到 SessionStart 触发）
      before_prompt_build (Modify)   —— 可"Add prompt context"，适合注入用户 prompt 相关提醒
  - OpenClaw 原生 hook 是 TS 回调，不读 stdin JSON。故本适配器为 **子进程桥**：
    JS 插件 shell 调用本脚本，stdin 收 {"hook_event_name","prompt"}，
    stdout 回 {"hookSpecificOutput": {"hookEventName","additionalContext"}}，
    插件把 additionalContext 通过 before_prompt_build 的返回值注入 prompt 上下文。
  - 对应模板 templates/openclaw-hooks.json 描述桥接约定。
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
    """桥接输出：hookSpecificOutput.additionalContext，由调用方 JS/TS 插件消费。"""
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

    # 接受原生名（session_start）与统一名（SessionStart）
    if ev in ("SessionStart", "session_start"):
        emit("SessionStart", session_start_reminder(str(KB_PATH)))
    elif ev in ("UserPromptSubmit", "before_prompt_build"):
        prompt = data.get("prompt")
        if not should_trigger_user_prompt(prompt):
            return 0
        emit("UserPromptSubmit", user_prompt_reminder())
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)
