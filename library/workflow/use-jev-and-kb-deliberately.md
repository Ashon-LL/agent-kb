---
name: use-jev-and-kb-deliberately
description: Jev 用于分类初筛评分核查，KB 用于非平凡任务前检索及跨项目经验沉淀；介绍 DSH 插件时区分插件、技能、命令并核对实际状态
type: workflow
source: 用户明确偏好（2026-10-01）
date: 2026-10-01
verified: 2026-10-01
topic: methodology
---

**经验**：

- 非平凡任务开始前读 ~/.agents/kb/INDEX.md，命中后再读全文；任务闭环时只把跨项目可复用方法或教训沉淀至全局 KB，先查重并更新索引。
- 分类、路由、批量初筛、按明确标准评分排序、简单事实核查适合使用 agent-jev；不要用它生成文本或代码，也不要为琐碎的一次性判断增加调用。
- 介绍 DSH 时区分插件、技能、斜杠命令、bundle、preset 和 provider。全局可见插件数不等于当前启用数；本机配置片段不是完整清单，需明确各自范围和启用状态。

**Why**：用户要求经常使用 agent-jev 和 KB。此前曾把 skills 误称插件，又把本机 patch 中出现的插件说成完整清单；根因是没区分概念及清单范围。

**How to apply**：开始任务先判断是否符合 KB Recall 和 Jev 类型化判断条件；介绍本机插件前核实实际安装/bundle 清单，分开报告全局可见、当前 preset 启用、停用、未知。

关联 [[spec-priority-official-first]]。
