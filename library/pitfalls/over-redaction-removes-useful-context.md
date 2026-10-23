---
name: over-redaction-removes-useful-context
description: 过度脱敏会把执行方需要的上下文删掉——第三方项目的公开地址、项目名、许可证默认可写，只剔除凭据与本机绝对路径；脱敏红线只管密钥/token/secret；拿不准就写进去并加边界说明，而不是默默省掉
type: pitfall
source: MH-Agent-Open（2026-10-06 写派单任务书漏掉对标项目地址，用户指出「怎么没有说地址」）
date: 2026-10-23
verified: 2026-10-06
topic: delivery, security
---

**教训**：脱敏和泄露一样是信息事故，只是方向相反——删过头会让执行方无从下手。

## 事故

写七份派单任务书时，把对标对象 ArHub 的 GitHub 地址省掉了（自认属「保守脱敏」）。
用户直接指出：「同类开源产品 ArHub 源码级 这个怎么没有说地址？」
补进总册时加了边界说明：分册自包含、地址仅供必要时参照、以本仓现状与分册判据为准。

## 边界（2026-09-19 已放宽）

- **必须剔除**：密钥、token、secret、连接串、本机绝对路径。
- **允许写**：第三方项目的公开地址、项目名、许可证、公开文档链接、站点名。
- **拿不准**：写进去 + 一句边界说明（为什么给、以什么为准），不要默默省掉。

## How to apply

- 派单/交接文档里，执行方可能需要溯源的信息（对标项目、上游仓库、许可证）默认给。
- 用户追问「怎么没写 X」时，先承认这是自己的取舍并说明依据，再补，不要辩称「没必要」。
- 脱敏检查清单只针对凭据与绝对路径，不要扩大成「凡是外部信息都删」。

关联 [[token-and-secrets-hygiene]]、[[credentials-never-in-memory-or-logs]]、
[[dispatch-requires-three-way-equality-and-artifact-hygiene]]、
[[user-list-to-plan-must-diff-each-item]]。
