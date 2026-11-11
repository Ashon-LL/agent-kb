---
name: credential-write-never-cross-account
description: 绝不跨账号写凭据（用一份凭据填多个账号是结构性错误）；凭据写入失败 ≠ 登录失败（不可逆动作前先判关键产物是否已落地）
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: security
---

**经验**：两条铁律——① 任何「写凭据」的路径都必须确认**目标账号 == 凭据所属账号**，
绝不把 A 的凭据写进 B 的槽位；② 登录流程里「凭据已落盘」就是成功，**落盘后的记账/状态更新失败**
要报「登录成功但状态未更新」，不能报「登录失败」并删号。

**Why**：2026-10-26 参考工程审计两例真实破坏：refreshAll() 与 refreshAccountCredential() 都拿
current() 的结果无条件写回目标 ref，把**账号 A 的凭据铺满整个池**、抹掉 B 的真实凭据（口诀：
「IDE 能用而插件说没额度」先怀疑凭据被覆盖，而不是配额）；另一例把「登录成功后的记账失败」
抛成「登录失败」⇒ 落盘失败时直接删号，与事实相反。

**How to apply**：写凭据前打印/断言 (uid, credential.uid) 一致；
登录终态判定用「关键产物是否已落地」（凭据文件在 = 成了），不可逆动作（删号/覆盖）前必须过这一判。

相关：[[rotating-refresh-token-needs-single-writer]]、[[credential-expiry-authoritative-not-fabricated]]
