#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_publish.py — 显式发布器：运行时库 → 仓库 → 校验 → 本地提交 →（可选）推送。

设计边界（2026-11-11 用户选定 A 方案）：
  - **默认不推送**；只有显式 `--push` 才 `git push`。
  - 只允许 `library/` 下的条目、INDEX、CHANGELOG 变更；其他改动一律拒绝。
  - 同步运行时库时，把本机绝对路径替换为 `%USERPROFILE%` / `$HOME`。
  - 提交前必须 `kb_validate [PASS]`（`--skip-validate` 仅供测试）。
  - 推送失败保留本地提交，不 force push；origin 必推，mirror 需 `--mirror`。

用法（仓库内）：
    python hooks/kb_publish.py --from-live --message "新增 1 条" --push
用法（运行时副本，需指定仓库）：
    python ~/.agents/kb/kb_publish.py --repo <agent-kb> --from-live --push
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kb_lock import kb_write_lock  # noqa: E402

ENTRY_DIRS = ("pitfalls", "tools", "workflow")
ALLOWED_FILES = {"library/INDEX.md", "library/CHANGELOG.md"}
IGNORE = {"library/.kb-write.lock"}


def _repo(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("AGENT_KB_REPO", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent
    if (here.parent / ".git").is_dir():
        return here.parent
    return None


def _git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=check,
    )


def _status(repo):
    p = _git(repo, "status", "--porcelain", "--untracked-files=all")
    out = []
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        code, path = line[:2], line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
            path = path[1:-1]
        out.append((code, path))
    return out


def _allowed(rel):
    rel = rel.replace("\\", "/")
    if rel in IGNORE:
        return False
    if rel in ALLOWED_FILES:
        return True
    return any(rel.startswith(f"library/{d}/") and rel.endswith(".md")
               for d in ENTRY_DIRS)


def _home_variants(home=None):
    home = Path(home or Path.home())
    if os.name == "nt":
        return [
            (str(home), "%USERPROFILE%"),
            (home.as_posix(), "%USERPROFILE%"),
            (f"/{home.drive[0].lower()}{home.as_posix()[2:]}", "$HOME"),
        ]
    return [(str(home), "$HOME")]


def sanitize_text(text, home=None):
    changed = 0
    for old, new in _home_variants(home):
        if old and old in text:
            text = text.replace(old, new)
            changed += 1
    return text, changed


def sanitize_file(path, home=None):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    new, changed = sanitize_text(text, home)
    if changed:
        path.write_text(new, encoding="utf-8")
    return changed


def _count_entries(library):
    total = 0
    for d in ENTRY_DIRS:
        path = library / d
        if path.is_dir():
            total += sum(1 for _ in path.glob("*.md"))
    return total


def _copy_live(repo, live):
    """把运行时库的新增/变更条目与 INDEX 同步到仓库；不删除仓库条目。"""
    library = repo / "library"
    copied = []
    before = _count_entries(library)
    for sub in ENTRY_DIRS:
        src_dir, dst_dir = live / sub, library / sub
        if not src_dir.is_dir():
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src in src_dir.glob("*.md"):
            dst = dst_dir / src.name
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copy2(src, dst)
                copied.append(f"library/{sub}/{src.name}")
    src_index = live / "INDEX.md"
    if src_index.is_file():
        dst_index = library / "INDEX.md"
        if not dst_index.exists() or dst_index.read_bytes() != src_index.read_bytes():
            shutil.copy2(src_index, dst_index)
            copied.append("library/INDEX.md")
    after = _count_entries(library)
    if after > before:
        with (library / "CHANGELOG.md").open("a", encoding="utf-8") as f:
            f.write(f"\n## {time.strftime('%Y-%m-%d')}\n"
                    f"- 同步运行时库新增 {after - before} 条（{after} 条）\n")
        copied.append("library/CHANGELOG.md")
    return copied


def _validate(repo, skip=False):
    if skip:
        print("[WARN] 跳过 kb_validate（仅测试用）")
        return True
    validator = repo / "hooks" / "kb_validate.py"
    if not validator.is_file():
        print(f"[FAIL] 找不到校验器：{validator}", file=sys.stderr)
        return False
    env = dict(os.environ)
    env["AGENT_KB_PATH"] = str(repo / "library")
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, str(validator)], cwd=str(repo), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    print(p.stdout[-2000:].strip())
    if p.stderr.strip():
        print(p.stderr[-1000:].strip(), file=sys.stderr)
    return p.returncode == 0 and "[PASS]" in p.stdout


