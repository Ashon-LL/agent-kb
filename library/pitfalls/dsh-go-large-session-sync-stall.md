---
name: dsh-go-large-session-sync-stall
description: "dsh-go 手机端卡在「正在同步会话」多为客户端解析大快照所致，不是服务端故障；会话 <500 条消息时首帧全量下发，Web UI 开同一会话正常即可确诊"
type: pitfall
source: APIShow 多服务器管理（2026-11-11，qiniumei 上 dsh web + 手机 dsh-go）
date: 2026-11-11
verified: 2026-11-11
topic: toolchain
---

# dsh-go 卡「正在同步会话」先排除客户端，不要先动服务器

## 经验

- 症状：手机 dsh-go 能连上远端 `dsh web`，但一直停在「正在同步会话」。
- 服务端排除清单（全部只读，1 分钟能跑完）：

  ```bash
  pgrep -af 'dsh web'
  ss -tlnp | grep <port>                       # 进程在听
  curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:<port>/'   # 401/303 正常
  # WebSocket 握手应 101
  curl -s -o /dev/null -w '%{http_code}\n' --max-time 6 \
    -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
    -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==' \
    'http://127.0.0.1:<port>/api/remote.mux'
  ```

  会话文件本身也要验：`zstd -dc <session>.jsonl.zstd` 能完整解压、最后一条是 `turn/end`、事件类型配对（tool/call 与 tool/result 数量相等）。

- 根因（上游 issue #370 / #444 已定位到客户端源码）：
  - WebSocket 大帧在 **UI isolate 同步 JSON 解码**，大快照直接卡界面；
  - 重连时**整段已加载历史重新折叠**，不是只补增量；
  - 历史补拉逐页 `insertAll(0, …)`，分页数 p 时累计搬移 **O(p²)**。
- 客户端 `session/follow` 默认 `maxMessages: 500`：**会话消息数少于 500 时首帧一次性下发全部历史**。实测一条 759 事件 / 解压 2.86MB 的会话就会卡住；21MB 会话会直接闪退（#444）。
- 快速判据：**同一条会话在电脑浏览器打开 `dsh web` 正常** ⇒ 服务端无问题，瓶颈在手机端解析。
- 相关设计问题：#786（dsh-go 通过 SSH 会**另起一个 dsh**，不复用已在跑的实例）、#785（会话同步冲突/「正在别处使用」）。

## Why

- 服务端处理很快：同一条会话官方 Web UI 打开时，`session/follow` 首帧服务端生成只要 ~120ms（#444 实测）；把「同步卡住」当服务端故障去重启、清缓存、改配置，全是白费。
- 双实例会让情况更糟：一个 systemd 固定端口 + 客户端 `--port 0` 各占几百 MB，token/端口/日志都不同。

## How to apply

1. 先跑上面的服务端排除清单；全绿就不要再动服务器。
2. 手机端改用**新会话**或会话数少的工作区；大会话用电脑 Web UI 看。
3. 升级 dsh-go 到最新（2026-11-11 为 1.0.15）；注意 #370/#444 截至该版本仍 open，升级不保证解决。
4. 避免双实例：要么 systemd 守护固定端口，要么交给客户端拉起（`dsh-web.service` 保持 disabled），别两边都开。
5. 真要瘦身大会话属破坏性操作，先备份会话文件并征得站主同意。
