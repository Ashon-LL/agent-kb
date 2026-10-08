---
name: browser-only-success-check-credential-first
description: 同一 token 只有浏览器能通、curl/python/node/TLS 伪装全 401 时，先验证凭据是否失效/被轮换（改密码、会话吊销、cookie 轮换），别一头扎进 TLS 指纹/WAF 假设——实测一例真因是用户改了密码
type: pitfall
source: APIShow 商汤小浣熊(RaccoonWork) relay 调试（2026-10-07，误诊半天后由用户一句"我改了密码"破案）
date: 2026-10-07
verified: 2026-10-07
topic: methodology
---

# 「只有浏览器成功」先查凭据失效，再谈 TLS 指纹/WAF

## 经验

遇到「**同一个 token，浏览器 fetch 200，而 curl / python / node / 甚至 Chrome TLS 伪装全 401，本机与服务器都一样**」时，第一步不是研究 JA3/头族，而是**验证手里这份凭据与浏览器当前用的是不是同一份、还有没有效**：

1. 在浏览器页面里 `fetch(url, {credentials:"omit", headers:{Authorization:"Bearer "+tok}})`——**不带 cookie 只带 token**：若 200，说明 token 本身有效、与 cookie/TLS 无关；若 401，手里的 token 就是死的。
2. 对比指纹：把浏览器 `document.cookie` 里现取的 token 与自己之前存的做 `sha256` 前 12 位比对——**不一致就是被轮换/重发了**（Web 应用常在每次请求后 rotation）。
3. 重新取新鲜凭据立刻重放原请求。本例：新鲜 token 在服务器上用最朴素的 curl / python-urllib 直接 **200**——所谓"WAF 拦非浏览器 TLS"从头就不存在。

真实根因清单（本例全中）：用户**改了密码**⇒旧 access/refresh 被服务端吊销；页面 **cookie 轮换**⇒两次抓到的根本不是同一个 token。

## Why

「浏览器行、程序全不行」的表象与 TLS 指纹拦截完美吻合，且逐层排除头族/UA/HTTP2/impersonate 都**无法证伪**它——因为**对照组（token）本身已经失效**，所有实验都在拿死凭据重复测。凭据失效和客户端指纹拦截的症状在 401 上不可区分，但前者只需重取凭据一次请求即可证伪，成本远低于研究伪装方案。本例为此误诊半天、还去翻了两参照项目的 TLS 依赖栈。

## How to apply

任何「仅浏览器/官方客户端可用，第三方请求 401/403」的排障，按序做：①`credentials:"omit"` 页内裸 token 复测；②token 指纹比对（是否同一份）；③新鲜凭据重放；④以上全过仍 401 才升级到头族/TLS/IP 假设。改密码、登出、会话吊销类操作会让**已导出的所有副本**（含 refresh token）一起报废，多账号收割场景尤其要先核这份。

相关：[[leak-probe-false-positive-three-guards]]（下结论前先设对照与复现的同族纪律）、[[env-claims-must-be-reverified]]、[[measurement-must-verify-control-group]]
