# -*- coding: utf-8 -*-
"""Kimi Code CLI hook 适配器。

hook 输出格式（已核对官方文档，https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/customization/hooks.md）：
  - 配置位置：~/.kimi-code/config.toml 的 [[hooks]] 数组（注意：**TOML 不是 JSON**）。
      每条规则字段仅 4 个：event / matcher / command / timeout（1-600 秒，默认 30）。
      例：[[hooks]] event="SessionStart"  command="python3 .../kimi_adapter.py"
  - 事件：SessionStart（matcher 匹配 startup|resume）/ UserPromptSubmit（matcher 匹配用户提交文本）
  - stdin 收到事件 JSON（含 hook_event_name、session_id、session_title、client_type、cwd、prompt 等）
  - 返回值：主要看 **退出码** —— 0 放行、2 拦截、其他视为脚本错误(放行)。
      **stdout 文本内容会被追加进上下文**（这就是我们的注入通道，无需 JSON 包装）。
      另有可选 JSON 形式（仅 PreToolUse/Stop/UserPromptSubmit 生效）用于拦截决策。
  - 本项目策略：只注入上下文、永不拦截 → 直接往 stdout 写纯文本，始终 exit 0。
  - 模板 templates/kimi-hooks.json 是"结构化占位"，实际要转写成 TOML 写进 config.toml。
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
    """Kimi Code hook 输出格式：stdout 纯文本会被追加进上下文（不需 JSON 包装）。

    保持事件前缀，便于在 transcript 里分辨来源。
    """
    text = f"[kb:{event_name}] {context}\n"
    sys.stdout.buffer.write(text.encode("utf-8"))


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
