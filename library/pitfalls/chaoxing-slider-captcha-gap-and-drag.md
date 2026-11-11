---
name: chaoxing-slider-captcha-gap-and-drag
description: 超星考试入口的滑块拼图验证：用灰度线性回归从背景图定缺口偏移，再用"读拼图块 left 闭环修正"拖动——块位置落后手柄约 8px，开环必失败
type: pitfall
topic: browser
source: chaoxing-automation
date: 2026-11-11
verified: 2026-11-11
---

**经验**：超星（Chaoxing）考试入口 `examnotes` 页勾选协议、点「进入考试」后会弹**滑块验证**
（`#captcha` 内嵌在顶层文档，**不是 iframe**，别去翻 iframe）。它是 `captcha-b.chaoxing.com/slide/` 的
「向右拖动滑块填充拼图」：320×160 背景图 + 56×160 的 RGBA 拼图条。

**核心两招**

1. **缺口位置用线性回归算，不要截图靠眼睛**：缺口 = 拼图块轮廓 + 60% 白色半透明覆盖，
   所以正确偏移处满足 `big ≈ a·piece + b`（实测 `big=0.396*piece+103`，a 就是 1-alpha）。
   对每个候选 x 取拼图条 alpha>200 的掩码像素做 Pearson 相关，峰值即缺口（实测 0.71 vs 次优 0.48）。
   仅用「亮度/局部方差」阈值会被照片纹理带偏（狗毛、猫毛背景都试过，噪声很大）。
   ```python
   # gap.py 摘要：mask=alpha>200; for off in range(0,320-56+1): corr(big[y0:y1,off:off+56][mask], piece[mask])
   ```
2. **拖动必须闭环**：拼图块 `.cx_imgBtn` 的 `left` **不等于**滑块手柄 `.cx_rightBtn` 的 `left`
   （实测按住手柄中心拖 142px，手柄走 142、块只到 134，差 8px），而且这个差值与按下点有关。
   做法：`mouse.down()` → 按缓动分 30 步移动 → 多次读 `parseFloat(qs('.cx_imgBtn').style.left)`，
   `err = target - left` 再补移到 `err<0.6px` → 停留 250ms → `mouse.up()`。

**失败代价**：松手位置偏了会静默换一张新图（`#cx_imgBg` 的 URL token 变），不提示"失败"，
所以脚本要先打印/核对 `bg` 与 `piece` 两个图片地址，确认没被换图再继续。

**How to apply**：
- 图片地址直接从 DOM 取：`getComputedStyle(#cx_imgBg).backgroundImage` 与 `.cx_imgBtn img` 的 `src`；
  两个 URL 都是 `slide/big|small/<token>.jpg`，**small 实际是 PNG（带 alpha）**，按扩展名硬解会失败。
- 缺口坐标是 320×160 原图坐标；页面按 `rect.width/320` 缩放（本次为 1:1），缩放不为 1 时要换算。
- 通过判据：`#eject` 弹层消失 + URL 跳到 `exam-ans/exam/test/reVersionTestStartNew`。
- 打开浏览器窗口被最小化时 **screenshot 会直接报错**（"Cannot capture a screenshot while the window is minimized"），
  但 DOM 读取、`mouse.*`、`evaluate` 全部正常——本方案不依赖截图。

关联 [[nested-iframe-coordinates-need-frame-offset-sum]]、[[web-automation-call-page-functions-not-dom-clicks]]。
