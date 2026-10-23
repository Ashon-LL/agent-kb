---
name: interaction-latency-must-use-event-timing
description: 量交互延迟只能用 Event Timing API + 真实输入；rAF 回调计时漏掉光栅化/合成、dispatchEvent 造的 MouseEvent 不进合成器、无头 Chromium 软件光栅会把 840ms 漂成 34s；用户体感差时先质疑测法，别报漂亮的无用数字
type: pitfall
source: MH-Agent-Open（2026-09-24 用户三次追问「交互延迟怎么还是那么高」后复盘）
date: 2026-10-23
verified: 2026-09-24
topic: methodology, browser
---

**教训**：交互延迟的测法错了，会量出「84ms → 0.3ms」这种漂亮数字，而用户体感极差。

## 三处错法（同一次实测）

1. **量 JS 派发 → 下一个 rAF 回调**：真实代价在光栅化/合成，排在 rAF **之后** ⇒ 系统性漏掉大头。
2. **用 `new MouseEvent()` + dispatchEvent 造输入**：不与合成器同路，不进 Event Timing。
3. **无头 Chromium 默认 `--disable-gpu` 走软件光栅**：同码重测能把 840ms 漂成 34008ms（压测堆积假象）；加 `--gpu` 后 840ms 才与体感一致。

## 正确测法

- 用 **Event Timing API**（`PerformanceEventTiming`，click/pointerdown 等）拿真实输入到绘制完成的时长；
- 输入必须是真实交互（或 CDP 的 Input.dispatch* 走合成器），不要造 DOM 事件；
- 无头环境显式加 `--gpu`，并记录渲染路径（软件/硬件光栅）；
- 报告带 p50/p95 与对照（同一 DOM 关闭可疑特性），单点数字不算结论。

## How to apply

用户说「还是卡/还是慢」时，先复核测量方法三件事：测的是不是绘制完成、输入是不是真实、渲染是不是软件光栅。
测法不可信时，先修测法再谈优化。

关联 [[measurement-must-verify-control-group]]、[[clear-resume-anchors-before-benchmark]]、
[[verification-script-ua-can-fake-a-config-failure]]、[[no-assertion-without-measurement]]。
