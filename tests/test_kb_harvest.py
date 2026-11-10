# -*- coding: utf-8 -*-
"""kb_harvest 只读候选生成器测试。

只测离线逻辑：临时 SQLite + 临时工作区 + 临时库；不访问真实会话库，不写真实库。
运行：python -m unittest tests.test_kb_harvest -v
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "hooks"))

import kb_harvest  # noqa: E402


def _make_db(path, rows):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, "
        "time_created INTEGER, data TEXT)"
    )
    con.execute("CREATE TABLE part (message_id TEXT, data TEXT)")
    for mid, sid, ts, data, text in rows:
        con.execute(
            "INSERT INTO message VALUES (?,?,?,?)",
            (mid, sid, ts, json.dumps(data, ensure_ascii=False)),
        )
        con.execute(
            "INSERT INTO part VALUES (?,?)",
            (mid, json.dumps({"type": "text", "text": text}, ensure_ascii=False)),
        )
    con.commit()
    con.close()


class TestHarvest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kb = self.root / "kb"
        (self.kb / "pitfalls").mkdir(parents=True)
        (self.kb / "INDEX.md").write_text(
            "# INDEX\n\n- [部署指南](notes/deploy-guide.md) — 已收录\n",
            encoding="utf-8",
        )
        self.ws = self.root / "ws"
        (self.ws / "notes").mkdir(parents=True)
        (self.ws / "docs").mkdir()
        (self.ws / ".git").mkdir()
        (self.ws / "library").mkdir()
        (self.ws / "notes" / "deploy-guide.md").write_text(
            "# 部署指南\n\n步骤一。\n", encoding="utf-8"
        )
        (self.ws / "docs" / "lesson.md").write_text(
            "# 教训：不要重复踩坑\n\n先测再改。\n", encoding="utf-8"
        )
        (self.ws / "random.md").write_text("# 随机内容\n", encoding="utf-8")
        (self.ws / ".git" / "hidden.md").write_text("# 隐藏\n", encoding="utf-8")
        (self.ws / "library" / "x.md").write_text("# 库\n", encoding="utf-8")

        now = int(time.time() * 1000)
        self.db = self.root / "db.sqlite"
        sid = "sess_12345678-aaaa-bbbb-cccc-dddddddddddd"
        _make_db(self.db, [
            (1, sid, now, {"role": "user", "semantics": {"origin": "real_user"},
                           "time": {"created": now}},
             "记住这个坑：改脚本后必须同步副本"),
            (2, sid, now + 1, {"role": "user", "semantics": {"origin": "agent_runtime"},
                               "time": {"created": now + 1}},
             "内部注入，不是用户消息"),
            (3, "sess_subagent-xxxx", now + 2,
             {"role": "user", "semantics": {"origin": "real_user"},
              "time": {"created": now + 2}},
             "子代理任务书，应排除"),
            (4, sid, now + 3, {"role": "user", "semantics": {"origin": "real_user"},
                               "time": {"created": now + 3}},
             "今天天气很好"),
            (5, sid, now + 4, {"role": "user", "semantics": {"origin": "real_user"},
                               "time": {"created": now + 4}},
             "请更新这个配置文件"),
        ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_session_filters_and_dedup(self):
        cands, _since = kb_harvest.collect_session_candidates(days=1, db_path=self.db)
        self.assertEqual(len(cands), 1)
        self.assertIn("记住这个坑", cands[0]["text"])
        self.assertEqual(cands[0]["suggest_dir"], "pitfalls")

    def test_weak_signal_requires_flag(self):
        default, _ = kb_harvest.collect_session_candidates(days=1, db_path=self.db)
        weak, _ = kb_harvest.collect_session_candidates(
            days=1, db_path=self.db, include_weak=True
        )
        self.assertEqual(len(default), 1)
        self.assertEqual(len(weak), 2)
        self.assertTrue(any(c["signal"] == "weak" for c in weak))

    def test_workspace_filters_known_and_excluded_dirs(self):
        known = kb_harvest._index_keys(self.kb)
        cands = kb_harvest.collect_workspace_candidates(self.ws, known=known)
        paths = {c["path"] for c in cands}
        self.assertIn("docs/lesson.md", paths)
        self.assertNotIn("notes/deploy-guide.md", paths)  # 已在 INDEX
        self.assertNotIn("random.md", paths)
        self.assertNotIn(".git/hidden.md", paths)
        self.assertNotIn("library/x.md", paths)

    def test_render_markdown(self):
        cands, _ = kb_harvest.collect_session_candidates(days=1, db_path=self.db)
        ws = kb_harvest.collect_workspace_candidates(self.ws)
        text = kb_harvest.render_markdown(cands, ws, {
            "generated": "2026-11-10 08:00",
            "sources": "测试来源",
        })
        self.assertIn("会话候选", text)
        self.assertIn("工作区候选", text)
        self.assertIn("未写入经验库", text)
        self.assertIn("记住这个坑", text)
        self.assertIn("docs/lesson.md", text)

    def test_cli_writes_report_and_json(self):
        out = self.root / "report.md"
        jsonout = self.root / "report.json"
        with mock.patch.dict(os.environ, {"AGENT_KB_PATH": str(self.kb)}):
            rc = kb_harvest.main([
                "--days", "1", "--db", str(self.db),
                "--workspace", str(self.ws),
                "--out", str(out), "--json", str(jsonout),
            ])
        self.assertEqual(rc, 0)
        self.assertTrue(out.is_file())
        self.assertTrue(jsonout.is_file())
        payload = json.loads(jsonout.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["session"]), 1)
        self.assertTrue(any(c["path"] == "docs/lesson.md" for c in payload["workspace"]))
        # 只读：库内 INDEX 未被改写
        self.assertIn("部署指南", (self.kb / "INDEX.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()