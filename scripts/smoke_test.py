# -*- coding: utf-8 -*-
"""agent-kb 冒烟测试：真跑 Trae/ZCode 适配器，验证 hook 输出契约。

不依赖第三方库，起 subprocess 喂 stdin JSON，检查 stdout 是否是合法 JSON 且字段正确。

三个场景：
  1) SessionStart        → 注入开工钩子，hookEventName=SessionStart
  2) UserPromptSubmit+触发词 → 注入沉淀钩子，hookEventName=UserPromptSubmit
  3) UserPromptSubmit 无触发词 → 无 stdout（静默放行）

运行：python scripts/smoke_test.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTER = _REPO_ROOT / "hooks" / "trae_zcode_adapter.py"

TRIGGER_WORD = "记住"
FAKE_INDEX = "# 索引\n\n- [a](a.md) —— 冒烟示例\n- [b](b.md) —— 冒烟示例二\n"


def run_adapter(stdin_obj, kb_path=None, extra_env=None):
    """跑一次适配器，返回 (returncode, stdout_text, stderr_text)。"""
    env = dict(os.environ)
    env.pop("AGENT_KB_TRIGGER", None)
    if extra_env:
        env.update(extra_env)

    argv = [sys.executable, str(ADAPTER)]
    if kb_path is not None:
        argv.append(str(kb_path))

    try:
        proc = subprocess.run(
            argv,
            input=json.dumps(stdin_obj, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except Exception as exc:  # 起不来进程也算失败，不炸栈
        return -1, "", f"执行适配器失败: {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def check_session_start(kb_path):
    """场景 1：SessionStart 必须返回合法 JSON + hookSpecificOutput.additionalContext。"""
    code, out, err = run_adapter({"hook_event_name": "SessionStart"}, kb_path)
    if code != 0:
        return False, f"exit={code}（期望 0）{err.strip()}"
    if not out.strip():
        return False, "stdout 为空，期望注入开工钩子"
    try:
        payload = json.loads(out)
    except Exception as exc:
        return False, f"stdout 不是合法 JSON: {exc}"
    hook = payload.get("hookSpecificOutput")
    if not isinstance(hook, dict):
        return False, "缺 hookSpecificOutput 字段"
    if hook.get("hookEventName") != "SessionStart":
        return False, f"hookEventName={hook.get('hookEventName')!r}，期望 'SessionStart'"
    ctx = hook.get("additionalContext") or ""
    if "开工钩子" not in ctx:
        return False, "additionalContext 缺“开工钩子”"
    if "2 条" not in ctx:
        return False, "additionalContext 未反映 INDEX.md 真实条目数（期望 2 条）"
    return True, "SessionStart 注入开工钩子，条数统计正确"


def check_user_prompt_triggered(kb_path=None):
    """场景 2：UserPromptSubmit 带触发词，必须返回合法 JSON + 沉淀钩子。"""
    code, out, err = run_adapter(
        {"hook_event_name": "UserPromptSubmit", "prompt": f"{TRIGGER_WORD}这个坑"}
    )
    if code != 0:
        return False, f"exit={code}（期望 0）{err.strip()}"
    if not out.strip():
        return False, "stdout 为空，期望注入沉淀钩子"
    try:
        payload = json.loads(out)
    except Exception as exc:
        return False, f"stdout 不是合法 JSON: {exc}"
    hook = payload.get("hookSpecificOutput")
    if not isinstance(hook, dict):
        return False, "缺 hookSpecificOutput 字段"
    if hook.get("hookEventName") != "UserPromptSubmit":
        return False, (
            f"hookEventName={hook.get('hookEventName')!r}，期望 'UserPromptSubmit'"
        )
    if "沉淀钩子" not in (hook.get("additionalContext") or ""):
        return False, "additionalContext 缺“沉淀钩子”"
    return True, f"触发词 {TRIGGER_WORD!r} 命中，注入沉淀钩子"


def check_user_prompt_not_triggered(kb_path=None):
    """场景 3：UserPromptSubmit 无触发词，必须静默（exit 0 无 stdout）。"""
    code, out, err = run_adapter(
        {"hook_event_name": "UserPromptSubmit", "prompt": "帮我写个冒泡排序"}
    )
    if code != 0:
        return False, f"exit={code}（期望 0）{err.strip()}"
    if out.strip():
        return False, f"期望无输出，实际: {out.strip()[:80]}"
    return True, "无触发词静默放行"


def main() -> int:
    if not ADAPTER.exists():
        print(f"[FAIL] 找不到适配器: {ADAPTER}", file=sys.stderr)
        print("[FAIL] 0/3")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        kb = Path(tmp)
        (kb / "INDEX.md").write_text(FAKE_INDEX, encoding="utf-8")

        cases = [
            ("SessionStart 注入", check_session_start, kb),
            ("UserPromptSubmit 触发", check_user_prompt_triggered, None),
            ("UserPromptSubmit 不触发", check_user_prompt_not_triggered, None),
        ]

        passed = 0
        for i, (name, fn, arg) in enumerate(cases, 1):
            ok, detail = fn(arg)
            mark = "[PASS]" if ok else "[FAIL]"
            print(f"{mark} {i}/3 {name} —— {detail}")
            passed += 1 if ok else 0

    print(f"[{'PASS' if passed == len(cases) else 'FAIL'}] {passed}/3")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
