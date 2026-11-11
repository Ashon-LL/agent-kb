---
name: business-code-over-status-code
description: 业务码优先于状态码；状态码可能是某个源的风控专属语义（文档写 400 现场收 410），归因必须同时看 body
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：错误归因**以报文里的业务码为准**，HTTP 状态码只当「状态类」边界。
同一状态码在不同源可能是完全不同的语义（例如某源把风控拦截定义成 400，现场却收到 410）。

**Why**：2026-10-26 参考工程审计：只按状态码分支的实现会把「风控专属状态码」当普通 4xx，
既不放行也不换号，用户侧表现为「没报错但一直失败」。

**How to apply**：每个源登记一份「状态码/业务码 → 语义 → 动作」对照；
新源接入时先构造几个已知错误（风控、限额、参数错）实测状态码与 body，再写分支。

相关：[[error-classify-by-latency-and-layer]]、[[cooldown-category-action-table]]
