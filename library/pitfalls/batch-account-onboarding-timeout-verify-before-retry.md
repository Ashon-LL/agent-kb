---
name: batch-account-onboarding-timeout-verify-before-retry
description: 纳号/入池类 POST 客户端读超时 ≠ 失败——服务端常已完成登录入库；超时后必须只读核对池文件再决定重试，否则误判失败或重复纳号
type: pitfall
source: APIShow 戌线纳号 2026-10-10（Loomy 面板 add-pwd 客户端 60s 超时但服务端已成功）
date: 2026-10-10
verified: 2026-10-10
topic: api-gateway
---

**经验**：纳号/入池类写操作（面板 API、CLI 入库）客户端**读超时不等于失败**：服务端（登录上游 + 写池）可能已经完成，只是回包慢于客户端超时。超时后的正确动作是**只读核对**——读池文件/列表接口，看该账号在不在、session/令牌是否已写入——**以核对结果决定**是否重发，绝不盲目重试。

**Why**：盲目重试的代价：① 可能重复纳号或覆盖触发额外的上游登录；② 更常见的后果是**误判失败**，去排查一个根本没发生的故障（本次实例：5640 的 add-pwd 客户端 60s 超时，池内实测账号已在、session_len=32）。反向同理：写接口「回包成功」也不等于「已落盘」；纳号类操作一律以**落盘态**为准。

**How to apply**：任何「远程写 + 持久化」的纳号、开号、入池操作；客户端超时或连接中断时。核对手段：直接读池文件（如 `accounts.json`）或调只读列表接口，而不是重放写请求。相关 [[batch-account-onboarding-one-per-login]]。
