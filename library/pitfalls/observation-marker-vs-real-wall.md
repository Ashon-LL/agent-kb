---
name: observation-marker-vs-real-wall
description: 观测写标记与真实撞墙写标记必须分道（不同键或不同表）；同键同值会互相擦除 → 清标记路径把强证据擦掉 → 死循环，每轮真烧一发
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：给账号/模型写「限流标记」时，区分两种来源：**真实撞墙**（真收到 429/限额错误）
与**观测推断**（余额折算、用量趋势推算）。两者必须**分道存储**（不同键，或同键不同值域并带来源字段）。
绝不能让观测逻辑去写同一个键。

**Why**：2026-10-26 参考工程审计：观测层与真实层共用同一个键、同一种「清标记」路径 ⇒
真实撞墙写下的强证据被观测层的清除逻辑擦掉 ⇒ 下一轮继续派给同一个已撞墙的账号 ⇒ 死循环，
**每一轮都真的烧掉一次上游额度**。

**How to apply**：标记结构带 source（observed / real）与 evidence；清除逻辑只清 source=observed；
任何「主动写标记」的新机制上线前，普查所有读/清该标记的旁路，确认不会被绕过或误清。

相关：[[quota-per-account-model-bucket]]、[[cooldown-category-action-table]]
