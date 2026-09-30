# -*- coding: utf-8 -*-
"""GitHub 推送网络兜底：IP 存活秒级波动，测试与推送必须一体完成。

用法：python scripts/push_with_ip_retry.py <refspec...>
对候选 IP 逐个「改 hosts → flushdns → 立即 git push」，成功即停。
hosts 只在推送进行中临时指向候选 IP，无论成败结束前都恢复推送前的原始内容
（进程被强杀时除外）；条目行精确匹配 github.com，不碰 raw.githubusercontent.com
等其他含 "github" 字样的条目。
"""
import random
import re
import socket
import ssl
import subprocess
import sys
import time

HOSTS = r"C:\Windows\System32\drivers\etc\hosts"
HOST = "github.com"
# 只匹配「IP github.com」形态的条目行，避免误删 raw.githubusercontent.com /
# api.github.com 等含 github 字样的其他条目
_GH_ENTRY = re.compile(r"^\s*\d{1,3}(?:\.\d{1,3}){3}\s+github\.com\s*(?:#.*)?$")
# 官方 git 段候选（api.github.com/meta 实测较稳的 140.82 主站段优先）
CANDIDATES = [
    "140.82.113.4", "140.82.112.3", "140.82.116.4", "140.82.121.4",
    "140.82.114.4", "140.82.112.4", "140.82.118.4", "140.82.117.4",
]


def _tls_ok(ip: str, timeout: float = 3.0) -> bool:
    try:
        s = socket.create_connection((ip, 443), timeout=timeout)
        ssl.create_default_context().wrap_socket(s, server_hostname=HOST).close()
        return True
    except Exception:
        return False


def _set_hosts(ip: str) -> None:
    lines = [l for l in open(HOSTS, encoding="utf-8").read().splitlines()
             if not _GH_ENTRY.match(l)]
    lines.append(f"{ip} {HOST}")
    open(HOSTS, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def _flushdns() -> None:
    subprocess.run(["ipconfig", "/flushdns"], capture_output=True)


def main() -> int:
    # 每个参数是一项推送（如 "origin master" / "origin feat/xxx"），空格分词
    push_cmds = [arg.split() for arg in (sys.argv[1:] or ["origin"])]
    random.shuffle(CANDIDATES)
    original = open(HOSTS, "rb").read()  # 推送前的原始 hosts 字节，结束前恢复
    try:
        tried = 0
        for ip in CANDIDATES:
            if not _tls_ok(ip):
                print(f"[skip] {ip} TLS 不通")
                continue
            tried += 1
            _set_hosts(ip)
            _flushdns()
            for cmd in push_cmds:
                print(f"[try {tried}] {ip} -> git push {' '.join(cmd)}")
                r = subprocess.run(["git", "push"] + cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="ignore", timeout=300)
                out = (r.stdout + r.stderr).strip()
                print("   " + out.replace("\n", "\n   ")[:300])
                if r.returncode != 0:
                    break
            else:
                print(f"== 推送成功（{ip}）==")
                return 0
            time.sleep(1)
        print(f"== 全部 {tried} 个候选 IP 失败 ==")
        return 1
    finally:
        open(HOSTS, "wb").write(original)  # 无论成败，hosts 恢复推送前原样
        _flushdns()


if __name__ == "__main__":
    sys.exit(main())
