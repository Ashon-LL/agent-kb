---
name: warp-split-tunnel-china-direct
description: 【作用域=Windows + Cloudflare WARP 消费版】"外网走隧道、大陆直连"只能靠排除大陆网段实现；DNS 必须随隧道走，勿用 mode proxy
type: tool
source: default 会话 2026-10-13（为修 Codex 浏览器功能而配的分流）
date: 2026-10-13
verified: 2026-11-01
topic: windows, security
---

**经验**：Cloudflare WARP **消费版**的 split tunnel **只能"排除"**——`warp-cli tunnel ip` 没有 include 变体，`settings.json` 里也只有 `excluded_ips` / `excluded_hosts`（`tunnel dump` 提到的 include-only 属 Zero Trust 账号）。所以"外网走 WARP、大陆直连"只能**反过来表达**：保持 `mode warp+doh` **全量隧道**，再把**大陆 IPv4+IPv6 网段**写进排除列表。

- 落点：`C:\ProgramData\Cloudflare\settings.json` 的 `excluded_ips`，每条 `[cidr, "标签"]`。改前 `Stop-Service CloudflareWARP`、改后 `Start-Service`（改文件期间服务在跑会被覆盖）。
- **v4 和 v6 都要排**：只排 IPv4 时，国内双栈站点的 IPv6 仍走隧道（Windows 优先 IPv6），等于白做一半。
- 列表源：IPv4=`misakaio/chnroutes2`（约 3.9k 聚合路由）；IPv6=`gaoyifan/china-operator-ip` 的 `china6.txt`（约 3.5k）。实测共 7,408 条排除项 → 路由表 IPv4≈1.0 万 / IPv6≈1.55 万条。
- **自启是白送的**：`always_on=true` + `operation_mode=WarpWithDnsOverHttps` 存在 settings.json 里，重启后以该模式自动重连，不必另配启动项。
- 可复用脚本（自动刷新列表 + 备份 + 重启服务）：`~/proxy/apply-cn-excludes.py`（`--dry-run` / `--no-refresh`）。

- **"境外但应该直连"的目标必须手工补 IP 级排除**（2026-10-14 实测）：某服务域名解析到 `170.106.100.129`，而那台**正是用户自己的境外生产机**。它在大陆列表里必然不命中 ⇒ 走隧道 ⇒ **出口 IP 变成 Cloudflare 数据中心** ⇒ 被服务器白名单/风控/fail2ban 判为陌生来源而断连。现象是"一开隧道就连不上自己的服务"，**与国内外无关**。⛔ **此类目标要逐个手工补**（自己的服务器、有来源 IP 白名单的服务、要求固定出口 IP 的后台），地理网段分流**识别不了**它们。
- ⛔ **域名级排除在"DNS 走远端"的模式下可能不生效**：该域一直在 `excluded_hosts` 里却照样断连——因为解析由远端完成、域名排除发生在解析之后。要可靠就加 **IP 级排除**（路由层判定，一定生效）。
- ⛔ **排查时先分清“谁改的”**（2026-11-01 更正）：本次 `always_on=false` 是关闭 GUI 后的既有行为，而服务 `DEMAND_START` 是**用户手动改的**（长时间不用），不是 GUI 关闭导致。SCM 事件 7040 只能证明“启动类型被改”，不能证明“谁改的”。两者叠加的现场是：GUI 进程在跑、daemon 不起、`warp-cli status` 报 `os error 2`。修复：`sc config CloudflareWARP start= auto` + 把 `settings.json` 的 `always_on` 改回 `true` + `sc start`，再用 `warp-cli status` / `warp-cli settings` 复核 Connected 与 Always On。
- ⛔ **别用"关掉客户端"当收尾**：实测会把 `always_on` 置成 False（日志 `Disconnected(SettingsChanged{always_on:false})`），"重启后自动重连"随之失效，下次表现为"很难启动"。要恢复就改回 `true`。

- ⚠️ **应用 7k+ 排除列表后不会立刻 Connected**（2026-11-01 实测）：先出现 `Configuring split tunnel firewall rules`，随后可能 `Disconnected(Manual Disconnection)` 并重试，期间直连也会短暂中断；停服务恢复直连后再 `sc start`，约 30s 连上。排查先看 `warp-cli status` 的 Reason 与服务日志，别急着回退 `settings.json.bak`。

**Why**：①`mode proxy` 只开一个 SOCKS 口、**不代理 DNS**，域名会被本机被污染的 DNS 解析到错 IP（实测拿到过 `*.facebook.com` 的证书）——而"外网"恰恰全是被污染的域名，所以 proxy 模式在污染网络里必败；②不做排除时全量模式连国内也接管，就是用户抱怨的"妨碍访问国内东西"。**DNS 必须在隧道里解析**，这是全量模式唯一不可替代的理由。

**How to apply**：给这类网络配"智能分流"前，先确认工具的 split tunnel 是 include 还是 exclude 语义；只支持 exclude 就把大陆列表排进去（v4+v6）。代价要对用户直说：路由表变大；且 DNS 由 Cloudflare 侧解析会让部分国内站拿到"海外 CDN 优化"地址、那部分仍走隧道而**偏慢**（实测 baidu≈5s / taobao≈4s，多数站 2–3s），要优化可配 WARP 的 Local Domain Fallback 把国内后缀交回本地 DNS。⚠️ **判定国内站点可达性别用裸 Python TLS 客户端**（实测同一批站点它全超时、`curl.exe` 全 200，会把人带沟里）。相关：[[github-china-network-workarounds]]、[[chromium-proxy-behavior-socks4-vs-socks5-and-pac]]
