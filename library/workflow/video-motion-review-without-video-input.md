---
name: video-motion-review-without-video-input
description: 模型/Provider 不支持视频输入时，代码动画成片的动效验收：每幕按 0.6s 间隔抽帧拼条带（14 幕 244 帧）+ 1fps 全片接触表 + 成片逐幕抽帧；逐条看入场/连续运动/跳变/中途空帧/转场残影；汇报只声称看帧，不声称看视频
type: workflow
source: 10years-humanity EP06 v2（2026-11-09，用户要求逐帧检验）
date: 2026-11-10
verified: 2026-11-09
topic: verification
---

## 经验

Provider 不支持视频输入时（Read mp4 返回 `Media omitted ... does not support video input`），
不要退回「每幕只看 20/55/90% 三帧」——那会漏掉运动缺陷。按下面三层做：

1. **关键帧门禁**：`keyframes.js` 每幕 20/55/90% 共 42 帧，先看构图/文字/边界。
2. **逐幕运动条带**：每幕按 **0.6s** 间隔抽帧（12s 幕约 20 张），按 6 列拼条带并标 `scene + Δt`；
   本轮 14 幕共 244 帧 / 14 张条带。逐条 Read，检查：
   - 入场是否平滑（透明度/位移），首帧是否黑场；
   - 是否有连续运动（镜头漂移/光呼吸/田摆/轮转/粒子）；
   - 数字计数是否单调、有没有跳变；
   - 画面中段有没有「元素没出现」的空帧；
   - 幕尾/转场有没有残影或上一幕残留。
3. **成片复核**：成片按幕 60% 抽 14 帧 + 全片 1fps 接触表；与签收关键帧逐张比对；再跑
   `blackdetect` / `freezedetect` 与 `visual_metrics.py`。

汇报口径：**「看了 42 张关键帧 + 244 帧运动条带 + 14 张成片抽帧」**；不说「看了视频/看了运动」。

## Why

- v1 只看了 3 帧/幕就签收，边界写「只看了帧，没看运动」；用户看完直接判「太差劲，应该逐帧检验」。
- 稀疏关键帧会漏掉：剪影头肩缝、拨禾轮与割台脱节、切幕前的淡出残影、数字中途跳变、整段静止。
  0.6s 条带能把这些在 1 张图里摊开。
- 指标（mean/framediff/min2s）只能证明「有像素变化」，不能证明「观众看得懂」；条带是模型能做的最近似人眼监看。

## How to apply

- 先跑 `keyframes.js`；再用 `render.js --test "t1,t2,..."` 按 0.6s 时间表抽帧（`--test` 不触发签收门禁）。
- 用 PIL/ffmpeg 拼 6 列条带，每格标 `scene + Δt`；逐张 Read，别只看联系表。
- 成片后用 `grab.js <video> <每幕60%时间...>` + `visual_metrics.py --sheet` 复核。
- 报告里写清「哪些帧/条带看了、哪些没看」；Provider 支持视频时也应保留条带做转场抽查。
- 相关：[[video-motion-metrics-fps-calibration]]、[[dark-field-keyframes-thin-line-flow-false-empty]]、[[code-drawn-video-frame-review-checklist]]。
