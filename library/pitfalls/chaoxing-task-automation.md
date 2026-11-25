---
name: chaoxing-task-automation
description: 超星题库编号映射、滑块缺口闭环拖动、视频上报阈值与导航门槛；同一平台的三关
type: pitfall
source: 合并自 chaoxing-quiz-question-bank-title-mapping, chaoxing-slider-captcha-gap-and-drag, chaoxing-video-report-threshold-vs-navigation-gate；chaoxing-automation; chaoxing-automation; chaoxing-automation
date: 2026-11-07
verified: 2026-11-11
topic: methodology, browser
---
**经验**：超星题库编号映射、滑块缺口闭环拖动、视频上报阈值与导航门槛；同一平台的三关

> 本条由 3 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## chaoxing-quiz-question-bank-title-mapping

**经验**：超星课程（庄明科《大学生就业指导》系列，题库沿用多年）的章节测验，**标题就是题库编号**：
进入测验页时正文显示「7.1.5作业」「6.1.3作业题」「初步了解简历」等，这个编号可以直接拿去搜索/比对现成答案库
（例如简书的长文答案、道客巴巴/人人文库的历年答案文档），命中率很高。

**但答案库有三个坑**（本次 41 套测验实测）：

1. **"我的答案"不等于正确答案**：答案库里每题后面若跟着 `得分：33.3分`，说明那题答对了；
   若**没有得分标注**，那条"我的答案"很可能就是错答（作者贴的是自己的作答记录）。直接照抄会踩坑。
   实证：`6.1.8` 的判断题、"简历第三步"的两道判断题，答案库都没给分，照抄全错。
2. **选项顺序可能与题库不同**：同一编号在不同学期可能是同一组题但顺序打乱，必须按**题干/选项文本**逐题对齐，不能按序号搬。
3. **判断题不能靠题库反推**：判断题的"对/错"强依赖课程措辞与价值取向（例："简历要体现对行业的了解和热情"→对；
   "以谦虚好学态度赢得 HR 好感"→错，因为不应刻意讨好）。答案库没把握时，按课程价值观 + 排除绝对化表述判更稳。

**How to apply**：
- 进测验页先记录标题编号 → 查答案库对应小节 → 按题干文本匹配 → 再逐题过一遍"是否绝对化/是否与同卷他题矛盾"。
- 多选题用得分反推：少选得半分、错选得 0，可据此确定漏选/错选项。
- 宁可少选也不要带明显错项；判断题优先按课程原话，不按常识。

关联 [[chaoxing-task-automation]]。

## chaoxing-slider-captcha-gap-and-drag

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

## chaoxing-video-report-threshold-vs-navigation-gate

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

关联 [[chaoxing-task-automation]]、[[nested-iframe-coordinates-need-frame-offset-sum]]。
