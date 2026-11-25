# -*- coding: utf-8 -*-
"""kb_validate 密钥形状扫描单元测试。

运行：python -m unittest tests.test_kb_validate_secrets -v
"""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "hooks"))

import kb_validate  # noqa: E402


class TestSecretScan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self.tmp.name)
        (self.kb / "INDEX.md").write_text("", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def scan(self, text):
        return kb_validate.scan_secrets({"pitfalls/x.md": text}, self.kb)

    def test_detects_openai_key(self):
        hits = self.scan("key sk-AbCdEfGhIjKlMnOpQrStUvWxYz123456")
        self.assertTrue(any("openai-key" in h for h in hits))

    def test_detects_github_and_private_key(self):
        hits = self.scan("ghp_1234567890abcdefghijklmnopqrstuvwxyz\n"
                         "-----BEGIN PRIVATE KEY-----")
        self.assertTrue(any("github-token" in h for h in hits))
        self.assertTrue(any("private-key" in h for h in hits))

    def test_ignores_redacted_placeholder(self):
        hits = self.scan("key sk-REDACTEDREDACTEDREDACTED")
        self.assertEqual(hits, [])

    def test_clean_text_is_clean(self):
        hits = self.scan("普通经验：先查再改。")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()