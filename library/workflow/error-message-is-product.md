---
name: error-message-is-product
description: 错误文案是产品：纯文本、<150 字符、识别出语义就不复述原文、不说结构上不可能有用的话（末端别把上游报文直出）
type: workflow
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：给用户的错误文案按产品设计：**纯文本**（别带上游 HTML/JSON）、**<150 字符**、
**识别出语义后就不要复述原文**、**不说结构上不可能有用的话**。末端网关不要把上游报文直接透出。

**Why**：2026-10-26 参考工程审计：直出上游报文会让用户拿到「看起来像账号问题」的误导信息
（实际是限额/风控/参数错），把排障引向错误方向；长报文与 HTML 也会毁掉客户端的展示。

**How to apply**：错误映射表里为每类错误写一句人话（含「该做什么」）；
透传上游 msg 只在「语义未识别」的兜底分支，且截断长度。

相关：[[business-code-over-status-code]]、[[cooldown-category-action-table]]
