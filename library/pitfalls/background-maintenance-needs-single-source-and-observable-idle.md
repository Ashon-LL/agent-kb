---
name: background-maintenance-needs-single-source-and-observable-idle
description: 同一资源上的后台维护（VACUUM/压缩/清理）必须单源，且「空闲」判据要来自可观测的真实活动；多套各判各的空闲 + 判据读错字段恒为空，会在用户正在工作时抢独占锁
type: pitfall
source: zcodepro ADR-0059 / 2026-11-09 database is locked（%USERPROFILE%/Downloads/Project/zcodepro/adr/0059-vacuum-single-source-and-observable-idle.md）
date: 2026-11-10
verified: 2026-11-10
topic: database, sqlite, safety
---

**经验**：任何会拿**独占锁**的后台维护（SQLite VACUUM、整库重写、索引重建）必须满足三条：① 整个系统只有一个触发入口；② 「空闲」由可观测的真实活动判定（最近是否有写入/请求），且要用真实数据验证判据会随状态变化；③ 拿锁前用 `BEGIN IMMEDIATE` 之类探测，拿不到立即放弃，不让使用方排队等。

**Why**：实测一个 db 上同时存在三套 VACUUM（退役死代码、基线删任务触发、30min 存储维护），各判各的空闲；活跃那套的判据 `session_target.active_input_id is not null` 在真实表里 9 行全 NULL，**恒判空闲** → 用户回合进行中启动 VACUUM 抢写锁，写入方 `busy_timeout=5s` 等不住 → `database is locked` → turn 失败。与 [[rebase-same-name-map-value-type-may-swap]]（读错字段/对象导致判据恒 false）、[[guard-installed-by-the-mechanism-it-fixes]] 同族。

**How to apply**：① 加新维护任务前先搜已有同类入口，收口成单源再写；② 判据用「最近 N 分钟 message/part 等表有新写入」这类可测量信号，别用状态表里可能长期为空的目标字段；③ 写执行型测试灌 busy/idle 两种数据，断言判据真会变化；④ 拿锁失败即放弃并留日志，不设长 `busy_timeout` 让业务干等；⑤ 修判据，不要靠调阈值或关功能绕过。

关联 [[no-assertion-without-measurement]]、[[guard-criteria-anchored-to-spelling-always-escape]]。
