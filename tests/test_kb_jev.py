# -*- coding: utf-8 -*-
"""kb_jev（kb 自带的 Jev 客户端）单元测试——只测不联网的逻辑。

网络路径由 `python kb_jev.py` 自检覆盖（会打印各端点可用性）。
运行：python -m unittest tests.test_kb_jev -v
"""
import os
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "hooks"))

import kb_jev  # noqa: E402


class TestProviders(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in
                       ("KB_JEV_KEY", "KB_JEV_ENDPOINT", "KB_JEV_MODEL", "KB_JEV_PROVIDERS")}
        for k in self._saved:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_default_order_main_first(self):
        names = [p["name"] for p in kb_jev._providers()]
        self.assertEqual(names[0], "tokenrhythm")   # 主用在最前
        self.assertIn("apigogo", names)
        self.assertIn("zen", names)

    def test_providers_env_overrides_subset(self):
        os.environ["KB_JEV_PROVIDERS"] = "apigogo"
        names = [p["name"] for p in kb_jev._providers()]
        self.assertEqual(names, ["apigogo"])

    def test_endpoint_env_makes_single_provider(self):
        os.environ["KB_JEV_ENDPOINT"] = "https://example.test/v1/systemone"
        provs = kb_jev._providers()
        self.assertEqual(len(provs), 1)
        self.assertEqual(provs[0]["endpoint"], "https://example.test/v1/systemone")

    def test_key_env_wins(self):
        os.environ["KB_JEV_KEY"] = "test-key-123"
        for p in kb_jev._providers():
            self.assertEqual(kb_jev._key_for(p), "test-key-123")
        self.assertTrue(kb_jev.has_key())

    def test_no_key_detected(self):
        # 不设环境变量且屏蔽文件查找（用不存在的路径）
        os.environ["KB_JEV_PROVIDERS"] = "zen"
        provs = kb_jev._providers()
        provs[0]["key_files"] = ["~/.agents/kb/definitely-not-exist.key"]
        self.assertFalse(kb_jev.has_key())


class TestParsing(unittest.TestCase):
    def test_probability_noul(self):
        out = {"answers": {"q": {"type": "noul", "noul": 0.87}}}
        self.assertAlmostEqual(kb_jev.probability(out, "q"), 0.87)
        self.assertIsNone(kb_jev.probability(out, "missing"))

    def test_probabilities_choice_and_noul(self):
        out = {"answers": {
            "c": {"type": "choice", "choice": "consult", "confidence": 0.9,
                  "probabilities": {"consult": 0.9, "spam": 0.1}},
            "n": {"type": "noul", "noul": 0.7},
        }}
        self.assertEqual(kb_jev.probabilities(out, "c")["consult"], 0.9)
        n = kb_jev.probabilities(out, "n")
        self.assertAlmostEqual(n["yes"], 0.7)
        self.assertAlmostEqual(n["no"], 0.3)

    def test_choice_without_probabilities_synthesised(self):
        out = {"answers": {"c": {"type": "choice", "choice": "x", "confidence": 0.8}}}
        self.assertEqual(kb_jev.probabilities(out, "c"), {"x": 0.8})

    def test_error_out_gives_empty(self):
        self.assertEqual(kb_jev.probabilities({"error": "x"}, "q"), {})
        self.assertIsNone(kb_jev.probability({"error": "x"}, "q"))

    def test_opencode_session_shape(self):
        import re
        s = kb_jev._opencode_session("t")
        self.assertTrue(re.match(r"^ses_[0-9a-f]{12}[0-9A-Za-z]{14}$", s), s)
        self.assertTrue(re.match(r"^[0-9a-f]{9}f[c-f][0-9a-f]$", s[4:16]), s)


if __name__ == "__main__":
    unittest.main()