def _stage_commit(repo, paths, message):
    if not paths:
        print("[OK] 没有需要发布的变更")
        return None
    _git(repo, "add", "--", *paths)
    if _git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        print("[OK] 变更已暂存但无差异")
        return None
    msg = message if message.startswith("library:") else "library: " + message
    _git(repo, "commit", "-m", msg)
    head = _git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    print(f"[OK] 已提交 {head} — {msg}")
    return head


def _push(repo, mirror=False):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    r = subprocess.run(["git", "-C", str(repo), "push", "origin", "main"],
                       env=env, text=True, encoding="utf-8", errors="replace",
                       capture_output=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[FAIL] origin 推送失败；本地提交已保留，未 force push", file=sys.stderr)
        return False
    if mirror:
        r = subprocess.run(["git", "-C", str(repo), "push", "mirror", "main"],
                           env=env, text=True, encoding="utf-8", errors="replace",
                           capture_output=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode != 0:
            print("[WARN] mirror 推送失败；origin 已成功", file=sys.stderr)
            return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="kb 显式发布（默认不推送）")
    ap.add_argument("--repo", default=None, help="agent-kb 仓库根；也可设 AGENT_KB_REPO")
    ap.add_argument("--live", default=str(Path.home() / ".agents" / "kb"), help="运行时库路径")
    ap.add_argument("--from-live", action="store_true", help="先把运行时库同步到仓库 library")
    ap.add_argument("--message", default="同步经验条目", help="提交信息（自动加 library: 前缀）")
    ap.add_argument("--push", action="store_true", help="提交后推送 origin main")
    ap.add_argument("--mirror", action="store_true", help="同时推送 mirror main")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不写/不提交/不推送")
    ap.add_argument("--skip-validate", action="store_true", help="仅测试：跳过 kb_validate")
    args = ap.parse_args(argv)

    repo = _repo(args.repo)
    if repo is None:
        print("[FAIL] 找不到 agent-kb 仓库；请用 --repo <path> 或设 AGENT_KB_REPO", file=sys.stderr)
        return 2
    library = repo / "library"
    if not (repo / ".git").is_dir() or not library.is_dir():
        print(f"[FAIL] 不是 agent-kb 仓库（缺 .git 或 library）：{repo}", file=sys.stderr)
        return 2
    live = Path(args.live).expanduser().resolve()

    with kb_write_lock(library):
        if args.dry_run:
            changed = _status(repo)
            changed = [(c, p) for c, p in changed if _allowed(p) and p not in IGNORE]
            print("[dry-run] 可发布变更：")
            for code, path in changed:
                print(f"  {code} {path}")
            if args.from_live:
                print(f"[dry-run] 会从 {live} 同步新增/变更条目与 INDEX")
            print("[dry-run] 未写入、未提交、未推送")
            return 0

        if args.from_live:
            if not live.is_dir():
                print(f"[FAIL] 运行时库不存在：{live}", file=sys.stderr)
                return 2
            copied = _copy_live(repo, live)
            if copied:
                print(f"[OK] 已同步 {len(copied)} 个文件：")
                for p in copied[:20]:
                    print(f"  {p}")
                if len(copied) > 20:
                    print(f"  ... 其余 {len(copied) - 20} 个")

        changed = _status(repo)
        bad = [(c, p) for c, p in changed if not _allowed(p) and p not in IGNORE]
        if bad:
            print("[FAIL] 仓库存在 library 之外的改动，拒绝发布：", file=sys.stderr)
            for c, p in bad:
                print(f"  {c} {p}", file=sys.stderr)
            return 2

        # 只脱敏允许发布的文件；INDEX 与条目都可能是本机路径来源。
        sanitized = 0
        for _c, path in changed:
            if _allowed(path) and path.endswith(".md"):
                sanitized += sanitize_file(repo / path)
        if sanitized:
            print(f"[OK] 已脱敏 {sanitized} 处本机绝对路径")

        changed = [(c, p) for c, p in _status(repo) if _allowed(p) and p not in IGNORE]
        if not changed:
            print("[OK] 没有需要发布的变更")
            return 0
        if not _validate(repo, args.skip_validate):
            print("[FAIL] kb_validate 未通过；未提交、未推送", file=sys.stderr)
            return 1

        head = _stage_commit(repo, [p for _c, p in changed], args.message)
        if head is None:
            return 0
        if not args.push:
            print("[OK] 仅本地提交；要推送请显式加 --push")
            return 0
        return 0 if _push(repo, args.mirror) else 2


if __name__ == "__main__":
    sys.exit(main())