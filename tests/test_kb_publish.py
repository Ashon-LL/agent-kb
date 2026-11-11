# -*- coding: utf-8 -*-
"""kb_publish 显式发布器测试：不联网、不碰真实仓库。"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "hooks"))

import kb_publish  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], text=True,
                          capture_output=True, check=True)


class TestHelpers(unittest.TestCase):
    def test_allowed_paths(self):
        self.assertTrue(kb_publish._allowed("library/pitfalls/x.md"))
        self.assertTrue(kb_publish._allowed("library/INDEX.md"))
        self.assertTrue(kb_publish._allowed("library/CHANGELOG.md"))
        self.assertFalse(kb_publish._allowed("README.md"))
        self.assertFalse(kb_publish._allowed("hooks/kb_core.py"))
        self.assertFalse(kb_publish._allowed("library/.kb-write.lock"))

    def test_sanitize_home_path(self):
        home = str(Path.home())
        text, changed = kb_publish.sanitize_text(f"source: {home}/x")
        self.assertGreater(changed, 0)
        self.assertNotIn(home, text)
        expected = "%USERPROFILE%" if os.name == "nt" else "$HOME"
        self.assertIn(expected, text)


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.live = self.root / "live"
        for p in (self.repo / "library" / "pitfalls",
                  self.repo / "library" / "tools",
                  self.repo / "library" / "workflow"):
            p.mkdir(parents=True)
        (self.repo / "library" / "INDEX.md").write_text("# INDEX\n", encoding="utf-8")
        (self.repo / "library" / "CHANGELOG.md").write_text("# CHANGELOG\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text("library/.kb-write.lock\n", encoding="utf-8")
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def test_from_live_commit_and_sanitize(self):
        (self.live / "pitfalls").mkdir(parents=True)
        home = str(Path.home())
        (self.live / "pitfalls" / "new.md").write_text(
            f"---\nname: new\ndescription: new\ntype: pitfall\nsource: {home}/x\n"
            "date: 2026-11-11\nverified: 2026-11-11\ntopic: test\n---\n\n经验：x\n",
            encoding="utf-8",
        )
        (self.live / "INDEX.md").write_text(
            "# INDEX\n- [new](pitfalls/new.md) — new\n", encoding="utf-8")
        rc = kb_publish.main([
            "--repo", str(self.repo), "--live", str(self.live),
            "--from-live", "--message", "test entry", "--skip-validate",
        ])
        self.assertEqual(rc, 0)
        text = (self.repo / "library" / "pitfalls" / "new.md").read_text(encoding="utf-8")
        self.assertNotIn(home, text)
        log = git(self.repo, "log", "--oneline", "-1").stdout
        self.assertIn("library: test entry", log)
        self.assertTrue((self.repo / "library" / "CHANGELOG.md").read_text(
            encoding="utf-8").count("同步运行时库新增 1 条") == 1)

    def test_reject_changes_outside_library(self):
        (self.repo / "notes.txt").write_text("x", encoding="utf-8")
        before = git(self.repo, "rev-parse", "HEAD").stdout
        rc = kb_publish.main(["--repo", str(self.repo), "--skip-validate"])
        self.assertEqual(rc, 2)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD").stdout, before)

    def test_dry_run_does_not_write(self):
        (self.live / "pitfalls").mkdir(parents=True)
        (self.live / "pitfalls" / "dry.md").write_text("x", encoding="utf-8")
        rc = kb_publish.main([
            "--repo", str(self.repo), "--live", str(self.live),
            "--from-live", "--dry-run",
        ])
        self.assertEqual(rc, 0)
        self.assertFalse((self.repo / "library" / "pitfalls" / "dry.md").exists())


if __name__ == "__main__":
    unittest.main()