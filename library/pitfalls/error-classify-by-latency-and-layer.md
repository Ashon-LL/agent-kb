---
name: error-classify-by-latency-and-layer
description: 「秒回」与「慢回」是不同故障，用耗时做分类维度（低成本高判力）；分类必须放在拿得到耗时上下文的层，别放在 SSE 消费层
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：错误分类加一个**耗时维度**：同一错误码/文案，**秒回**（几百 ms 内）与**慢回**
（几十秒）往往是不同故障（无权益 vs 上游卡顿 vs 链路阻塞）。同时，分类逻辑必须放在
**拿得到 attempt/耗时上下文**的编排层，不要放在 SSE 消费层——那一层只看得到帧。

**Why**：2026-10-26 参考工程审计：某实现把「无权益」分类放在 SSE 层，那里拿不到耗时 ⇒
分类永远不命中；正确位置是持有 attempt 上下文的适配器层。

**How to apply**：为每种错误同时记录「错误形态 + 耗时区间」，用耗时做初判；
分层时明确「谁持有上下文」，分类/归因放那一层，SSE 层只做协议透传。

相关：[[business-code-over-status-code]]、[[sse-stream-three-traps]]
