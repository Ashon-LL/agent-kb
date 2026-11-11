---
name: vibe-video-skill-ecosystem-reuse
description: 做 B站「Vibe知识大赏」/vibe-video 风格知识短片先检索复用成熟开源技能生态，而非从零写工艺；纯代码逐帧（Canvas+seek(t)+Playwright+ffmpeg）零生图 API 成本批量生产；头部技能 HeyChengC/andyhuo520/liangdabiao/gnipbao 等
type: workflow
source: 10years-humanity EP05 立项前调研（2026-11-08，gh search repos 实测）
date: 2026-11-08
verified: 2026-11-08
topic: methodology
---

## 经验

接到「做一条 B 站知识大赏 / vibe-video 风格科普短片」类任务，**先检索复用现成技能生态，不要从零写工艺**。这类风格已被逆向成「规范 + 分镜模板 + 逐帧渲染管线 + 审查门禁」，纯代码逐帧（Canvas + `seek(t)` + Playwright + ffmpeg）可零生图 API 成本批量生产。

头部开源技能（GitHub，2026-11-08 实测星数）：
- **HeyChengC/vibe-knowledge-film**（1123★）：无旁白字幕片，核心是「先找形象再写文案」（references/visualization.md），逐镜截图改两轮。
- **andyhuo520/vibe-knowledge**（562★，44 套风格）：有旁白、每句带出处、代码逐帧。
- **liangdabiao/whiteboard-teacher-video**（514★）：手绘/MG，五套风格，本地 Chrome 零生图成本。
- **gnipbao/anatomy-explainer**：等轴测机械插画，**grill-me 审题**开头、豆包 TTS、浅/黑主题。
- **JustChenk/vibe-video-skills**：dark-field-explainer-video（暗场发光八条硬规则）+ handdrawn + series-video-planner。
- 其他：xiazhuo123456789/vibe-knowledge-video（逆向 8 条抖音爆款）、YT-smart/pixel-explainer-video（像素风）、HorizonGazer/PaperTalker-CLI（研究→视频→字幕→B站发布全程）。

## Why

这些风格的难点（给概念找外行认得的形象、分镜、逐帧确定性渲染、逐块审查门禁、暗场色带/发光规范）都已被踩平并写成规范。从零写会重复踩坑，且画风难以对齐爆款。复用技能＝拿走整套工艺与避坑清单。

## How to apply

① `gh search repos "知识大赏"` / `gh search repos vibe-video` 找头部仓库；② `git clone --depth 1` 后读 `SKILL.md` + `references/`（尤其 visualization/visual-grammar）；③ 复用其工艺，画面为当前文案现写、不搬模板零件；④ 编排层（选题→调研→制作→发布→触发互动）可固化成项目技能。10years-humanity 项目已固化 `vibe-video-pipeline` 技能并克隆 HeyChengC 到 `out/ref/vibe-skills/heychengc/`。相关：[[bilibili-upload-flow]]。