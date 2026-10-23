# -*- coding: utf-8 -*-
"""kb_validate 的「时效状态」检查单元测试。

背景：2026-10-16 一条未实测的「apigogo/x 已删除」写进手册与 kb，10-19 仓库重建，
10-23 照旧记录派单失败。规则=外部对象的状态句必须带 ⏰/复核命令，技术用法不误报。

运行：python -m unittest tests.test_kb_validate_volatile -v
"""
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "hooks"))

import kb_validate  # noqa: E402


def notes(text):
    return kb_validate._volatile_notes({"pitfalls/x.md": text})


class VolatileNotesTest(unittest.TestCase):
    def test_external_state_without_marker_is_flagged(self):
        self.assertEqual(len(notes("入口仓 apigogo/x 已被删除，现行入口改到别处。")), 1)

    def test_marker_suppresses(self):
        text = ("> ⏰ 时效状态（2026-10-16，未复核）：fork 已删除\n"
                "> ⚠️ 用前必须实测：cnb repositories get-by-id --repo apigogo/x")
        self.assertEqual(notes(text), [])

    def test_recheck_word_suppresses(self):
        self.assertEqual(notes("该服务已下线；复核命令：curl -sI https://x"), [])

    def test_technical_db_usage_not_flagged(self):
        text = "DELETE FROM abilities WHERE channel_id IN (...)——残留行会让已删的 channel_id 留在候选集里。"
        self.assertEqual(notes(text), [])

    def test_generic_version_not_flagged(self):
        self.assertEqual(notes("个别 404 = 该版本已删除，跳过"), [])

    def test_state_before_object_also_flagged(self):
        self.assertEqual(len(notes("已删除的仓库不会再收到事件")), 1)

    def test_current_entry_phrase_flagged(self):
        self.assertEqual(len(notes("现行入口 = `@i.o/x(角色)`")), 1)

    def test_broad_regex_covers_technical_uses(self):
        for word in ("已删除", "已失效", "已重建", "现行入口"):
            self.assertIsNotNone(kb_validate._VOLATILE_BROAD_RE.search(word))


if __name__ == "__main__":
    unittest.main()
