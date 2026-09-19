# -*- coding: utf-8 -*-
"""kb_core 单元测试（unittest，零第三方依赖）。

运行：python -m unittest discover tests/   或   python -m pytest tests/
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# 让测试能 import hooks/ 下的模块
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "hooks"))

import kb_core  # noqa: E402


class TestTriggerPattern(unittest.TestCase):
    """内置触发词命中 / 不命中。"""

    def test_hits_remember(self):
        self.assertTrue(kb_core.TRIGGER_PATTERN.search("记住这个坑"))

    def test_hits_capture(self):
        self.assertTrue(kb_core.TRIGGER_PATTERN.search("把这条沉淀一下"))

    def test_hits_promote(self):
        self.assertTrue(kb_core.TRIGGER_PATTERN.search("晋升到全局"))

    def test_misses_normal_smalltalk(self):
        for text in ["今天天气不错", "帮我改一下这个函数", "1 + 1 等于几？"]:
            with self.subTest(text=text):
                self.assertIsNone(kb_core.TRIGGER_PATTERN.search(text))


class TestShouldTriggerUserPrompt(unittest.TestCase):
    """should_trigger_user_prompt 的命中 / 不命中 / None 兜底。"""

    def setUp(self):
        self._saved = os.environ.pop(kb_core.TRIGGER_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(kb_core.TRIGGER_ENV_VAR, None)
        if self._saved is not None:
            os.environ[kb_core.TRIGGER_ENV_VAR] = self._saved

    def test_triggered_by_builtin(self):
        self.assertTrue(kb_core.should_trigger_user_prompt("记住这条经验"))

    def test_not_triggered_by_normal_prompt(self):
        self.assertFalse(kb_core.should_trigger_user_prompt("帮我写个冒泡排序"))

    def test_none_prompt_defaults_to_true(self):
        self.assertTrue(kb_core.should_trigger_user_prompt(None))


class TestTriggerEnvVar(unittest.TestCase):
    """AGENT_KB_TRIGGER 环境变量生效，并与内置正则取并集。"""

    def setUp(self):
        self._saved = os.environ.pop(kb_core.TRIGGER_ENV_VAR, None)

    def tearDown(self):
        os.environ.pop(kb_core.TRIGGER_ENV_VAR, None)
        if self._saved is not None:
            os.environ[kb_core.TRIGGER_ENV_VAR] = self._saved

    def test_env_var_adds_custom_trigger(self):
        os.environ[kb_core.TRIGGER_ENV_VAR] = "归档;复盘"
        self.assertTrue(kb_core.should_trigger_user_prompt("把这次复盘写下来"))
        self.assertTrue(kb_core.should_trigger_user_prompt("归档到库里"))

    def test_env_var_keeps_builtin_triggers(self):
        os.environ[kb_core.TRIGGER_ENV_VAR] = "归档"
        self.assertTrue(kb_core.should_trigger_user_prompt("记住这个"))

    def test_env_var_empty_falls_back_to_builtin(self):
        os.environ[kb_core.TRIGGER_ENV_VAR] = ""
        self.assertFalse(kb_core.should_trigger_user_prompt("随便聊聊"))
        self.assertTrue(kb_core.should_trigger_user_prompt("沉淀一下"))

    def test_env_var_invalid_regex_falls_back(self):
        os.environ[kb_core.TRIGGER_ENV_VAR] = "([unclosed"
        # 坏正则不该把 hook 拖挂，内置触发词仍然生效
        self.assertTrue(kb_core.should_trigger_user_prompt("记住这个"))


class TestDefaultKbPath(unittest.TestCase):
    """默认路径运行时求值，不写死 "~" 字符串。"""

    def test_runtime_evaluated(self):
        path = kb_core.default_kb_path()
        self.assertIsInstance(path, Path)
        self.assertNotIn("~", str(path))
        self.assertEqual(path, Path.home() / ".agents" / "kb")

    def test_env_override(self):
        saved = os.environ.get("AGENT_KB_PATH")
        os.environ["AGENT_KB_PATH"] = "/tmp/fake-kb"
        try:
            self.assertEqual(kb_core.default_kb_path(), Path("/tmp/fake-kb"))
        finally:
            os.environ.pop("AGENT_KB_PATH", None)
            if saved is not None:
                os.environ["AGENT_KB_PATH"] = saved


class TestIndexCounting(unittest.TestCase):
    """session_start_reminder 真读 {kb_path}/INDEX.md 统计条目数。"""

    SAMPLE_INDEX = """# 全局经验库索引（kb）

> 说明行，不算条目。

## pitfalls/ 教训与反模式

- [不要把临时目录当持久存储](pitfalls/tempdir-not-persistent.md) —— /tmp 会被清理
* [另一个坑](pitfalls/another.md) —— 星号也是条目

## workflow/ 流程与协作

- [任务闭环时总结经验](workflow/summarize-on-task-close.md) —— 花 5 分钟复盘

## 条目格式

```markdown
- [示例行在代码块内](xxx.md) —— 这行不该被计数
```
"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_index(self, text):
        (self.kb / kb_core.INDEX_FILENAME).write_text(text, encoding="utf-8")

    def test_counts_entry_lines_only(self):
        self._write_index(self.SAMPLE_INDEX)
        # 3 条真实条目；代码块内示例行不计
        self.assertEqual(kb_core.count_index_entries(self.kb), 3)

    def test_missing_index_returns_zero(self):
        self.assertEqual(kb_core.count_index_entries(self.kb), 0)

    def test_reminder_reports_real_count(self):
        self._write_index(self.SAMPLE_INDEX)
        text = kb_core.session_start_reminder(str(self.kb))
        self.assertIn("3 条", text)
        self.assertIn(str(self.kb), text)
        self.assertIn("开工钩子", text)

    def test_reminder_on_empty_kb(self):
        text = kb_core.session_start_reminder(str(self.kb))
        self.assertIn("尚无条目", text)
        self.assertNotIn("条）", text)

    def test_reminder_accepts_path_object(self):
        self._write_index("- [a](a.md) —— x\n- [b](b.md) —— y\n")
        self.assertIn("2 条", kb_core.session_start_reminder(self.kb))

    def test_default_arg_uses_runtime_path(self):
        # 不传参不报错（真实 ~/.agents/kb 可能不存在）
        self.assertIn("开工钩子", kb_core.session_start_reminder())


if __name__ == "__main__":
    unittest.main()
