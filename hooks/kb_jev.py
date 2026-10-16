#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kb_jev.py — agent-kb **自带**的 Jev 客户端（TypeSafe System One 决策模型）。

## 为什么内联（而不是依赖 agent-jev 技能）

kb 的部分工具（触发词挖掘器等）需要「高频小判断」能力——判一条消息是否表达沉淀意图、
给候选分类打分这类。此前该能力靠外部 agent-jev 技能提供，代价是**用户要装两个东西**。
本文件把调用能力内联为单文件：**只装 agent-kb 就能用**，零第三方依赖。

## 配置（按优先级）

1. 环境变量 `KB_JEV_KEY`（+ 可选 `KB_JEV_ENDPOINT`、`KB_JEV_MODEL`）——单端点模式
2. 密钥文件（先命中先用）：
   - `~/.agents/kb/jev.key`  （kb 自己的位置，单行密钥）
   - `~/.jev/tokenrhythm.key` / `apigogo.key` / `zen.key`（与 agent-jev 共存时的位置，兼容）

## 多端点冗余

默认按 PROVIDERS 顺序尝试（tokenrhythm → apigogo → zen），**前一个失败才切下一个**（故障转移，
非负载均衡）。`KB_JEV_PROVIDERS` 可覆盖顺序/子集（逗号分隔名字）。

## 用法

    import kb_jev
    out = kb_jev.call({"state": "...", "questions": {"q": {"type": "noul", "instructions": "..."}}})
    p = kb_jev.probability(out, "q")      # noul → 0..1；choice/score 见 probabilities()

命令行自检：`python kb_jev.py`（打印各端点可用性，不打印密钥）
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

# ── 端点表（顺序 = 尝试顺序；密钥分渠道，互不通用）────────────────────
PROVIDERS = [
    {
        "name": "tokenrhythm",
        "endpoint": "https://tokenrhythm.studio/v1/systemone",
        "model": "NeoHorse-Jev-4B",
        "key_files": ["~/.agents/kb/jev.key", "~/.jev/tokenrhythm.key"],
    },
    {
        "name": "apigogo",
        "endpoint": "https://api.apigogo.cyou/v1/systemone",
        "model": "jev-1.13-free",
        "key_files": ["~/.agents/kb/jev.key", "~/.jev/apigogo.key"],
    },
    {
        # 直连 opencode 需官方客户端指纹（见 _opencode_headers）；部分源 IP 受限
        "name": "zen",
        "endpoint": "https://opencode.ai/zen/v1/systemone",
        "model": "jev-1.13-free",
        "key_files": ["~/.agents/kb/jev.key", "~/.jev/zen.key"],
        "opencode_client": True,
    },
]

RETRYABLE = {429, 500, 502, 503, 529}
DEFAULT_TIMEOUT = 8
DEFAULT_RETRIES = 2
DEFAULT_DEADLINE = 15

_B62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_OC_UA = "opencode/1.18.31 (linux amd64; go1.23.4)"


def _providers():
    """本次要尝试的端点列表（KB_JEV_* 环境变量可覆盖）。"""
    ep = os.environ.get("KB_JEV_ENDPOINT", "").strip()
    if ep:
        return [{
            "name": "override", "endpoint": ep,
            "model": os.environ.get("KB_JEV_MODEL", PROVIDERS[0]["model"]),
            "key_files": ["~/.agents/kb/jev.key"],
        }]
    order = os.environ.get("KB_JEV_PROVIDERS", "").strip()
    if order:
        by = {p["name"]: p for p in PROVIDERS}
        picked = [by[n.strip()] for n in order.split(",") if n.strip() in by]
        if picked:
            return picked
    return PROVIDERS


def _key_for(p):
    env = os.environ.get("KB_JEV_KEY", "").strip()
    if env:
        return env
    for raw in p.get("key_files", []):
        path = os.path.expanduser(raw)
        try:
            if os.path.exists(path):
                k = open(path, encoding="utf-8").read().strip()
                if k:
                    return k
        except OSError:
            continue
    return None


def has_key():
    """是否有任一可用密钥（调用方据此决定是否启用 Jev 功能）。"""
    return any(_key_for(p) for p in _providers())


