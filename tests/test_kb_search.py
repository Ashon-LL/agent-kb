# -*- coding: utf-8 -*-
"""kb_search（检索器/查重）单元测试。

运行：python -m unittest tests.test_kb_search -v
Windows 与 CI 容器均可跑（tempfile + Path，无 POSIX 假设）。
"""
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "hooks"))

import kb_search  # noqa: E402

FM = (
    "---\nname: {name}\ndescription: {desc}\ntype: {typ}\nsource: 测试\n"
    "date: 2026-10-04\nverified: 2026-10-04\ntopic: {topic}\n---\n\n{body}\n"
)


def make_kb(tmp: Path):
    (tmp / "pitfalls").mkdir()
    (tmp / "tools").mkdir()
    (tmp / "workflow").mkdir()
    (tmp / "pitfalls" / "console-window-storm.md").write_text(FM.format(
        name="console-window-storm", typ="pitfall", topic="windows",
        desc="后台进程弹黑窗风暴的修法",
        body="**经验**：用 NO_WINDOW。后台任务被卡死时的黑窗会反复弹出。\n"), encoding="utf-8")
    (tmp / "pitfalls" / "full-put-wipes.md").write_text(FM.format(
        name="full-put-wipes", typ="pitfall", topic="api-gateway, security",
        desc="读-改-写全量 PUT 回传会清空配置",
        body="**经验**：GET 脱敏字段原样回传即清空，改用专用端点。\n"), encoding="utf-8")
    (tmp / "workflow" / "dual-scan.md").write_text(FM.format(
        name="dual-scan", typ="workflow", topic="methodology",
        desc="线上与文档双扫描",
        body="**经验**：先扫线上再扫文档。\n"), encoding="utf-8")
    (tmp / "INDEX.md").write_text(
        "- [黑窗风暴](pitfalls/console-window-storm.md) — 后台弹黑窗用 NO_WINDOW\n"
        "- [全量 PUT 清空](pitfalls/full-put-wipes.md) — 读改写覆盖配置\n"
        "- [双扫描](workflow/dual-scan.md) — 线上与文档双扫\n", encoding="utf-8")


class KbSearchCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self._tmp.name)
        make_kb(self.kb)

    def tearDown(self):
        self._tmp.cleanup()


class TestSearch(KbSearchCase):
    def test_symptom_word_hits_body_not_index_hook(self):
        # 「卡死」只出现在正文——症状词检索必须能穿透到正文层（缺陷分析的核心场景）
        results = kb_search.cmd_search(self.kb, ["卡死"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "pitfalls/console-window-storm.md")

    def test_index_hook_outranks_body(self):
        # 钩子命中的条目应排在正文命中之前
        results = kb_search.cmd_search(self.kb, ["清空"])
        self.assertEqual(results[0][1], "pitfalls/full-put-wipes.md")

    def test_topic_filter(self):
        results = kb_search.cmd_search(self.kb, ["黑窗"], only_topics={"windows"})
        self.assertEqual(len(results), 1)
        results = kb_search.cmd_search(self.kb, ["黑窗"], only_topics={"git"})
        self.assertEqual(results, [])

    def test_dir_filter(self):
        results = kb_search.cmd_search(self.kb, ["双扫"], only_dir="workflow")
        self.assertEqual(len(results), 1)
        results = kb_search.cmd_search(self.kb, ["双扫"], only_dir="pitfalls")
        self.assertEqual(results, [])

    def test_soft_and_downweights_missing_keyword(self):
        # 两个词只命中一个词的条目仍在结果里（软 AND），但两个词全命中的排前
        results = kb_search.cmd_search(self.kb, ["黑窗", "NO_WINDOW"])
        self.assertEqual(results[0][1], "pitfalls/console-window-storm.md")
        self.assertEqual(len(results), 1)


class TestSimilar(KbSearchCase):
    def test_same_family_ranks_first(self):
        # 措辞不同但共享事故名词的同族条目应浮上来（人肉查重漏掉的那类）
        results = kb_search.cmd_similar(
            self.kb, "配置 option 写操作六步铁律——全量 PUT 覆盖清空配置")
        self.assertTrue(results)
        self.assertEqual(results[0][1], "pitfalls/full-put-wipes.md")

    def test_no_overlap_returns_empty(self):
        self.assertEqual(kb_search.cmd_similar(self.kb, "quantum flux capacitor"), [])

    def test_tokens_cjk_bigram(self):
        toks = kb_search._tokens("记住这个坑")
        self.assertIn("记住", toks)
        self.assertIn("这个", toks)
        toks2 = kb_search._tokens("PUT config")
        self.assertIn("put", toks2)
        self.assertIn("config", toks2)


if __name__ == "__main__":
    unittest.main()
