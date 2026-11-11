---
name: zcodepro-release-copy-format
description: 用户指定的 zcodepro 发版文案格式：简短有力，新增/修复/去掉三段（》》》），结尾覆盖安装/回退+发版状态(id/latest/hash/size/链接)
type: workflow
source: zcodepro v29.19 发版（2026-11-08 用户给出模板）
date: 2026-11-08
verified: 2026-11-08
topic: preference
---

**经验**：zcodepro 发版文案按用户固定格式：标题「zcodepro（zcode魔改版） vX.Y（基于官方 A / 果冻 B）」；
正文分「新增》》》 / 修复》》》 / 去掉》》》」三段、每段「· 」短句；结尾「覆盖安装不丢记录；包内自带上一版可一键回退。」
+「发版状态：Release 已建并设 latest：CNB Release vX.Y（id …）= latest；资产 …7z hash …/… B」+ release 链接。

**Why**：用户明确要求「以后这样给我发版文案」，简短有力，不要长篇。

**How to apply**：发版时照此格式产出；完整实例见 zcodepro/docs/release-copy-template.md。
另：用户澄清超大会话不需新开（可压缩），413 根因是请求体过大（工具输出/文件），收紧单条输出上限即可。
