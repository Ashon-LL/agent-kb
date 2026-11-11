---
name: cooldown-category-action-table
description: 冷却的「类别→动作」表是语义载体（分几类/每类换不换号/写不写标记/抛什么码/耗尽报什么）；认证类写冷却 = 一次网关抖动封死整池
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：上游错误处置必须落成一张**「类别 → 动作」表**，而不是一段 if-else 循环骨架。
表要逐格写清：分几类、每类**换不换号**、**写不写冷却标记**、抛什么码、全池耗尽时报什么。
其中最贵的一格是「认证类」：**认证类只换号、绝不写冷却**。

**Why**：2026-10-06 事故——上游网关对**全池**回 401（网关侧抖动，不是账号问题），
实现把 401 归到「账号故障」并给每个号写 24h 冷却 ⇒ **一个请求内 6 个号各被封 24h，整个 provider 死一天**。
移植/对齐一个源时，如果只照抄循环骨架而漏抄分支语义表，同类事故会原样复现。

**How to apply**：对齐/移植任何一源，先要那张表，逐格核对；改动错误分支后做**逐格回归**
（每类构造一个样本，断言换号/冷却/抛码三个动作都对）。新源接入时把表写进该源的纳号手册。

相关：[[api-gateway-deterministic-errors-not-retried]]、[[upstream-queue-error-must-be-429-not-hard-403]]、[[multikey-pool-is-multi-account-rotation-is-the-point]]
