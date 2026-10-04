# -*- coding: utf-8 -*-
"""kb_validate.check_triggers（触发词副本一致性）单元测试。

运行：python -m unittest tests.test_kb_validate_triggers -v
覆盖三组检查：① kb_hooks.py 不存触发词副本 ② config.json matcher 与 kb_core 一致
③ 全机 kb_core.py 部署副本（硬链 intact / 断链内容一致 / 内容漂移）。
全部经参数注入临时目录，不触碰真实部署路径，Windows 与 CI 容器均可跑。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "hooks"))

import kb_validate  # noqa: E402

# 能被 _TRIGGER_RE 解析出触发词的源码形状（与真实 kb_core.py 的写法一致）
SRC_OK = (
    "# -*- coding: utf-8 -*-\n"
    "import re\n\n"
    "TRIGGER_PATTERN = re.compile(\n"
    '    r"记住|沉淀|晋升|以后别|下次别|全局经验"\n'
    ")\n"
)
SRC_NO_TRIGGER = "# -*- coding: utf-8 -*-\nprint('hello')\n"

HOOKS_CLEAN = (
    "# -*- coding: utf-8 -*-\n"
    "import kb_core\n\n"
    "def main():\n"
    "    return 0\n"
)
# 钩子里存了漂移副本（正是 2026-10-02 分叉事故的形态）
HOOKS_DRIFT = (
    "import re\n"
    "TRIGGER_PATTERN = re.compile(r\"记住|沉淀|旧词\")\n"
)
# 钩子里存的副本内容与源一致（词序/空白不同也应视为一致）
HOOKS_SAME_COPY = (
    "import re\n"
    "TRIGGER_PATTERN = re.compile(\n"
    '    r"全局经验 | 下次别 | 以后别 | 晋升 | 沉淀 | 记住"\n'
    ")\n"
)

MATCHER_OK = "记住|沉淀|晋升|以后别|下次别|全局经验"
MATCHER_DRIFT = "记住|沉淀|晋升"


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _write_config(path: Path, matcher) -> Path:
    grps = [{"matcher": matcher, "hooks": []}] if matcher is not None else [{"hooks": []}]
    cfg = {"hooks": {"enabled": True, "events": {"UserPromptSubmit": grps}}}
    path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return path


class CheckTriggersCase(unittest.TestCase):
    """公共脚手架：每个用例一个干净的临时目录。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.src = _write(self.dir / "kb_core.py", SRC_OK)
        self.hooks = _write(self.dir / "kb_hooks.py", HOOKS_CLEAN)
        self.config = _write_config(self.dir / "config.json", MATCHER_OK)

    def tearDown(self):
        self._tmp.cleanup()

    def run_check(self, copies=None, **overrides):
        kwargs = dict(hooks_rel=self.hooks, zcode_config=self.config,
                      source=self.src, copies=copies or [])
        kwargs.update(overrides)
        return kb_validate.check_triggers(**kwargs)


class TestHooksCopy(CheckTriggersCase):
    """① kb_hooks.py：import kb_core、不存副本是正确状态；存了漂移副本必须报。"""

    def test_clean_hooks_pass(self):
        problems, notes = self.run_check()
        self.assertEqual(problems, [])
        self.assertTrue(any("kb_hooks.py" in n for n in notes))

    def test_hooks_missing_in_non_zcode_env_is_note_only(self):
        # 非 ZCode 环境（config.json 不存在）：入口缺失无从核对，只记 note
        self.config.unlink()
        self.hooks.unlink()
        problems, notes = self.run_check()
        self.assertEqual(problems, [])
        self.assertTrue(any("kb_hooks.py 不在" in n for n in notes))

    def test_hooks_missing_in_zcode_env_fails(self):
        # config.json 在 = ZCode 部署环境，入口脚本丢了是钩子全死，不是「未部署」
        self.hooks.unlink()
        problems, _ = self.run_check()
        self.assertTrue(any("钩子入口丢失" in p for p in problems))

    def test_hooks_drifted_copy_fails(self):
        _write(self.hooks, HOOKS_DRIFT)
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 1)
        self.assertIn("[trigger] kb_hooks.py", problems[0])
        self.assertIn("漂移源", problems[0])

    def test_hooks_identical_copy_passes(self):
        # 副本内容与源一致（词序/空白不同）不报——报的判据是内容不一致，不是"存在副本"
        _write(self.hooks, HOOKS_SAME_COPY)
        problems, _ = self.run_check()
        self.assertEqual(problems, [])


class TestConfigMatcher(CheckTriggersCase):
    """② config.json matcher：与源一致；漂移与"无 matcher"都是真故障。"""

    def test_matching_matcher_passes(self):
        problems, _ = self.run_check()
        self.assertEqual(problems, [])

    def test_drifted_matcher_fails(self):
        _write_config(self.config, MATCHER_DRIFT)
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 1)
        self.assertIn("matcher 与 kb_core.TRIGGER_PATTERN 不一致", problems[0])

    def test_missing_matcher_is_error_not_skip(self):
        # 文件在但解析不出 matcher —— 正是 2026-10-04 修正要抓的情形，不得静默跳过
        _write_config(self.config, None)
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 1)
        self.assertIn("没有 matcher", problems[0])

    def test_config_absent_is_note_only(self):
        self.config.unlink()
        problems, notes = self.run_check()
        self.assertEqual(problems, [])
        self.assertTrue(any("跳过配置比对" in n for n in notes))


