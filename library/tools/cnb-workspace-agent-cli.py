# -*- coding: utf-8 -*-
"""直连 CNB 云原生开发工作区里的 AI Agent（CodeBuddy）——发消息 / 读会话 / 保活。

背景：CNB OpenAPI **没有**「向工作区 Agent 发消息」的端点（199 个端点全查过，
`workspace/*` 只有 start/stop/delete/list/detail）。但 Agent 自己的 REST API
就跑在容器里（`codebuddy --serve` 监听容器内 8688），从外面 SSH 进去即可操作。

用法：
    python cbc.py reply "<文本>"      # 派活（Agent 正忙时也能投，不占用其 writer）
    python cbc.py history [条数]      # 读最近若干轮输入/输出
    python cbc.py sessions            # 列全部会话
    python cbc.py keepalive           # 发一次心跳（防工作区被回收）
    python cbc.py watch [秒]          # 持续盯：定期心跳 + 打印新发言
                                  # ⛔ 须在你自己能看见的窗口里跑；挂在后台/被会话结束杀掉就会哑。

环境变量：
    CNB_WS_SSH   工作区 SSH 地址（`cnb workspace get-workspace-detail` 的 remoteSsh）
                 不设则用下面 DEFAULT_SSH（会随工作区重建而变，用前最好更新）
    CNB_WS_BASE  容器内服务地址（默认 http://127.0.0.1:8688）

⛔ 必需请求头 `x-codebuddy-request: 1`，缺了全站 403（看起来像"没登录/无权限"，
   极具误导性——务必先带头再下结论说"没权限"）。

保活原理：官方 `vscode` 流水线的 `keepAliveTimeout` 默认 **600000 ms = 10 分钟**，
超时且无 HTTP/SSH 心跳即回收开发环境。保持 SSH 连接（或跑 `keepalive`）即可。
⛔ 别与 Job 级 `timeout`（默认 2h / 最大 12h / 无输出 10min）混淆——那是构建流水线。
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time

DEFAULT_SSH = "cnb-k6e-1k4027d29-001.15834225-75d9-4add-9fce-eb94a934c172-mm6@cnb.space"
BASE = os.environ.get("CNB_WS_BASE", "http://127.0.0.1:8688")
HDR = "x-codebuddy-request: 1"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=20",
            # 消掉 SSH 的 PQ 警告（每次都打到 stderr，会挤掉真正的输出）
            "-o", "LogLevel=ERROR"]


def _ssh(script: str, timeout: int = 120) -> str:
    """在远端跑 bash 片段并回传 stdout（脚本以 stdin 传，避免本机引号转义问题）。"""
    host = os.environ.get("CNB_WS_SSH", DEFAULT_SSH)
    p = subprocess.run(["ssh", *SSH_OPTS, host, "bash -s"], input=script,
                       capture_output=True, text=True, timeout=timeout)
    return (p.stdout or "") + (("\n[stderr] " + p.stderr.strip()) if p.stderr.strip() else "")


def _py_json(expr: str) -> str:
    """在远端解析 JSON 并输出紧凑文本（避免 GBK 终端显示问题）。"""
    return f"python3 -c {shlex.quote(expr)}"


def reply(text: str) -> str:
    """向当前活跃会话投递一条消息。"""
    if not text.strip():
        return "ERROR: empty text"
    script = f"""
set -uo pipefail
B={shlex.quote(BASE)}; H={shlex.quote(HDR)}
SID=$(curl -s --max-time 8 -H "$H" "$B/api/v1/sessions/live" | python3 -c 'import sys,json;d=json.load(sys.stdin) or {{}};print((d.get("data") or {{}}).get("sessionId") or "")')
[ -z "$SID" ] && {{ echo NO_LIVE_SESSION; exit 3; }}
PAYLOAD=$(python3 -c {shlex.quote('import json,sys;print(json.dumps({"text": sys.argv[1]}))')} {shlex.quote(text)})
echo "SID=$SID"
curl -s --max-time 25 -X POST -H "$H" -H 'content-type: application/json' \
     -d "$PAYLOAD" "$B/api/v1/sessions/$SID/reply" -w '\\nhttp=%{{http_code}}\\n'
"""
    return _ssh(script)


def history(limit: int = 6) -> str:
    """读最近若干轮对话（userInput / finalReply）。"""
    script = f"""
set -uo pipefail
B={shlex.quote(BASE)}; H={shlex.quote(HDR)}
SID=$(curl -s --max-time 8 -H "$H" "$B/api/v1/sessions/live" | python3 -c 'import sys,json;d=json.load(sys.stdin) or {{}};print((d.get("data") or {{}}).get("sessionId") or "")')
[ -z "$SID" ] && {{ echo NO_LIVE_SESSION; exit 3; }}
curl -s --max-time 20 -H "$H" "$B/api/v1/sessions/$SID/history?limit={int(limit)}" | python3 -c '
import sys, json
d = (json.load(sys.stdin) or {{}}).get("data") or {{}}
for i, r in enumerate(d.get("requests") or [], 1):
    ui = (r.get("userInput") or "").replace(chr(10), " ")[:200]
    fr = (r.get("finalReply") or "").replace(chr(10), " ")[:600]
    print(f"--- #{{i}} IN: {{ui}}")
    if fr:
        print(f"    OUT: {{fr}}")
'
"""
    return _ssh(script)


def sessions() -> str:
    script = f"""
curl -s --max-time 15 -H {shlex.quote(HDR)} {shlex.quote(BASE + '/api/v1/sessions')} | python3 -c '
import sys, json
for s in ((json.load(sys.stdin) or {{}}).get("data") or {{}}).get("sessions") or []:
    print(s.get("id"), "|", s.get("messageCount"), "|", (s.get("name") or "").replace(chr(10), " ")[:100])
'
"""
    return _ssh(script)


def keepalive() -> str:
    """一次短连接即算心跳（keepAliveTimeout 默认 10 分钟）。"""
    return _ssh("date -u +%FT%TZ\n", timeout=60)


def watch(interval: int = 240) -> None:
    """持续盯：定期心跳 + 只在有新发言时打印。Ctrl-C 退出。"""
    seen = 0
    print(f"watch: 每 {interval}s 心跳 + 拉一次历史（Ctrl-C 退出）", flush=True)
    try:
        while True:
            keepalive()
            out = history(4)
            blocks = [b for b in out.split("--- #") if b.strip()]
            if len(blocks) > seen:
                for b in blocks[seen:]:
                    print(f"--- #{b.rstrip()}", flush=True)
                seen = len(blocks)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nbye")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, rest = argv[1], argv[2:]
    if cmd == "reply":
        print(reply(" ".join(rest)))
    elif cmd == "history":
        print(history(int(rest[0]) if rest else 6))
    elif cmd == "sessions":
        print(sessions())
    elif cmd == "keepalive":
        print(keepalive())
    elif cmd == "watch":
        watch(int(rest[0]) if rest else 240)
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
