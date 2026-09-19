# -*- coding: utf-8 -*-
"""adapter_base 与全平台适配器的公共契约测试（零第三方依赖）。"""
import importlib
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import adapter_base  # noqa: E402

# 10 个平台适配器（trae 与 zcode 共用一个文件）
ADAPTERS = [
    "claude_adapter",
    "codex_adapter",
    "hermes_adapter",
    "kimi_adapter",
    "openclaw_adapter",
    "opencode_adapter",
    "pi_adapter",
    "qoder_adapter",
    "trae_zcode_adapter",
    "workbuddy_adapter",
]


class TestAdapterBase(unittest.TestCase):
    def test_env_path_beats_argv(self):
        os.environ["AGENT_KB_PATH"] = "/tmp/env-kb"
        try:
            self.assertEqual(
                adapter_base.resolve_kb_path(["x.py", "/tmp/argv-kb"]),
                Path("/tmp/env-kb"),
            )
        finally:
            del os.environ["AGENT_KB_PATH"]

    def test_argv_beats_default(self):
        os.environ.pop("AGENT_KB_PATH", None)
        self.assertEqual(
            adapter_base.resolve_kb_path(["x.py", "/tmp/argv-kb"]),
            Path("/tmp/argv-kb"),
        )

    def test_default_is_home_based(self):
        os.environ.pop("AGENT_KB_PATH", None)
        self.assertEqual(
            adapter_base.resolve_kb_path(["x.py"]),
            Path.home() / ".agents" / "kb",
        )

    def test_normalize_event(self):
        n = adapter_base.normalize_event
        self.assertEqual(n("SessionStart"), "SessionStart")
        self.assertEqual(n("session_start"), "SessionStart")
        self.assertEqual(n("session.created"), "SessionStart")
        self.assertEqual(n("UserPromptSubmit"), "UserPromptSubmit")
        self.assertEqual(n("before_prompt_build"), "UserPromptSubmit")
        self.assertEqual(n("tui.prompt.append"), "UserPromptSubmit")
        self.assertEqual(n("unrelated_event"), "")

    def test_read_stdin_json_tolerates_garbage(self):
        old = sys.stdin
        try:
            sys.stdin = type("S", (), {"buffer": io.BytesIO(b"not json")})()
            self.assertEqual(adapter_base.read_stdin_json(), {})
            sys.stdin = type("S", (), {"buffer": io.BytesIO(b"")})()
            self.assertEqual(adapter_base.read_stdin_json(), {})
        finally:
            sys.stdin = old


def _run(adapter: str, payload: object, env_extra: dict | None = None):
    env = dict(os.environ)
    env["AGENT_KB_PATH"] = "/tmp/adapter-test-kb"
    if env_extra:
        env.update(env_extra)
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOKS_DIR / f"{adapter}.py")],
        input=raw.encode("utf-8"),
        capture_output=True,
        env=env,
        timeout=20,
    )


