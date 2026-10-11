---
name: web-automation-call-page-functions-not-dom-clicks
description: Web自动化操纵SPA页面：直接调页面函数+服务端接口是确定性方案，element.click()/UI模拟时灵时不灵
type: pitfall
topic: browser
source: chaoxing-automation
date: 2026-10-11
verified: 2026-10-11
---

**经验**：自动化操纵带交互的 SPA 页面时，优先级排序应为：① 直接调用页面自己的函数（从 `onclick` 属性 reverse 出来的，如 `addChoice(li)`）→ ② 直接调用页面完成任务的服务端接口（从源码 `finishJob` 等 reverse 出 URL+参数后 `fetch`）→ ③ `element.click()` / 事件派发 → ④ 模拟 UI 操作（滚动、等待、停留）。①②是确定性方案，③④时灵时不灵——受上报周期、节流、事件信任检查影响，"时好时坏"的失败最难排查。

**Why**：超星学习通实战（2026-10-11）：PDF 任务点滚动到底+等待 90s 只有约 5% 成功率（触发完成靠客户端上报周期，且可能被节流）；改用页面 `AttachmentSetting` 里的 jobid/jtoken 直接 fetch 完成接口后 21 项全部一次通过。测验选项用 `element.click()` 只命中部分（Q2/Q3/Q4 静默失效），直接调 `addChoice(li)` 全部生效。

**How to apply**：
- 多层嵌套 iframe：递归遍历 `contentDocument` 找目标 frame（panView/wpsView/frame_content 等按 id 定位）。
- 字体混淆页（font-cxsecret 类）：DOM `textContent` 是乱码但截图渲染正常——用截图+视觉读内容，别试图解码 DOM。
- SPA 内切换章节后 iframe 可能残留旧内容：操作前 `reload`。
- 验证页面状态看服务器快照（reload 后读侧栏计数）而非同页 DOM（不实时更新）；权威进度在列表页顶部计数。
- 外层 `window.scrollTo` 可能被页面脚本重置：优先对目标元素 `scrollIntoView({block:'center'})`。
- 截图读长页面：给内容容器设 `style.zoom = 0.55~0.8` 一屏看更多。

关联 [[browser-extension-forensics-profile-leveldb]]、[[browser-only-success-check-credential-first]]。
