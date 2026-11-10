# -*- coding: utf-8 -*-
"""kb_audit 只读审计测试。

只测离线逻辑：临时库；不改真实库。
运行：python -m unittest tests.test_kb_audit -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "hooks"))

import kb_audit  # noqa: E402

FM = (
    "---\nname: {name}\ndescription: {desc}\ntype: {typ}\nsource: 测试\n"
    "date: {date}\nverified: {verified}\ntopic: {topic}\n---\n\n{body}\n"
)


def _write(path, **kw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(FM.format(**kw), encoding="utf-8")


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self.tmp.name)
        _write(
            self.kb / "pitfalls" / "alpha.md",
            name="alpha", typ="pitfall", topic="api-gateway", date="2020-01-01",
            verified="2020-01-01", desc="清空配置",
            body="**经验**：全量 PUT 会清空配置。配置 清空 全量 PUT",
        )
        _write(
            self.kb / "pitfalls" / "beta.md",
            name="beta", typ="pitfall", topic="api-gateway", date="2026-11-10",
            verified="2026-11-10", desc="覆盖清空",
            body="**经验**：全量 PUT 覆盖会清空配置。配置 清空 全量 PUT",
        )
        _write(
            self.kb / "workflow" / "gamma.md",
            name="gamma", typ="workflow", topic="methodology", date="2026-11-10",
            verified="2026-11-10", desc="孤立条目",
            body="**经验**：没有链接的独立条目。",
        )
        _write(
            self.kb / "tools" / "delta.md",
            name="delta", typ="tool", topic="methodology", date="2026-11-10",
            verified="2026-11-10", desc="链到 alpha",
            body="**经验**：参见 [[alpha]]。",
        )
        (self.kb / "INDEX.md").write_text(
            "- [alpha](pitfalls/alpha.md) — 清空\n"
            "- [beta](pitfalls/beta.md) — 覆盖清空\n"
            "- [gamma](workflow/gamma.md) — 孤立\n"
            "- [delta](tools/delta.md) — 链\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _entries(self):
        return kb_audit._load_entries(self.kb) if hasattr(kb_audit, "_load_entries") else None

    def test_duplicate_pairs(self):
        entries = __import__("kb_search")._load_entries(self.kb)
        pairs = kb_audit.duplicate_pairs(entries, threshold=0.5)
        self.assertTrue(any(
            {p["a"], p["b"]} == {"pitfalls/alpha.md", "pitfalls/beta.md"}
            for p in pairs
        ))

    def test_orphans_and_inlinks(self):
        from kb_search import _load_entries
        entries = _load_entries(self.kb)
        orphans = {o["rel"] for o in kb_audit.orphan_entries(entries)}
        self.assertIn("workflow/gamma.md", orphans)
        self.assertNotIn("pitfalls/alpha.md", orphans)  # delta 链到 alpha

    def test_stale_entries(self):
        from kb_search import _load_entries
        entries = _load_entries(self.kb)
        stale = kb_audit.stale_entries(entries, stale_days=180)
        self.assertTrue(any(s["rel"] == "pitfalls/alpha.md" for s in stale))
        self.assertFalse(any(s["rel"] == "pitfalls/beta.md" for s in stale))

    def test_link_suggestions(self):
        from kb_search import _load_entries
        entries = _load_entries(self.kb)
        orphans = kb_audit.orphan_entries(entries)
        links = kb_audit.link_suggestions(entries, orphans, threshold=0.2)
        beta = next((x for x in links if x["rel"] == "pitfalls/beta.md"), None)
        self.assertIsNotNone(beta)
        self.assertTrue(any(s["rel"] == "pitfalls/alpha.md" for s in beta["suggestions"]))

    def test_render_and_cli(self):
        from kb_search import _load_entries
        entries = _load_entries(self.kb)
        pairs = kb_audit.duplicate_pairs(entries, 0.5)
        orphans = kb_audit.orphan_entries(entries)
        links = kb_audit.link_suggestions(entries, orphans)
        stale = kb_audit.stale_entries(entries)
        topics = kb_audit.topic_distribution(entries)
        text = kb_audit.render_markdown(self.kb, entries, pairs, orphans, links, stale, topics, {
            "generated": "2026-11-10 08:00", "threshold": 0.5, "stale_days": 180,
        })
        self.assertIn("同族重复候选", text)
        self.assertIn("入链建议", text)
        self.assertIn("零入链条目", text)
        self.assertIn("过期/待复核", text)
        self.assertIn("topic 分布", text)

        out = self.kb / "audit.md"
        jsonout = self.kb / "audit.json"
        rc = kb_audit.main(["--kb", str(self.kb), "--threshold", "0.5",
                            "--out", str(out), "--json", str(jsonout)])
        self.assertEqual(rc, 0)
        self.assertTrue(out.is_file())
        payload = json.loads(jsonout.read_text(encoding="utf-8"))
        self.assertEqual(payload["entries"], 4)
        self.assertGreaterEqual(len(payload["duplicates"]), 1)
        self.assertIn("links", payload)


if __name__ == "__main__":
    unittest.main()