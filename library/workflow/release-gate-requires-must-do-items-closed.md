---
name: release-gate-requires-must-do-items-closed
description: 发布门禁必须硬阻断「用户明确指定计入本版的必做项未关闭」：只记进待办/已知问题就发布，等于把本版漏项推给用户，随后只能同版本号重制、覆盖资产、补发说明
type: workflow
source: zcodepro 复盘 2026-11-04（%USERPROFILE%/Downloads/Project/zcode改造/reports/project-retrospective-2026-11-04.md §6.2）
date: 2026-11-10
verified: 2026-11-10
topic: delivery, change-discipline
---

**经验**：用户说「计入本版要修」的条目，发布前必须逐条核到**代码 + 产物 + 文档**三处都关闭；不能因为已写进待办清单就算处理。发布顺序里加一条显式闸门：列出本版必做项 → 逐条给出关闭证据 → 有任一项未关闭就停止发布。

**Why**：实测用户 10:03 指定了一项 P1 计入 v29.17，执行方只写进 `open-items` 且标题「暂不修」，发布时 README/RN 仍把它列为已知问题；用户质问后才于同日重制补修。随后又错误建议「升一个新版本」，被用户纠正「本来就该做到这一版里」。一个漏项连带引发：同版本重制、资产同名覆盖、tag 漂移、三轮文案纠错。

**How to apply**：① 建版本分支时把用户点名的必做项固定成清单；② 发布前一条命令/脚本逐项核对并输出「已关闭 / 未关闭 + 证据路径」；③ 未关闭就停，不用「下版再修」替代；④ 补做本版漏项**不新增版本号**，同名资产覆盖后同步 tag 与 release body（见 [[release-tag-must-match-published-artifact]]）；⑤ 文案按 [[zcodepro-release-copy-format]] 固定模板输出。发版后的清理另见 [[post-release-housekeeping-mandatory]]。

关联 [[minimal-change-and-no-scope-creep]]。
