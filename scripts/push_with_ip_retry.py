# -*- coding: utf-8 -*-
"""GitHub 推送网络兜底：IP 存活秒级波动，测试与推送必须一体完成。

用法：python scripts/push_with_ip_retry.py <refspec...>
      例：python scripts/push_with_ip_retry.py "mirror main"
          python scripts/push_with_ip_retry.py "mirror main --force"

策略（按代价从低到高）：
  1. 先对候选 IP 做 TLS 预检，快速筛掉不可达的（省掉每个 21s 的 git 连接超时）
  2. 候选 IP 跨多个网段 —— 曾经 8 个候选全挤在 140.82.112.0/20，
     整段被干扰时全军覆没（实测：3 个 TLS 通但一推就断，5 个 TLS 都不通）
  3. 对预检通过的 IP，依次尝试「默认协议」与「protocol.version=1」两种形态
     （应用层被针对性干扰时，换协议版本可能绕开，v2 的 HTTP 特征更明显）
  4. 每个 IP 最多试 ROUNDS 轮，应对瞬时抖动

候选 IP **实时获取**（2026-10-04 用户要求，不再写死）：运行时向多个 DoH 端点
（1.1.1.1 / 8.8.8.8 / 223.5.5.5，走 443 不易被 DNS 污染）查询 github.com 的 A 记录
取并集作主力候选；全部 DoH 源失败才退回内置 FALLBACK 列表。

hosts 指向候选 IP 后**不再恢复**（2026-10-04 用户要求）：推送成功的 IP 就固化在
hosts 里，下次推送/访问直接走已验证的通路；全部失败的也停在最后尝试的 IP。
条目行精确匹配 github.com，不碰 raw.githubusercontent.com 等其他含 "github" 字样的条目。
"""
import json
import random
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.request

HOSTS = r"C:\Windows\System32\drivers\etc\hosts"
HOST = "github.com"
# 只匹配「IP github.com」形态的条目行，避免误删 raw.githubusercontent.com /
# api.github.com 等含 github 字样的其他条目
_GH_ENTRY = re.compile(r"^\s*\d{1,3}(?:\.\d{1,3}){3}\s+github\.com\s*(?:#.*)?$")

# DoH JSON API 端点（Cloudflare / Google / 阿里，走 443；多源并集防单点污染）
_DOH_ENDPOINTS = (
    "https://1.1.1.1/dns-query?name={host}&type=A",
    "https://8.8.8.8/resolve?name={host}&type=A",
    "https://223.5.5.5/resolve?name={host}&type=A",
)

# 兜底：仅当所有 DoH 源都拿不到结果时使用（DoH 源全被阻断的极端情形）
FALLBACK_CANDIDATES = [
    "140.82.112.3", "140.82.112.4", "140.82.113.4",
    "140.82.114.4", "140.82.116.4", "140.82.121.4",
    "20.205.243.166", "20.27.177.113", "4.237.22.38",
]

ROUNDS = 2                    # 每个 IP 的尝试轮数（瞬时抖动很常见）
PROTOCOL_VARIANTS = (         # 先默认，再退回 HTTP 特征更旧的一版
    [],
    ["-c", "protocol.version=1"],
)


def _fetch_dynamic_ips():
    """实时解析 github.com 的 A 记录：多 DoH 源并集，零第三方依赖。"""
    ips = []
    for tpl in _DOH_ENDPOINTS:
        url = tpl.format(host=HOST)
        try:
            req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            found = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            if found:
                print(f"  [doh]  {url.split('/')[2]}: {', '.join(found)}")
                ips.extend(found)
        except Exception as exc:
            print(f"  [doh]  {tpl.split('/')[2]}: 失败（{exc}）")
    return list(dict.fromkeys(ips))  # 去重保序


def _tls_ok(ip, timeout=3.0):
    """TCP + TLS 握手是否成功。只是粗筛：握手通不代表 git push 能通。"""
    try:
        s = socket.create_connection((ip, 443), timeout=timeout)
        ssl.create_default_context().wrap_socket(s, server_hostname=HOST).close()
        return True
    except Exception:
        return False


def _set_hosts(ip):
    lines = [l for l in open(HOSTS, encoding="utf-8").read().splitlines()
             if not _GH_ENTRY.match(l)]
    lines.append(f"{ip} {HOST}")
    open(HOSTS, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def _flushdns():
    subprocess.run(["ipconfig", "/flushdns"], capture_output=True)


def main():
    # 每个参数是一项推送（如 "mirror main" / "mirror main --force"），空格分词
    push_cmds = [arg.split() for arg in (sys.argv[1:] or ["origin"])]
    print("== 实时解析 github.com A 记录（DoH 多源）==")
    candidates = _fetch_dynamic_ips()
    if candidates:
        print(f"== 动态候选 {len(candidates)} 个；DoH 全挂时才用内置兜底 ==")
        candidates += [ip for ip in FALLBACK_CANDIDATES if ip not in candidates]
    else:
        print("== DoH 全部失败，退回内置兜底列表 ==")
        candidates = list(FALLBACK_CANDIDATES)
    random.shuffle(candidates)
    alive = []
    # 阶段一：TLS 预检，快速筛掉不可达的 IP
    print("== TLS 预检 ==")
    for ip in candidates:
        if _tls_ok(ip):
            alive.append(ip)
            print(f"  [ok]   {ip}")
        else:
            print(f"  [skip] {ip}  TLS 不通")
    if not alive:
        print("== 所有候选 IP 都无法完成 TLS 握手：整条链路疑似被阻断，直接放弃 ==")
        return 1

    # 阶段二：对可握手的 IP 实际推送；hosts 指向候选 IP 后不恢复——
    # 成功的 IP 固化下来，下次推送/访问直接走已验证通路（2026-10-04 用户要求）
    for idx, ip in enumerate(alive, 1):
        _set_hosts(ip)
        _flushdns()
        for rnd in range(1, ROUNDS + 1):
            all_ok = True
            for cmd in push_cmds:
                for extra in PROTOCOL_VARIANTS:
                    tag = "默认协议  " if not extra else "protocol.v1"
                    print(f"[try {idx}/{len(alive)} r{rnd} {tag}] {ip} -> git push {' '.join(cmd)}")
                    r = subprocess.run(["git"] + extra + ["push"] + cmd,
                                       capture_output=True, text=True,
                                       encoding="utf-8", errors="ignore",
                                       timeout=300)
                    out = (r.stdout + r.stderr).strip()
                    print("   " + out.replace("\n", "\n   ")[:300])
                    if r.returncode != 0:
                        all_ok = False
                        break
                if not all_ok:
                    break
            if all_ok:
                print(f"== 推送成功（{ip}，第 {rnd} 轮）；hosts 已固化为 {ip} ==")
                return 0
            time.sleep(1)
    print(f"== {len(alive)} 个可握手的 IP 全部失败；hosts 停在最后尝试的 {ip} ==")
    return 1


if __name__ == "__main__":
    sys.exit(main())
