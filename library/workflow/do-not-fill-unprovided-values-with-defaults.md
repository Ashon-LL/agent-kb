---
name: do-not-fill-unprovided-values-with-defaults
description: 用户没给的值不要替用户填默认——未知就明确标注「未记录/未提供」，被问才给选项；把程序默认值当用户设置会误导（实测把 DSH 最大输出默认 128K 写成用户配置，被用户纠正）
type: workflow
topic: preference
source: default 会话 2026-11-08（dsh-go 配置：我把未提供的最大输出按默认 128K 填出，用户明确纠正「没有征求我的意见就瞎搞」）
date: 2026-11-08
verified: 2026-11-08
---

**经验**：给用户出配置/报告时，**只写有来源的值**（用户给的、上游文档/接口返回的、本机配置里读到的）。用户没提供的字段（如模型的最大输出、上下文、阈值），一律明确标注「未提供 / 未记录」，不要拿程序默认值去填，也不要替用户选一个。

**Why**：把「程序默认 128K」写成「用户配置的最大输出」是**伪造来源**——用户会以为这是自己设的或上游的，据此做决策就错了。默认值是程序行为，不是用户意图；两者混写后无法分辨。实测：给 dsh-go 写渠道配置时，我把没提供的最大输出按默认 128000 填出，用户直接指出「我没有让你搞最大输出默认 128K，这是不对的，你没有征求我的意见就瞎搞」。

**How to apply**：
- 出配置/汇总时，每个值标来源；无来源的写「未提供」，并说明「需你自己定」。
- 被问「该填多少」时，按 [[ask-with-options-early-never-at-end]] 给选项+代价，让用户拍板。
- 与 [[never-pad-reports-with-desired-state]] 同源：不要把「希望/默认」包装成「已定/事实」。

关联 [[never-pad-reports-with-desired-state]]、[[user-authority-overrides-default-discipline]]、[[model-window-from-upstream-catalog-not-guess]]。