class TestDeployCopies(CheckTriggersCase):
    """③ kb_core 部署副本：samefile 放行；断链内容一致提示；内容漂移报错。"""

    def _new_copy(self, content=None):
        copy = self.dir / f"copy{len(list(self.dir.iterdir()))}.py"
        return _write(copy, content if content is not None else SRC_OK)

    def test_hardlinked_copy_is_silent_pass(self):
        copy = self._new_copy()
        copy.unlink()
        try:
            os.link(self.src, copy)
        except OSError:
            self.skipTest("此文件系统不支持硬链接")
        problems, notes = self.run_check(copies=[copy])
        self.assertEqual(problems, [])
        self.assertFalse(any(str(copy) in n for n in notes))  # 同 inode 不刷屏

    def test_broken_link_same_content_is_note(self):
        copy = self._new_copy()  # 独立文件、内容一致 → 断链态
        problems, notes = self.run_check(copies=[copy])
        self.assertEqual(problems, [])
        self.assertTrue(any("硬链已断" in n for n in notes))

    def test_drifted_copy_fails(self):
        copy = self._new_copy(SRC_OK.replace("全局经验", "旧词"))
        problems, _ = self.run_check(copies=[copy])
        self.assertEqual(len(problems), 1)
        self.assertIn("内容不一致", problems[0])
        self.assertIn("漂移源", problems[0])

    def test_absent_copy_is_note_only(self):
        copy = self.dir / "not_deployed.py"
        problems, notes = self.run_check(copies=[copy])
        self.assertEqual(problems, [])
        self.assertTrue(any("副本不存在" in n for n in notes))


class TestSourceParsing(CheckTriggersCase):
    """真源自身解析不出触发词 = 钩子与校验同时失效，必须报 FAIL（2026-10-04 升级）。"""

    def test_unparseable_source_fails(self):
        _write(self.src, SRC_NO_TRIGGER)
        problems, _ = self.run_check()
        self.assertEqual(len(problems), 1)
        self.assertIn("钩子与校验器同时失效", problems[0])

    def test_missing_source_fails(self):
        self.src.unlink()
        problems, _ = self.run_check()
        self.assertTrue(any("解析不出触发词（missing）" in p for p in problems))


class TestHooksEnabled(CheckTriggersCase):
    """②b config.json 的 hooks 开关：matcher 完好而开关关闭时不得全绿。"""

    def _write_config_enabled(self, root_enabled, entry_enabled=None):
        hook = {"type": "process", "command": "python", "args": ["kb_hooks.py"]}
        if entry_enabled is not None:
            hook["enabled"] = entry_enabled
        cfg = {
            "hooks": {
                "enabled": root_enabled,
                "events": {"UserPromptSubmit": [{"matcher": MATCHER_OK, "hooks": [hook]}]},
            }
        }
        self.config.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    def test_enabled_true_passes(self):
        self._write_config_enabled(True)
        problems, _ = self.run_check()
        self.assertEqual(problems, [])

    def test_master_switch_off_fails(self):
        self._write_config_enabled(False)
        problems, _ = self.run_check()
        self.assertTrue(any("hooks 总开关已关闭" in p for p in problems))

    def test_entry_switch_off_fails(self):
        self._write_config_enabled(True, entry_enabled=False)
        problems, _ = self.run_check()
        self.assertTrue(any("enabled=false 的 hook 条目" in p for p in problems))


class TestIndexShapes(unittest.TestCase):
    """validate() 5b：围栏未闭合与路径含空格——regex 全绿但实际检索不到/打不开的形状。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self._tmp.name)
        for d in ("pitfalls", "tools", "workflow"):
            (self.kb / d).mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def _validate(self, index_text):
        (self.kb / "INDEX.md").write_text(index_text, encoding="utf-8")
        import kb_validate
        return kb_validate.validate(self.kb)

    def test_unclosed_fence_is_reported(self):
        problems = self._validate(
            "- [a](pitfalls/a.md) — x\n\n```markdown\n- [示例](x.md) — 围栏内不算\n"
        )
        self.assertTrue(any("未闭合的代码围栏" in p for p in problems))

    def test_closed_fence_is_clean(self):
        (self.kb / "pitfalls" / "a.md").write_text(
            "---\nname: a\ndescription: d\ntype: pitfall\nsource: s\ndate: 2026-10-04\n"
            "verified: 2026-10-04\ntopic: methodology\n---\n\n正文\n", encoding="utf-8")
        problems = self._validate(
            "- [a](pitfalls/a.md) — x\n\n```markdown\n- [示例](x.md) — 围栏内不算\n```\n"
        )
        self.assertEqual(problems, [])

    def test_path_with_space_is_reported(self):
        problems = self._validate("- [t](pitfalls/my file.md) — x\n")
        self.assertTrue(any("路径含空格" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
