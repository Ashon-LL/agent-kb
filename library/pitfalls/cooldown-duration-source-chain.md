---
name: cooldown-duration-source-chain
description: 冷却时长取值链：响应头（Retry-After）→ 报文里的人类可读时长（英文句子）→ 兜底常量；「报文没有机器可读时间 ≠ 报文里没有时间」
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：向上游要的冷却时长按**三级链**取：① 响应头（Retry-After / X-RateLimit-Reset）；
② 报文里**人类可读**的时长（retry after 19h39m、请 30 分钟后再试）；③ 兜底常量。
二级最容易被漏：很多网关只在 body 文本里给时间，解析器只认头就会静默用兜底值（可能是 600s，
而真实要求是 19h39m），结果要么过早重试被打脸、要么白等。

**Why**：2026-10-26 参考工程审计记录：Cline 的限流是 19h39m，只藏在英文句子里；
「报文里没有机器可读时间」不等于「报文里没有时间」。用错量级会让限流惩罚被自己延长或缩短。

**How to apply**：写冷却解析时把三级都实现并各留一条单测样本（纯头 / 纯正文句子 / 都没有）；
正文解析覆盖常见格式（19h39m、30 minutes、请稍后再试 无具体值时走兜底并记一条日志）。

相关：[[api-gateway-deterministic-errors-not-retried]]、[[cooldown-category-action-table]]
