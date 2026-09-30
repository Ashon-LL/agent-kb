#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_validate 的平台无关自测（重点覆盖 Windows 路径分隔符回归）。

背景：Windows 上 Path.relative_to() 产出 `pitfalls\\x.md`，而 INDEX.md 里写 `pitfalls/x.md`；
若直接 str() 比较，全库索引行会被误报为 220 项不一致（Linux 天然一致，测不出）。
本自测用 PureWindowsPath / PurePosixPath 构造输入，无需 Windows 环境即可验收。

运行：python3 hooks/kb_validate_selftest.py
"""
import sys
import tempfile
import shutil
import unittest
from pathlib import PureWindowsPath, PurePosixPath, Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb_validate as kbv  # noqa: E402


def make_kb(tmp, entries: dict, index_paths):
    """造一个最小库：entries = {相对路径: 正文}，index_paths = INDEX 里登记的路径。"""
    kb = Path(tmp) / "library"
    for d in ("pitfalls", "tools", "workflow"):
        (kb / d).mkdir(parents=True, exist_ok=True)
    for rel, body in entries.items():
        p = kb / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    lines = ["# 全局经验库索引（kb）", ""]
    for i, ip in enumerate(index_paths):
        lines.append(f"- [条目{i}]({ip}) — 一句话")
    (kb / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return kb


def valid_entry(slug, typ="pitfall"):
    return (f"---\nname: {slug}\ndescription: d\ntype: {typ}\nsource: s\n"
            f"date: 2026-09-30\nverified: 2026-09-30\ntopic: methodology\n---\n\n**经验**：x\n")


class TestPathNormalization(unittest.TestCase):
    def test_windows_backslash_normalized(self):
        # 关键回归：Windows 风格输入必须归一为 / 形式
        self.assertEqual(kbv.disk_key(PureWindowsPath(r"pitfalls\x.md")), "pitfalls/x.md")
        self.assertEqual(kbv.disk_key(PureWindowsPath(r"a\b\c\y.md")), "a/b/c/y.md")

    def test_posix_unchanged(self):
        self.assertEqual(kbv.disk_key(PurePosixPath("pitfalls/x.md")), "pitfalls/x.md")

    def test_index_side_normalized(self):
        self.assertEqual(kbv.index_path_key(r"pitfalls\x.md"), "pitfalls/x.md")
        self.assertEqual(kbv.index_path_key("pitfalls/x.md"), "pitfalls/x.md")

    def test_old_str_behavior_would_mismatch(self):
        # 证明「旧写法」（直接 str）在 Windows 上必错 —— 这不是库脏，是分隔符问题
        old = str(PureWindowsPath("pitfalls/x.md"))
        self.assertNotEqual(old, "pitfalls/x.md")
        self.assertEqual(kbv.disk_key(PureWindowsPath("pitfalls/x.md")), "pitfalls/x.md")


class TestKeyStyleConsistency(unittest.TestCase):
    def test_collect_and_index_keys_same_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            kb = make_kb(tmp,
                         {"pitfalls/a.md": valid_entry("a")},
                         ["pitfalls/a.md"])
            disk = set(kbv.collect_entries(kb))
            idx = {kbv.index_path_key(p) for p in kbv.index_entry_paths(kb)}
            self.assertEqual(disk, idx)
            self.assertTrue(all("/" in p and "\\" not in p for p in disk))

    def test_windows_relative_value_normalizes_to_index_key(self):
        # 模拟 Windows：relative_to() 返回的是 WindowsPath 风格；用 PureWindowsPath 表示，
        # 断言其 disk_key 归一后与 INDEX 侧 key 完全一致（这正是修复点）
        with tempfile.TemporaryDirectory() as tmp:
            kb = make_kb(tmp, {"pitfalls/a.md": valid_entry("a")}, ["pitfalls/a.md"])
            win_rel = PureWindowsPath(*Path("pitfalls/a.md").parts)  # 即 Windows 上 relative_to 的形状
            self.assertEqual(kbv.disk_key(win_rel), "pitfalls/a.md")
            idx = {kbv.index_path_key(p) for p in kbv.index_entry_paths(kb)}
            self.assertIn(kbv.disk_key(win_rel), idx)


class TestReverseCaseDetectsRealProblems(unittest.TestCase):
    def test_missing_index_line_is_reported(self):
        """反向用例：磁盘多一条、INDEX 没登记 → 必须报「磁盘有条目但索引缺行」。"""
        with tempfile.TemporaryDirectory() as tmp:
            kb = make_kb(tmp,
                         {"pitfalls/a.md": valid_entry("a"),
                          "pitfalls/b.md": valid_entry("b")},
                         ["pitfalls/a.md"])  # 故意漏 b
            probs = kbv.validate(str(kb))
            self.assertTrue(any("磁盘有条目但索引缺行" in p and "b.md" in p for p in probs),
                            msg=f"未报出缺行：{probs}")

    def test_stale_index_line_is_reported(self):
        """反向用例：INDEX 有行、磁盘无文件 → 必须报「索引有行但磁盘无」。"""
        with tempfile.TemporaryDirectory() as tmp:
            kb = make_kb(tmp,
                         {"pitfalls/a.md": valid_entry("a")},
                         ["pitfalls/a.md", "pitfalls/ghost.md"])
            probs = kbv.validate(str(kb))
            self.assertTrue(any("索引有行但磁盘无" in p for p in probs), msg=str(probs))


class TestRealLibraryRegression(unittest.TestCase):
    def test_repo_library_passes(self):
        lib = Path(__file__).resolve().parent.parent / "library"
        if not (lib / "INDEX.md").exists():
            self.skipTest("仓库库不存在")
        self.assertEqual(kbv.validate(str(lib)), [], msg="真实库应 PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
