---
name: store-owns-data-page-owns-cadence
description: 前端同一份数据只能有一个持有者（store 管 state 与写入口），页面只负责节拍（轮询周期）与副作用（通知）；两个组件各自 fetch 同一接口会漂移（徽标显示 3 个执行中、列表页 2 个）；通知类副作用要留在有历史状态的页面，别下放到 store
type: workflow
source: MH-Agent-Open（Workflows.vue 4s 轮询 + App.vue 侧栏徽标 30s 轮询收编 store，2026-10-05）
date: 2026-10-23
verified: 2026-10-05
topic: methodology
---

**经验**：前端同一份数据出现两个持有者，迟早漂移。切分原则是
**store 管数据，页面管节拍与副作用**。

## 事故形态

`Workflows.vue`（4s 轮询）与 `App.vue` 侧栏徽标（30s 轮询）**各自** `fetch /api/workflows`：
徽标显示 3 个执行中、列表页显示 2 个——两份独立副本，计数必然漂移。

收编到 store 时的真实冲突：`Workflows.vue` 的 `load()` 还要跑 `notifyStatusChanges()`，
依赖页面级 `prevStatusMap` 判断「某工作流迁移到 done/failed 就弹通知」。
若让两处都改 store 再各自读 `state.workflows` 判迁移，徽标那次（30s，没有自己的历史状态）会**误报「状态变了」**。

## 三条切分

| 谁拥有 | 是什么 | 为什么 |
|---|---|---|
| store | `state.workflows` / `state.error` 数据本身 | 唯一持有者，消除双份副本 |
| store | 写入口（局部删除/设置等 action） | 所有修改走同一处，便于追踪 |
| 页面 | 轮询频率、通知、动画等副作用 | 节拍与 UI 副作用是页面职责；通知需要页面级历史状态 |

## How to apply

- 发现两个组件 fetch 同一接口 ⇒ 先合并到 store，再谈优化。
- 合并时把「读数据」和「派生副作用」分开：副作用留在拥有历史状态的那一层。
- 页面只订阅 store 的节拍（谁多久拉一次可以不同），数据本身不再有副本。

关联 [[producer-consumer-status-mismatch-silently-noops]]、[[shared-config-multi-owner-merge-write]]、
[[same-config-key-different-semantics-per-step-type]]。
