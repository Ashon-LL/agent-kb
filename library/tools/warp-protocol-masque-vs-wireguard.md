---
name: warp-protocol-masque-vs-wireguard
description: WARP/Cloudflare One 连不上（卡 Connecting/happy-eyeballs）先换隧道协议 MASQUE↔WireGuard；校园网等常挡 MASQUE(QUIC 443/8095)，WireGuard(UDP 2408) 可通
type: tool
source: 本机实测（zhishangqing/XYU-WIFI，2026-11-09）
date: 2026-11-09
verified: 2026-11-09
topic: windows, diagnosis
---

**经验**：WARP 状态卡 `Connecting / Performing happy eyeballs to 162.159.x:443|8095` 多为 **MASQUE 协议被当前网络 blocking**，不是客户端坏。

- 隧道协议仅两种：`MASQUE`（默认，HTTP/3/QUIC，UDP 443/8095，伪装 HTTPS 抗 DPI）与 `WireGuard`（传统，UDP 2408，轻量兼容好）。
- 修复：`warp-cli --accept-tos tunnel protocol set WireGuard` 再 `connect`，实测从卡死变 `Connected/healthy`。反向网络（挡 WireGuard 放行 MASQUE）则切回 MASQUE。
- 协议设置会持久化，换网络不用重设。
- 工作模式（warp/doh/warp+doh/dot/proxy）是 DNS/隧道开关，与隧道协议无关，别混淆。
- 隧道下 IPv6 可能不通；用户已关网卡 IPv6 时浏览器/curl 走 IPv4 正常。

**How to apply**：WARP 连不上先 `tunnel protocol set` 换协议重试，再考虑重装/重注册；相关 [[github-china-network-workarounds]]。
