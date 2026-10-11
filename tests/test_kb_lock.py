# -*- coding: utf-8 -*-
"""kb_lock（跨平台写入锁）单元测试。运行：python -m unittest tests.test_kb_lock -v"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "hooks"))


class TestKbLock(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self._tmp.name)
        os.environ["AGENT_KB_PATH"] = str(self.kb)

    def tearDown(self):
        os.environ.pop("AGENT_KB_PATH", None)
        self._tmp.cleanup()

    def test_acquire_and_release_creates_lockfile(self):
        import kb_lock
        with kb_lock.kb_write_lock():
            self.assertTrue((self.kb / kb_lock.LOCK_NAME).exists())

    def test_reentrant(self):
        import kb_lock
        with kb_lock.kb_write_lock():
            with kb_lock.kb_write_lock():   # 同进程重入不应死锁
                pass
        # 退出全部后深度归零
        self.assertEqual(kb_lock._DEPTH, 0)

    def test_cross_process_mutual_exclusion(self):
        """真互斥：A 持锁期间 B 必须等待。"""
        holder = (
            "import sys,time,os; sys.path.insert(0, r'%s')\n"
            "os.environ['AGENT_KB_PATH']=r'%s'\n"
            "from kb_lock import kb_write_lock\n"
            "lk=kb_write_lock(); lk.__enter__(); print('A',flush=True); time.sleep(2); lk.__exit__()\n"
            % (_REPO / "hooks", self.kb)
        )
        waiter = (
            "import sys,time,os; sys.path.insert(0, r'%s')\n"
            "os.environ['AGENT_KB_PATH']=r'%s'\n"
            "from kb_lock import kb_write_lock\n"
            "t=time.time(); lk=kb_write_lock(timeout=10); lk.__enter__()\n"
            "print(f'{time.time()-t:.1f}')\n"
            % (_REPO / "hooks", self.kb)
        )
        pa = subprocess.Popen([sys.executable, "-c", holder],
                              stdout=subprocess.PIPE, text=True)
        time.sleep(0.4)
        pb = subprocess.run([sys.executable, "-c", waiter],
                            capture_output=True, text=True)
        pa.stdout.readline()
        pa.wait()
        waited = float(pb.stdout.strip().splitlines()[-1])
        self.assertGreater(waited, 1.0, f"B 未等待 A（{waited}s）——锁未互斥")

    def test_second_acquire_in_same_process_is_reentrant_not_blocking(self):
        """同进程二次进入不应超时告警（可重入）——用 capfd 不便，改判深度与耗时不阻塞。"""
        import kb_lock
        t = time.time()
        with kb_lock.kb_write_lock(timeout=0.3):
            with kb_lock.kb_write_lock(timeout=0.3):
                pass
        self.assertLess(time.time() - t, 0.3, "重入不应走等待/超时路径")


if __name__ == "__main__":
    unittest.main()
