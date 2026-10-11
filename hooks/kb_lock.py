#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb 库写入锁：多会话/多 Agent 同时写库时的互斥保护。

背景（2026-10-12）：本机同时有多个 Agent 会话在写 ~/.agents/kb（实测会话进行中
另一会话就在补条目、改 topic），而写入动作是「读 INDEX → 改 → 写回」的读-改-写
序列，两个进程交错会丢条目或丢索引行。此前无任何锁，靠运气。

设计：
  - **跨平台**：Windows 用 msvcrt.locking，POSIX 用 fcntl.flock；都是 OS 级文件锁，
    进程崩溃时内核自动释放（不会留死锁）。
  - **零依赖**：纯标准库。
  - **fail-open**：拿不到锁不阻塞会话（钩子绝不阻塞是全局原则），只在超时后告警放行，
    并把「可能发生并发写」写进 stderr——静默失败比丢数据更糟，所以这里不静默。
  - **可重入**：同一进程重复 acquire 计数，release 到 0 才真释放。

用法：
    from kb_lock import kb_write_lock
    with kb_write_lock():          # 进入即持锁，退出即释放
        ...读-改-写 INDEX.md...
"""
import os
import sys
import time
from pathlib import Path

try:
    import msvcrt  # Windows
except ImportError:
    msvcrt = None
try:
    import fcntl  # POSIX
except ImportError:
    fcntl = None

LOCK_NAME = ".kb-write.lock"
DEFAULT_TIMEOUT = 10.0   # 秒；钩子场景下超过它就没必要再等
_DEPTH = 0               # 进程内可重入计数
_FH = None


class _KbWriteLock:
    def __init__(self, kb=None, timeout=DEFAULT_TIMEOUT):
        from kb_core import resolve_kb_path  # 复用库路径解析，避免第二份实现
        self.kb = resolve_kb_path(kb)
        self.timeout = timeout
        self.path = self.kb / LOCK_NAME

    def _try_acquire(self, fh):
        if msvcrt is not None:
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        elif fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            return  # 无锁原语可用：退化为无锁（不阻塞）

    def _release(self, fh):
        try:
            if msvcrt is not None:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl is not None:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass

    def __enter__(self):
        global _DEPTH, _FH
        if _DEPTH > 0:            # 可重入
            _DEPTH += 1
            return self
        try:
            self.kb.mkdir(parents=True, exist_ok=True)
            fh = open(self.path, "a+")
        except Exception as exc:
            print(f"[agent-kb] 无法创建锁文件 {self.path}: {exc}（无锁继续）", file=sys.stderr)
            _DEPTH = 1
            _FH = None
            return self
        deadline = time.time() + self.timeout
        while True:
            try:
                self._try_acquire(fh)
                _FH, _DEPTH = fh, 1
                return self
            except OSError:
                if time.time() >= deadline:
                    # fail-open 但**不静默**：并发写有丢数据风险，必须让用户看见
                    print(
                        f"[agent-kb] 等锁超时（{self.timeout}s）——另一进程正在写库，"
                        f"本次在无锁状态继续，可能发生并发写冲突（{self.path}）",
                        file=sys.stderr,
                    )
                    _FH, _DEPTH = fh, 1
                    return self
                time.sleep(0.1)

    def __exit__(self, *exc):
        global _DEPTH, _FH
        _DEPTH -= 1
        if _DEPTH <= 0 and _FH is not None:
            self._release(_FH)
            try:
                _FH.close()
            except Exception:
                pass
            _FH = None
            _DEPTH = 0
        return False


def kb_write_lock(kb=None, timeout=DEFAULT_TIMEOUT):
    """上下文管理器：`with kb_write_lock(): ...`。"""
    return _KbWriteLock(kb, timeout)


if __name__ == "__main__":
    # 自测：拿锁后打印持有信息
    with kb_write_lock() as lk:
        print(f"[OK] 已持锁 {lk.path}（可重入测试）")
        with kb_write_lock():
            print("[OK] 重入正常")
    print("[OK] 已释放")
