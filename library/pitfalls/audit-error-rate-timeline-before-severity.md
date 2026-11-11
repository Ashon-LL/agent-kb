---
name: audit-error-rate-timeline-before-severity
description: 审计失败率/错误日志必须先定时间线（last_ok/last_err+按天分布）再定级：单日错误潮≠持续故障，无流量≠不可用
type: pitfall
source: apishow（2026-11-05 生产运行面审计）
date: 2026-11-05
verified: 2026-11-05
topic: diagnosis
---

**经验**：对 logs/错误表按 model×channel 聚合出 ok/err 后，定级前必查三件事：①`MAX(created_at)` 的 last_ok 与 last_err；②按天分布（错误是否集中单日）；③此后有无流量。错误潮集中在单日且末次状态为成功=历史事件（上游限额重置/容器重启后已恢复），降级为观测项；末次连续失败+零成功+单源供给才判「实质不可用」，且仍标注「现状需受控验证」（无流量期间上游可能已恢复）。持续项的判据=错误每天发生且审计当时仍在出现。

**Why**：APIShow 2026-11-05 审计实测：7 天 49,936 条错误中 99% 是 11-02 单日 kimi-k3.1-pro 客户端重试风暴（上游 11-03 05:50 重置后恢复）；CodeArts 404/Trae 502/Qoder 排队全是 10-29 历史波、此后无流量；只有商汤 429 是持续项（每日 7–87 条、审计当时仍在发生）。若只看 7 天聚合失败率（ch176 69.7%、ch181 76.9%、ch182 84.6%）会把三个已平息的历史事件误判成 P0/P1 持续故障，误导处置优先级。

**How to apply**：任何基于日志聚合的故障定级/审计/告警分析。聚合查询同批带上 `MAX(created_at) FILTER type` 与按天 GROUP BY；报告里每条发现标注「持续/历史/待验证」。关联 [[same-error-across-batch-is-one-incident]]、[[quota-exhausted-vs-banned-distinguish]]。
