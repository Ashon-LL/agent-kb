# -*- coding: utf-8 -*-
"""Trae / ZCode 适配器端到端测试（unittest，零第三方依赖）。

用 subprocess 真跑 hooks/trae_zcode_adapter.py —— 验证的是「进程级」行为：
stdin 喂 JSON，检查退出码 / stdout。

运行：python -m unittest discover tests/   或   python -m pytest tests/
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
ADAPTER = _REPO_ROOT / "hooks" / "trae_zcode_adapter.py"


def run_adapter(stdin_text: str, kb_path=None, extra_env=None):
    """跑一次适配器，返回 (returncode, stdout, stderr)。"""
    env = dict(os.environ)
    env.pop("AGENT_KB_TRIGGER", None)
    if extra_env:
        env.update(extra_env)
    argv = [sys.executable, str(ADAPTER)]
    if kb_path is not None:
        argv.append(str(kb_path))
    return subprocess.run(
        argv,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


class TestAdapterBasics(unittest.TestCase):
    def test_valid_sessionstart_json(self):
        proc = run_adapter(json.dumps({"hook_event_name": "SessionStart"}))
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)          # stdout 必须是合法 JSON
        self.assertIn("hookSpecificOutput", payload)
        self.assertEqual(
            payload["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )

    def test_empty_stdin(self):
        proc = run_adapter("")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_malformed_json(self):
        proc = run_adapter("{not json at all")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_unknown_event_is_silent(self):
        proc = run_adapter(json.dumps({"hook_event_name": "SomethingElse"}))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


class TestSessionStart(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self._tmp.name)
        (self.kb / "INDEX.md").write_text(
            "# 索引\n\n"
            "- [a](a.md) —— 第一条\n"
            "- [b](b.md) —— 第二条\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_output_contains_session_hook_and_real_count(self):
        proc = run_adapter(
            json.dumps({"hook_event_name": "SessionStart"}), kb_path=self.kb
        )
        self.assertEqual(proc.returncode, 0)
        ctx = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("开工钩子", ctx)
        self.assertIn("2 条", ctx)


class TestUserPromptSubmit(unittest.TestCase):
    def _context(self, proc):
        return json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_trigger_word_injects_capture_hook(self):
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "记住这个坑"}
        proc = run_adapter(json.dumps(payload))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("沉淀钩子", self._context(proc))

    def test_no_trigger_word_is_silent(self):
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "帮我写个排序"}
        proc = run_adapter(json.dumps(payload))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_custom_trigger_via_env_var(self):
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "归档这条"}
        proc = run_adapter(
            json.dumps(payload), extra_env={"AGENT_KB_TRIGGER": "归档"}
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("沉淀钩子", self._context(proc))

    def test_hook_event_name_matches(self):
        payload = {"hook_event_name": "UserPromptSubmit", "prompt": "沉淀一下"}
        proc = run_adapter(json.dumps(payload))
        hook = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(hook["hookEventName"], "UserPromptSubmit")


if __name__ == "__main__":
    unittest.main()
