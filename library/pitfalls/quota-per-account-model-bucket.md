---
name: quota-per-account-model-bucket
description: 配额按「账号×模型」分桶，而非只看汇总余额；汇总余额 >0 会把请求持续派给「该模型已尽」的账号（用户看到「不换号」）
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：多账号池的配额判据必须是**二维**的：账号 × 模型。
只看「账号汇总余额 > 0」不够——同一账号可能 A 模型还有额度、B 模型已尽，
汇总值 >0 会持续把 B 模型的请求派给这个账号，表现为「明明有别的号却一直不换」。

**Why**：汇总余额把不同模型的额度混成一个数，丢失了「哪个模型还能用」这个真正决定派单的信息；
用户侧症状是「这个模型一直失败但不换号」，而账号池看起来是健康的。

**How to apply**：池的选号函数签名带 model，配额查询按 (account, model) 维度缓存与判活；
账号级只用于「账号整体是否可用」（封禁/过期），模型级才决定能不能派。

相关：[[pool-credit-priority-keep-serving-and-billing-account-tied]]、[[observation-marker-vs-real-wall]]
