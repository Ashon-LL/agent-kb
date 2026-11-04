---
name: gif-stego-scan-frames-before-format
description: GIF/动图隐写先逐帧扫码+帧间差分，再谈调色板/LZW 等格式层——单帧叠加物在格式层完全不可见
type: pitfall
topic: security
source: ctf-2026qwb-preheat
date: 2026-10-30
verified: 2026-10-30
---

**经验**：动图（GIF/APNG/视频）隐写题的第一动作是**逐帧扫码 + 帧与相邻帧差分**，不是调色板/LZW/元数据。一个 87MB、818 帧的 GIF，答案只在第 561 帧左上角贴了一个二维码；调色板、LZW 码流、时间轴全部干净，任何格式层分析都永远找不到它。

**Why**：我在这题上花了一个多小时做 palette ASCII 统计、LZW 码流审计、索引位平面、时间轴、未使用调色板项，全部"无命中"，直到做邻居中值差分才把帧 561 顶出来。技能里其实早有 `zbarimg`，但我没加载技能、自己造了一套缺项流程。两个错误叠加：**没走技能路由** + **缺最便宜的那一步**。

**How to apply**：
1. 新题第一动作 `Skill(solve-challenge)`，别凭记忆自己设计流程。
2. 动图类立刻跑：全帧 `zbarimg`（不许抽样）+ 帧间邻居中值差分找离群帧（阈值 >2% 面积）。
3. 15 分钟还没验证完一个假设、且没做过逐帧扫码 → 停下来先扫。
4. 知道题名就去搜：本题同源 writeup（NSSCTF「gif好像有点大」）一句话就点明"500 多帧有一帧是二维码"，早搜省一小时。
5. 格式层通道（palette LSB/未使用项/LZW/元数据/时间轴）只在 1-2 干净后才做；且要么做干净重编码对照实验判定"是否伪影"，要么别下结论。

关联 [[palette-ascii-hits-are-quantizer-artifacts]]。
