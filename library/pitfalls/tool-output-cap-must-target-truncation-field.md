---
name: tool-output-cap-must-target-truncation-field
description: 收紧「工具输出上限」必须改在真正执行截断的字段上——改模型可见的元数据等于没改
type: pitfall
topic: methodology
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：要给工具输出设上限时，先确认「哪个字段真正决定模型看到多少字节」。把上限写进「随工具描述透传给模型的元数据」字段，对截断行为零效果，但构建期只断言字符串计数，全绿。

**Why**：在 ZCode CLI（官方 3.18.2）里，`metadata.maxOutputBytes`（Bash 官方 1e7 / Write·Edit 1e6）只是进入 provider tool spec、告诉模型「这个工具最多吐多少」，真正截断模型可见输出的是 `resultBudget.{maxInlineBytes,maxModelBytes}`（官方实测 Bash 30 KB、Write·Edit 100 KB，另有工具 10/20 KB）。我们把 `maxOutputBytes` 换成动态上限函数后，模型可见输出**一点没变**，而门禁只断言 `maxOutputBytes:__zsmToolCapBytes()` 出现 3 次 ⇒ 假绿。

**How to apply**：① 改上限前先在产物里找「截断入口」（通常是 `min(maxModelBytes,maxInlineBytes)` 之后的截断调用），把上限夹在那里；② 夹取语义用「只收紧不放大」`min(官方值, 我方上限)`，避免把官方更小的预算放大；③ 验收测试必须能证明判据会变（灌基线值断言真/假两态），而不是断言字符串存在；④ 配置缺失/损坏时的回退值也要有行为级断言。

关联 [[guard-must-cover-the-changed-layer]]、[[business-code-over-status-code]]、[[minified-alias-must-resolve-at-build-time]]。
