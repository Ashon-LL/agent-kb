# -*- coding: utf-8 -*-
"""agent-kb 适配器公共底座（平台无关）。

所有平台适配器统一从这里取「运行期配置」和「事件解析」逻辑，避免 10 个文件
各写一份 KB_PATH 解析、各写一份 stdin 解析、各写一份 debug 输出。

## 环境变量（全 10 平台统一生效）

| 变量 | 取值 | 语义 |
|---|---|---|
| `AGENT_KB_PATH`  | 目录路径 | 覆盖默认 kb 路径。**优先级最高**，高于 `sys.argv[1]` |
| `AGENT_KB_DEBUG` | `1` 开启 | 开启后向 **stderr** 输出 `[agent-kb debug] ...` 诊断行 |

## kb 路径解析优先级（高 → 低）

1. `AGENT_KB_PATH` 环境变量（非空即用）
2. `sys.argv[1]`（平台 hooks.json 里写死的路径参数）
3. `~/.agents/kb`（默认值，运行时求值，不硬编码）

## debug 输出

`AGENT_KB_DEBUG=1` 时，每次 hook 触发输出一行到 stderr：

    [agent-kb debug] 事件=SessionStart prompt_len=0 kb_path=/home/u/.agents/kb

stderr 不被平台当成 hook 返回值消费（各平台只读 stdout / 退出码），
所以调试输出天然安全，不会污染注入内容。

## 事件名归一化

各平台 stdin 字段不同，本模块统一映射到两个规范名：
`SessionStart` 与 `UserPromptSubmit`。映射表见各适配器文件头注释。

## 零阻塞承诺

任何解析异常一律返回空，适配器侧 `main()` 永不抛异常、恒 exit 0。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 默认库路径：运行时求值，兼容非 POSIX 环境（不写死 "~/.agents/kb" 字符串）
ENV_KB_PATH = "AGENT_KB_PATH"
ENV_DEBUG = "AGENT_KB_DEBUG"

# 规范事件名
EVENT_SESSION_START = "SessionStart"
EVENT_USER_PROMPT = "UserPromptSubmit"


def default_kb_path() -> Path:
    """默认 kb 路径：~/.agents/kb（运行时求值）。"""
    return Path.home() / ".agents" / "kb"


def resolve_kb_path(argv: list[str] | None = None) -> Path:
    """解析 kb 路径。优先级：AGENT_KB_PATH > sys.argv[1] > ~/.agents/kb。"""
    env_val = os.environ.get(ENV_KB_PATH, "").strip()
    if env_val:
        return Path(env_val).expanduser()

    args = sys.argv if argv is None else argv
    if len(args) > 1 and args[1].strip():
        return Path(args[1]).expanduser()

    return default_kb_path()


def debug_enabled() -> bool:
    """AGENT_KB_DEBUG 是否开启（值为 "1" 视为开启）。"""
    return os.environ.get(ENV_DEBUG, "").strip() == "1"


def debug_log(event: str, prompt: str | None, kb_path: object) -> None:
    """向 stderr 输出一行诊断信息（仅 AGENT_KB_DEBUG=1 时）。"""
    if not debug_enabled():
        return
    prompt_len = len(prompt) if isinstance(prompt, str) else 0
    sys.stderr.write(
        f"[agent-kb debug] 事件={event} prompt_len={prompt_len} kb_path={kb_path}\n"
    )
    sys.stderr.flush()


def read_stdin_json() -> dict:
    """读取 stdin 并解析 JSON。空输入 / 畸形 JSON 一律返回 {}，绝不抛异常。"""
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def first_present(data: dict, keys: tuple[str, ...]) -> object:
    """按顺序返回第一个存在且非 None 的键值（各平台字段名不同时用）。"""
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def normalize_event(raw_event: object) -> str:
    """把各平台原生事件名归一化成规范事件名。

    返回 "" 表示不关心该事件，适配器应静默 exit 0。
    """
    if not isinstance(raw_event, str):
        return ""
    name = raw_event.strip()
    if not name:
        return ""

    # 大小写 / 下划线 / 连字符 归一
    norm = name.replace("-", "_")
    lower = norm.lower()
    snake = ""
    for ch in norm:
        if ch.isupper() and snake:
            snake += "_"
        snake += ch.lower()

    candidates = {lower, snake, norm}

    if candidates & {
        "sessionstart",
        "session_start",
        "session.created",
        "session_created",
        "startup",
        "on_session_start",
    }:
        return EVENT_SESSION_START

    if candidates & {
        "userpromptsubmit",
        "user_prompt_submit",
        "before_prompt_build",
        "beforepromptbuild",
        "user_prompt",
        "on_user_prompt",
    }:
        return EVENT_USER_PROMPT

    return ""


def extract_prompt(data: dict) -> str | None:
    """从 stdin JSON 里取用户 prompt，兼容各平台字段名。

    找不到返回 None（表示"拿不到 prompt"，由 kb_core 决定默认行为）。
    """
    value = first_present(
        data,
        ("prompt", "user_prompt", "userPrompt", "message", "content", "text"),
    )
    return value if isinstance(value, str) else None


def emit_text(text: str) -> None:
    """向 stdout 写纯文本（UTF-8 字节）。"""
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def emit_json(payload: dict) -> None:
    """向 stdout 写 JSON（UTF-8，不转义中文，不追加换行）。"""
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.flush()


def claude_style_payload(event_name: str, context: str) -> dict:
    """Claude Code 风格载荷：hookSpecificOutput.additionalContext。"""
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }


def run_adapter(main_func) -> int:
    """适配器统一入口包装：任何异常静默 exit 0（零阻塞承诺）。"""
    try:
        code = main_func()
    except Exception:
        code = 0
    return code if isinstance(code, int) else 0