class TestAllAdapters(unittest.TestCase):
    """10 个适配器的公共契约：零阻塞 + 事件路由 + 环境变量生效。"""

    def test_malformed_json_exits_zero_silently(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, "{not json at all")
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout, b"")

    def test_empty_stdin_exits_zero_silently(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, "")
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout, b"")

    def test_session_start_route_emits(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, {"hook_event_name": "SessionStart"})
                self.assertEqual(r.returncode, 0)
                out = r.stdout.decode("utf-8")
                self.assertIn("kb", out)
                self.assertIn("/tmp/adapter-test-kb", out)

    def test_unrelated_event_is_silent(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, {"hook_event_name": "PreToolUse", "prompt": "记住"})
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout, b"")

    def test_trigger_word_emits_prompt_reminder(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, {"hook_event_name": "UserPromptSubmit", "prompt": "记住这个坑"})
                self.assertEqual(r.returncode, 0)
                self.assertIn("沉淀", r.stdout.decode("utf-8"))

    def test_no_trigger_word_is_silent(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(a, {"hook_event_name": "UserPromptSubmit", "prompt": "今天天气不错"})
                self.assertEqual(r.returncode, 0)
                self.assertEqual(r.stdout, b"")

    def test_debug_goes_to_stderr_not_stdout(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                r = _run(
                    a,
                    {"hook_event_name": "SessionStart"},
                    env_extra={"AGENT_KB_DEBUG": "1"},
                )
                self.assertIn(b"[agent-kb debug]", r.stderr)
                self.assertNotIn(b"[agent-kb debug]", r.stdout)

    def test_agent_kb_path_env_beats_argv(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                env = dict(os.environ)
                env["AGENT_KB_PATH"] = "/tmp/env-wins"
                r = subprocess.run(
                    [sys.executable, str(HOOKS_DIR / f"{a}.py"), "/tmp/argv-loses"],
                    input=json.dumps({"hook_event_name": "SessionStart"}).encode(),
                    capture_output=True,
                    env=env,
                    timeout=20,
                )
                self.assertIn(b"/tmp/env-wins", r.stdout)
                self.assertNotIn(b"/tmp/argv-loses", r.stdout)


class TestPlatformSpecifics(unittest.TestCase):
    def test_codex_uses_event_field_and_system_message(self):
        r = _run("codex_adapter", {"event": "SessionStart", "session_id": "s"})
        out = json.loads(r.stdout.decode("utf-8"))
        self.assertIn("systemMessage", out)
        self.assertNotIn("hookSpecificOutput", out)

    def test_codex_ignores_hook_event_name_alias(self):
        # 兜底路径：event 缺失时回退 hook_event_name
        r = _run("codex_adapter", {"hook_event_name": "SessionStart"})
        self.assertIn("systemMessage", json.loads(r.stdout.decode("utf-8")))

    def test_kimi_emits_plain_text_not_json(self):
        r = _run("kimi_adapter", {"hook_event_name": "SessionStart"})
        text = r.stdout.decode("utf-8")
        self.assertTrue(text.startswith("[kb:SessionStart]"))
        with self.assertRaises(json.JSONDecodeError):
            json.loads(text)

    def test_claude_style_platforms_emit_hook_specific_output(self):
        for a in ("claude_adapter", "qoder_adapter", "workbuddy_adapter",
                  "trae_zcode_adapter", "openclaw_adapter", "opencode_adapter",
                  "hermes_adapter", "pi_adapter"):
            with self.subTest(adapter=a):
                r = _run(a, {"hook_event_name": "SessionStart"})
                out = json.loads(r.stdout.decode("utf-8"))
                self.assertEqual(
                    out["hookSpecificOutput"]["hookEventName"], "SessionStart"
                )

    def test_opencode_nested_event_shape(self):
        r = _run(
            "opencode_adapter",
            {"event": {"type": "session.created", "properties": {"info": {"id": "s"}}}},
        )
        out = json.loads(r.stdout.decode("utf-8"))
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")

    def test_opencode_nested_prompt(self):
        r = _run(
            "opencode_adapter",
            {"event": {"type": "tui.prompt.append", "properties": {"prompt": {"text": "记住"}}}},
        )
        self.assertIn("沉淀", r.stdout.decode("utf-8"))

    def test_openclaw_native_event_names(self):
        r1 = _run("openclaw_adapter", {"hook_event_name": "session_start"})
        self.assertIn("开工", r1.stdout.decode("utf-8"))
        r2 = _run("openclaw_adapter", {"hook_event_name": "before_prompt_build", "prompt": "沉淀"})
        self.assertIn("沉淀钩子", r2.stdout.decode("utf-8"))


class TestHeaderDocumentation(unittest.TestCase):
    """AC：每个适配器文件头必须写清 平台 / hook 文档 / stdin 映射 / stdout 格式。"""

    REQUIRED_SECTIONS = ("## 平台", "## Hook 文档", "stdin 字段映射表", "stdout 格式说明")

    def test_every_adapter_header_is_documented(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                head = (HOOKS_DIR / f"{a}.py").read_text(encoding="utf-8")
                # 只查文件头（首个函数/import 之前的文档块）
                doc = head.split('"""')[1] if head.count('"""') >= 2 else head
                for section in self.REQUIRED_SECTIONS:
                    self.assertIn(section, doc, f"{a}: header missing {section!r}")

    def test_every_adapter_documents_env_vars(self):
        for a in ADAPTERS:
            with self.subTest(adapter=a):
                text = (HOOKS_DIR / f"{a}.py").read_text(encoding="utf-8")
                doc = text.split('"""')[1] if text.count('"""') >= 2 else text
                self.assertIn("AGENT_KB_PATH", doc)
                self.assertIn("AGENT_KB_DEBUG", doc)
                # 必须真的 import adapter_base 才能生效
                self.assertIn("from adapter_base import", text)


if __name__ == "__main__":
    unittest.main()