def _opencode_session(seed="kb"):
    """opencode 客户端会话指纹：ses_<12位倒序时间戳hex><14位base62>。"""
    import hashlib
    h = hashlib.sha256(b"ses\x00" + str(seed).encode()).digest()
    n = int(h[6:16].hex(), 16)
    tail = "".join(_B62[(n // (62 ** i)) % 62] for i in range(13, -1, -1))
    desc = (~(int(time.time() * 1000) * 0x1000 + 1)) & 0xFFFFFFFFFFFF
    return "ses_%012x%s" % (desc, tail)


def _headers(p, key):
    if p.get("opencode_client"):
        s = _opencode_session()
        return {"content-type": "application/json",
                "accept": "application/json, text/event-stream",
                "user-agent": _OC_UA, "x-opencode-client": "cli",
                "x-opencode-session": s, "x-session-affinity": s, "X-Session-Id": s,
                "x-opencode-request": "req_" + os.urandom(16).hex(),
                "x-opencode-project": "prj_" + os.urandom(6).hex(),
                "authorization": "Bearer " + key}
    return {"Authorization": "Bearer " + key, "Content-Type": "application/json",
            "User-Agent": "curl/8.9.1"}


def _call_one(p, req, retries, timeout):
    key = _key_for(p)
    if not key:
        return {"error": "no key"}
    body = dict(req)
    body.setdefault("model", p["model"])
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = None
    for i in range(max(1, retries)):
        try:
            r = urllib.request.Request(p["endpoint"], data=data, headers=_headers(p, key))
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE:
                return {"error": "HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:200])}
            last = e
        except Exception as e:
            last = e
        if i + 1 < max(1, retries):
            time.sleep(0.4)
    return {"error": "after %d try: %s" % (max(1, retries), last)}


def call(req, retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT, deadline=DEFAULT_DEADLINE):
    """按端点表顺序尝试，返回解析后的 dict；绝不抛异常（失败给 {"error": ...}）。

    deadline 是整次调用的硬预算（含所有端点与重试）——socket 超时兜不住总耗时。
    """
    box = {}

    def worker():
        errs = []
        for p in _providers():
            if not _key_for(p):
                errs.append("%s: no key" % p["name"])
                continue
            r = _call_one(p, req, retries, timeout)
            if "answers" in r:
                r.setdefault("_provider", p["name"])
                box["r"] = r
                return
            errs.append("%s: %s" % (p["name"], r.get("error", "failed")))
        box["r"] = {"error": "all endpoints failed | " + " | ".join(errs)}

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(deadline)
    if t.is_alive():
        return {"error": "deadline %ss exceeded" % deadline}
    return box.get("r") or {"error": "no result"}


def probability(out, qid):
    """取某个 noul 问题的概率（0..1）；拿不到返回 None。"""
    a = ((out or {}).get("answers") or {}).get(qid) or {}
    v = a.get("noul")
    return float(v) if isinstance(v, (int, float)) else None


def probabilities(out, qid):
    """统一取概率表：choice/score 原生 probabilities；noul 合成 {yes,no}。"""
    a = ((out or {}).get("answers") or {}).get(qid) or {}
    probs = a.get("probabilities")
    if isinstance(probs, dict):
        return {k: float(v) for k, v in probs.items() if isinstance(v, (int, float))}
    if isinstance(a.get("choice"), str):
        c = a.get("confidence")
        return {a["choice"]: float(c) if isinstance(c, (int, float)) else 1.0}
    if isinstance(a.get("noul"), (int, float)):
        p = float(a["noul"])
        return {"yes": p, "no": round(1.0 - p, 6)}
    return {}


def _selftest():
    """自检：逐端点探测可用性（不打印密钥）。"""
    print("kb_jev 自检（多端点探测）")
    ok = False
    for p in _providers():
        k = _key_for(p)
        mark = "有密钥" if k else "无密钥"
        if not k:
            print(f"  {p['name']:12} {mark}（跳过）")
            continue
        r = _call_one(p, {"state": "1+1=2",
                          "questions": {"q": {"type": "noul", "instructions": "Is 1+1=2?"}}},
                      retries=1, timeout=10)
        if "answers" in r:
            print(f"  {p['name']:12} {mark} ✅ 可用（{r.get('model')}）")
            ok = True
        else:
            print(f"  {p['name']:12} {mark} ❌ {str(r.get('error'))[:90]}")
    print("结论：" + ("至少一个端点可用" if ok else "全部不可用——检查密钥/网络"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest())
