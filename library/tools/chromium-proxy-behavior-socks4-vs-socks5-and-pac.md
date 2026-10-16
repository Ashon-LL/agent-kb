---
name: chromium-proxy-behavior-socks4-vs-socks5-and-pac
description: Chromium 代理实测：系统代理 socks= 是 SOCKS4(本地解析读 hosts)、PAC 的 SOCKS 令牌=SOCKS4而 SOCKS5=远端发域名、file:// PAC 经 AutoConfigURL 不生效；用"探针 SOCKS 服务"看 ATYP 即可判定
type: tool
source: default 会话 2026-10-13（WARP 分隧道 + PAC 方案全过程）
date: 2026-10-13
verified: 2026-10-13
topic: browser
---

**经验**：Chromium 系（Edge、ZCode IAB、Electron 应用）走代理时"谁解析域名"是**由代理协议决定**的，2026-10-13 用"只记录 ATYP 的探针 SOCKS 服务"逐条实测：

| 配置来源 | 实际协议 | 谁解析域名 | 后果 |
|---|---|---|---|
| 系统代理 `ProxyServer=socks=host:port` | **SOCKS4** | **本地**（读 hosts） | 只发 IP，无法交给代理解析 |
| PAC 返回 `SOCKS host:port` | SOCKS4 | 本地（读 hosts） | 同上 |
| PAC 返回 `SOCKS5 host:port` | SOCKS5 | **远端**（发域名） | 实测日志全是 `DOMAIN: x:443` |
| 命令行 `--proxy-server=socks5://…` | SOCKS5 | 远端（发域名） | 同上 |

- **探针法**（比读源码/文档可靠）：本地起一个只记录 SOCKS greeting/ATYP/目标再拒绝的假代理，把待测浏览器指过去，日志里看得到是 `DOMAIN:`（远端）还是 `IP:`（本地）。注意 Windows 下把日志写绝对路径，别写 `/tmp`（会被解析成 `C:\tmp`）。
- **`AutoConfigURL` 指向 `file:///…pac` 不被采纳**（Chromium 仍直连）；PAC 要用 **HTTP 承载**（本机小 http.server 即可），而且**本机 HTTP PAC 的取用是可以被观测到的**——日志里能看到哪些进程来拉 PAC，等于免费拿到"管线生效"的证据。
- **SOCKS4 是破解 DNS 污染的关键**：它协议里没有域名字段，浏览器**必须**本地解析 ⇒ 会读 `hosts` ⇒ 把正确 IP 钉进 hosts 就能绕开被污染的解析。SOCKS5 反而做不到（远端解析落回代理侧、代理不读 hosts）。**前提：代理服务端要接受 SOCKS4**（有的是纯 SOCKS5，会拒绝）。

**Why**：在污染网络里想"只让指定域名走代理"，直觉是上 SOCKS5（更现代、支持域名），结果正好把解析权交给了解析同样被污染的一方——现象是"连上了但证书是别的站的"（实测 `chatgpt.com` 拿到 `*.facebook.com` 的证书），很容易误判成"这条隧道不通"，从而错误放弃方案。判断"隧道通不通"必须用**IP + SNI** 直连测试，把 DNS 变量摘出去。

**How to apply**：需要"逐域名分流"时：①PAC 用 `SOCKS`（v4）令牌而非 `SOCKS5`；②目标域名的正确 IP 从能通的状态下取样后钉进 hosts；③代理服务端确认接受 SOCKS4。需要"任意外网都走隧道"时别用 PAC（hosts 白名单的维护量不可控），改隧道级方案，见 [[warp-split-tunnel-china-direct]]。相关：[[browser-extension-forensics-profile-leveldb]]
