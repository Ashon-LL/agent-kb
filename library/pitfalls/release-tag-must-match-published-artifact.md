---
name: release-tag-must-match-published-artifact
description: 允许同版本覆盖发布资产时，tag 会被留在初版提交、而线上资产/body/main 指向重制提交，按 tag checkout 复现不出线上产物；重制后必须把 tag 同步到与资产一致的忠实提交
type: pitfall
source: zcodepro 复盘 2026-11-04（%USERPROFILE%/Downloads/Project/zcode改造/reports/project-retrospective-2026-11-04.md §6.3）
date: 2026-11-10
verified: 2026-11-10
topic: git, delivery
---

**经验**：若发布体系允许「同一 tag/版本号覆盖资产」，就必须同时定义「重制后 tag 怎么处理」。规则：`tag` 所指 commit 的源码要与线上资产一致；重制发布后把 tag 移到含该修复的忠实提交并推送，release body、资产哈希、文档同步核对。

**Why**：实测 v29.17 初版发布后同日重制，tag 仍指初版 `f12010a`，重制在 `ede5539`，因此 tag / release body / 资产 / main 分处不同提交点；按 tag 复现不出用户实际下载的东西。v29.15 亦有三次同名覆盖、tag 停在更早时代。v29.20 又出现同类漂移（水印修复资产已覆盖、tag 落后 3 个提交），后经用户确认把 tag 移到忠实提交并 force 推送。

**How to apply**：① 发版时记录「tag commit ↔ 资产 sha256」对照；② 覆盖资产后立刻复核该对照，不一致就移 tag；③ 移动已发布 tag 属改写历史，需用户单独确认；④ 没有不可变 build id 时，至少保证 tag 与资产同源，别让「可复现」只剩口号。与 [[installer-completion-by-hash-not-mtime]]（用哈希判身份）、[[sync-latest-is-not-a-release]]（同步≠发布）配合。

关联 [[release-gate-requires-must-do-items-closed]]。
