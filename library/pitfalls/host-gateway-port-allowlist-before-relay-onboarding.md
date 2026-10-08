---
name: host-gateway-port-allowlist-before-relay-onboarding
description: 宿主进程绑 docker 网桥 IP（如 172.18.0.1）供容器网关调用时，新端口必须先进 iptables 放行白名单并写进开机重放脚本，否则"直连 200、经网关 dial tcp i/o timeout"——白名单外的包被静默 DROP
type: pitfall
source: APIShow 接入 Loomy(17890)/小浣熊(17910) relay 时 New API 容器全超时（2026-10-07；apishow-adapter-firewall 只放行白名单端口）
date: 2026-10-07
verified: 2026-10-07
topic: container
---

# 新增宿主网关端口：先放行白名单，再写进开机重放，最后才接容器网关

## 经验

部署模式为「容器网关（New API 等）→ 宿主网桥 IP（如 `172.18.0.1:<port>`）→ 宿主进程 relay」时，**新端口必须先进 iptables 放行链**。此类部署常有一条白名单链（如 APIShow 的 `APISHOW_ADAPTERS`）：**链内列出的端口 ACCEPT，其余来自该网桥网段的包一律被 DROP**——没有显式 REJECT 日志，表现为 `dial tcp 172.18.0.1:<port>: i/o timeout`，而**在宿主上直连同一端口却 200**（宿主自身流量走 INPUT 不经该链），极具迷惑性。

两步修法（缺一不可）：
1. 立即生效：`iptables -A <链> -s <网桥网段> -p tcp --dport <port> -m comment --comment "<链>:<port>" -j ACCEPT`（必要时同规则加到 INPUT）。
2. **开机重放**：把 `ensure_input_rule <port>` 写进维护该链的**开机脚本/unit**（iptables 规则不持久，重启即丢——"重启也要能开"必须在脚本层固化），`systemctl enable` 该 unit 并重放一次验证幂等。

## Why

症状（直连通、经容器网关超时）会把排查引向 relay 本身、网关配置或 DNS，每层看起来都正常；真凶是中间层的静默 DROP。而"当场 iptables 加一条"只活到下次重启——重启后服务起不来或再次超时，属于同一坑的二次发作。

## How to apply

凡新增「绑宿主网桥 IP 供容器调用的服务」，接网关**之前**：①查 `iptables-save | grep <port>` 与维护链的脚本；②加放行并固化进开机脚本；③从**容器内**实测一次连通（宿主直连 200 不算数）。反向同理：容器网关报 i/o timeout 而宿主直连正常时，先查中间防火墙链再怀疑服务本身。

相关：[[browser-only-success-check-credential-first]]（同族"表象相似、真凶在别处"的排障纪律）
