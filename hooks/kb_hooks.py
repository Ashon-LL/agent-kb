# -*- coding: utf-8 -*-
"""ZCode 钩子适配器：把 kb_core 的输出塞进 ZCode 的 hookSpecificOutput 协议。

只做"协议转换"这一件事：
- SessionStart     -> kb_core.session_start_reminder()
- UserPromptSubmit -> kb_core.should_trigger_user_prompt() 过滤，通过才注入
                     kb_core.user_prompt_reminder()

⛔ 本文件**不存任何文案或触发词副本**——那些全在 kb_core.py（唯一真相源）。
   与 kb_core 同目录（平铺），所以直接 import；若被移开，import 失败时
   退化成一句极短提示，**绝不退回旧文案副本**（退回副本等于重新引入漂移）。

设计原则：任何异常都 exit 0 静默放行，绝不阻塞会话。

环境变量（全部由 kb_core 解释，本文件只透传）：
  AGENT_KB_PATH / AGENT_KB_TRIGGER / AGENT_KB_DEBUG
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import kb_core
except Exception:
    kb_core = None

MSG_DEGRADED = "【kb】经验库核心模块未能加载，沉淀规程暂不可用。"


def debug(msg):
    if os.environ.get("AGENT_KB_DEBUG", "").strip() == "1":
        print(f"[kb_hooks debug] {msg}", file=sys.stderr)


def emit(event, context):
    out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}
    sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode("utf-8"))


def main():
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    try:
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    ev = data.get("hook_event_name", "")

    if ev == "SessionStart":
        debug("SessionStart -> kb_core.session_start_reminder()")
        emit(ev, kb_core.session_start_reminder() if kb_core else MSG_DEGRADED)
    elif ev == "UserPromptSubmit":
        # should_trigger_user_prompt 返回 True 当 prompt 取不到（保险，默认注入一次）
        if kb_core and not kb_core.should_trigger_user_prompt(data.get("prompt")):
            debug("UserPromptSubmit 未命中触发词，静默")
            return 0
        debug("UserPromptSubmit 注入沉淀规程")
        emit(ev, kb_core.user_prompt_reminder() if kb_core else MSG_DEGRADED)
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        code = 0
    sys.exit(code)