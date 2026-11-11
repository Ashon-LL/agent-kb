---
name: nested-iframe-coordinates-need-frame-offset-sum
description: 点嵌套 iframe 内元素时 getBoundingClientRect 只是帧内坐标，必须逐层加 frameElement 的 rect 才能用顶层鼠标点击
type: pitfall
topic: browser
source: chaoxing-automation
date: 2026-11-05
verified: 2026-11-05
---

**经验**：用顶层鼠标坐标（`page.mouse.click` / CDP `Input.dispatchMouseEvent` / 任何"按屏幕坐标点击"的封装）去点嵌套 iframe 里的元素时，
元素自身的 `getBoundingClientRect()` **只在该 iframe 的视口坐标系内有效**，直接拿它点击会全部落空，而且不会报错——
表现为"点了没反应"，很容易误判成页面脚本失效或事件被拦截。

**Why**：超星测验页的选项在两层 iframe 里（top → `iframe#iframe`(cards) → `iframe`(work/video)）。
对 `li` 取 rect 后直接 `mouse.click`，19 次点击全部无声失败，`check_answer` 一个都没出现；
按帧偏移换算后同一次点击立刻生效。同类问题在视频播放按钮上复现（按钮 rect y=260，实际屏幕 y≈1080）。

**How to apply**：
```js
// 在页面内执行：把元素中心换算成顶层视口坐标
const r = el.getBoundingClientRect();
let x = r.x + r.width / 2, y = r.y + r.height / 2;
let win = el.ownerDocument.defaultView;
while (win && win !== window) {
  const fe = win.frameElement;
  if (!fe) break;
  const fr = fe.getBoundingClientRect();
  x += fr.x; y += fr.y;
  win = win.parent;
}
return { x: Math.round(x), y: Math.round(y) };
```
- 点之前先 `el.scrollIntoView({block:'center'})`，再取 rect；页面内部滚动容器不一定吃 `window.scrollTo`。
- 换算后还要判断是否在视口内（`0 < y < innerHeight`），否则点击会落到视口外的坐标上。
- 若目标在视口外且滚动无效，先对祖先 iframe 也做一次 `scrollIntoView`。
- 交叉验证：点完读元素的选中标志（单选用 `.check_answer`、多选用 `.check_answer_dx`），别只看"没报错"。

关联 [[web-automation-call-page-functions-not-dom-clicks]]、[[browser-only-success-check-credential-first]]。
