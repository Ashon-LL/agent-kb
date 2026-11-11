---
name: chaoxing-video-report-threshold-vs-navigation-gate
description: 超星视频任务点约87%就上报，但打开下一章要求累计观看≥90%；把"上报"当"可以切下一节"会一直被重定向回上一章
type: pitfall
topic: browser
source: chaoxing-automation
date: 2026-11-07
verified: 2026-11-07
---

**经验**：超星（Chaoxing）课程里，"视频任务点上报"和"允许进入下一章"是两个不同的门槛。
任务点通常在观看 **~87%** 时就把 `jobUnfinishCount` 减一（页面上的 `.icon_Completed` 要 reload 后出现），
但**章节导航校验看的是累计观看时长 ≥ 总时长 90%**（页面完成条件原文："观看时长需 ≥ 总时长的 90%"）。

**症状**：视频播到 86~88% 就切去做章节测验、提交后想打开下一节，结果：
- 访问带下一章 `chapterId` 的学习页 URL，**URL 立刻被改回上一章的 chapterId**（服务端 302 / SPA 同步），
- 页面全局 `chapterId`、`curChapterId` 输入框、侧栏高亮全部指着上一章，
- 换个新标签重新打开也一样，看起来像"enc 失效"或"页面坏了"，实际只是没过 90% 门槛。

**How to apply**：
1. 每节视频**播到 94%~97%** 再切走（留 4~7% 余量抵消服务端计时与客户端 `currentTime` 的偏差）。
2. 判据不要只看 `input.jobUnfinishCount` 归零；要同时看**下一章 URL 是否能稳定停留**。
3. 已经提前切走的章节，回到该节第 1 页（`PCount.next('1', cid, ...)`）续播补足即可，服务端保留观看进度。
4. 若确认已 ≥95% 仍被重定向，再怀疑 enc/会话问题，别一开始就往 enc 上查。

**代价**：本次《大学生就业指导》1.2 在 87.6% 上报后立即切测验，随后 1.3 连续 6 次导航全部被拉回 1.2，
补播到 97.8% 后一次成功；每节多花约 10% 时长，但避免了反复重定向和"章节打不开"的误判。

关联 [[chaoxing-quiz-question-bank-title-mapping]]、[[nested-iframe-coordinates-need-frame-offset-sum]]。
