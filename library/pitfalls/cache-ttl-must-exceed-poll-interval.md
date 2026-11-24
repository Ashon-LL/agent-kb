---
name: cache-ttl-must-exceed-poll-interval
description: 轮询 + 缓存组合里，缓存 TTL 必须明显长于轮询间隔；TTL ≤ 间隔等于每轮都真查，缓存形同虚设且把慢查询全暴露给主线程
type: pitfall
topic: methodology
source: zcode改造-v29.22-audit-2026-11-16（对照果冻同类问题）
date: 2026-11-16
verified: 2026-11-16
---

**经验**：任何「定时轮询 + 结果缓存」的组合，**缓存 TTL 必须明显大于轮询间隔**（经验上 ≥3×）。TTL ≤ 间隔时，每次轮询缓存都已过期 ⇒ 每轮都真的查一遍，缓存只多了一份内存、没有省掉任何成本。

**Why**：ZCode 桌面端的用量指标条：渲染层每 **3 s** 拉一次，主进程结果缓存 TTL 只有 **1 s** ⇒ 每 3 s 必真查；单次刷新 12 条 SQL 合计约 **162 ms**（1.1 GB 库，hist30 一条就 57 ms），主进程约 5 % 时间被占，多 pane/多窗口成倍。果冻版更极端：缓存 TTL 正好等于 3 s 轮询、单次查询 1.5 s ⇒ 主进程 **52 %** 时间被堵。两边病根完全一样：**缓存没有跨过轮询周期**。

**How to apply**：① 先算「轮询间隔 × 单次查询耗时」得到主线程占用率；② 把 TTL 设为轮询间隔的 3–6 倍（本例 3 s 轮询 → 12 s TTL，占用从 ~5.4 % 降到 ~1.4 %）；③ 数据变化靠事件/失效通知（invalidate）而不是靠缩短轮询；④ 面板不可见/窗口失焦时停止轮询；⑤ 如果单次查询仍 >100 ms，再考虑索引或把查询拆小——**先改节奏，再改查询**。

关联 [[no-assertion-without-measurement]]、[[tautological-assertion-and-self-scoped-recheck]]。
