---
name: dark-field-keyframes-thin-line-flow-false-empty
description: 【作用域=dark-field-explainer-video skill】keyframes.js 的 0.6% 非底色阈值 + 2px 采样 3×3 投票会把细线流场幕滤成假空白 ERROR；在 spec 范围内提粒子密度/线宽解决，签收分支硬拦 ERROR 绕不过
type: pitfall
source: 10years-humanity EP04 vibe-video 重做
date: 2026-11-08
verified: 2026-11-08
topic: verification
---

## 经验

暗场发光图文视频（dark-field-explainer-video / Opus5.5 风）的情绪粒子幕，按 style-spec 默认参数
（1000 粒、线宽 1.25、描边 alpha 0.30）渲染时，keyframes.js 机械体检会报 ERROR「画面几乎全空
（非底色仅 0.5%）」——**画面本身是对的，是门禁假阳性**。

解法：在 spec 允许范围内提密度——粒子 1000→1300（上限 1500）、线宽 1.25→1.5（上限 1.6）、
alpha 0.30→0.34。重抽帧到 WARN（≥0.6%）即可，逐张目检确认仍是发丝不是网。

同管线两个附带坑：
- `render.js --review-dir` 默认 `./keyframes` 相对 **CWD**，工程在子目录时必须显式传
  `--review-dir <工程>/keyframes`，否则拒渲「没有签收记录」。
- `encode.js` 的 libx264 分支只吃 `--crf`，**第 4 参码率对 libx264 无效**（只对 libopenh264/libsvtav1 生效）；
  要落实暗场 8M 码率建议需直接调 ffmpeg `-b:v 8M`。

## Why

体检算法：四边估底色 → 亮度差 >34/255 记内容 → **2px 采样 + 3×3 邻域 ≥4 票**才算墨迹。
1.25px 细线在 2px 采样下多数是孤立点，被投票滤掉；只有中心密集平行线区少量计票 → 0.5% < 0.6% ERROR 线。
签收分支 `if (hard.length) die(...)` 硬拦 ERROR，目检确认没问题也签不了收，必须让指标过线。

## How to apply

做暗场风视频遇到流场幕 ERROR「几乎全空」时：先 Read 帧确认画面真有粒子（不是渲染 bug），
再按上面参数提密度重抽，不要改门禁脚本迁就。若 chart/文字幕报全空则是真 bug——优先查
**HTML id 撞车**（多幕单文件工程里 `getElementById` 取第一个匹配，新幕 div 透明度恒 0，
2026-11-08 EP04 幕8 与幕1柱容器同名 chart2 实测）。