---
name: pptx-anim-com-not-handwritten-xml
description: 改已有 pptx 动画用 PowerPoint COM 原生接口（TriggerType/TriggerDelayTime），不要手写 timing XML；附 COM 七个实操坑（Visible 不可设/Runs 集合不可调/窄框不抬字号等）
type: pitfall
source: 二叉树遍历课件动画优化实弹（18 页 / 374 效果重排）
date: 2026-10-19
verified: 2026-10-19
topic: office, windows
---

**经验**：

1. **本机装了 Office 时，改动画必须走 PowerPoint COM**：`win32com.client.Dispatch("PowerPoint.Application")` → `Presentations.Open(path, WithWindow=0)` → `Slide.TimeLine.MainSequence`。写 `Effect.Timing.TriggerType = 2`（WithPrevious，同组齐出）/ `3`（AfterPrevious，自动接续）+ `TriggerDelayTime`，`pres.Save()` / `SaveAs()`。PowerPoint 会自己重写 `<p:timing>` 并补上正确的中间层 `<p:par>`——**这是手写 XML 做不到的**。
2. **手写 timing XML 的失败模式（已实证）**：把 N 个效果平铺成同一层 `clickEffect`，PowerPoint 只把组首效果当触发点，其余全部退化成"单击一次出一条"。18 页课件因此每页要点 20~41 次。判别法：数 `nodeType="clickEffect"` 的数量，正常应是"语义组数"，而非"效果总数"。
3. **加新动画**（原页 0 效果时）：`seq.AddEffect(shape, 10, 0, 0.32)`（10 = msoAnimEffectFade），再用 TriggerType 统一重排。
4. **COM 实操坑**：
   - `app.Visible = 0` / `app.Minimize = 1` **都抛异常**（PowerPoint 不允许隐藏窗口；Minimize 是 Window 对象属性不是 Application 的）。只能 `app.DisplayAlerts = 0` 后正常打开。
   - `TextRange.Runs()` / `.Paragraphs()` **调用即抛"不支持集合"**（-2147352559），`Runs` 也不能当属性取 `.Count`（"function object has no attribute Count"）。要按字符/段落细分就改用 XML；**只整框设字号时 `TextRange.Font.Size` 读写都正常**。
   - 同一份文件 COM 读 `Shape.Width/Left/Top` 可能全返回 0（python-pptx 保存过的文件）。需要几何判断时**用 python-pptx 读坐标、COM 只做写入**。
   - 形状定位用 `Shape.Id`，与 XML 里 `<p:spTgt spid>` 一致；但**方案里的 spid 必须来自该文件当前 MainSequence 的真实 Shape.Id**，不能按"标题/书眉应该有动画"臆测——干跑校验缺失比事后返工便宜。
5. **僵尸进程会让后续 COM 全废**：上次 `pres.Close()` 抛异常后 `app.Quit()` 没执行，留下的 POWERPNT.EXE 会让新实例 `Presentations` 属性直接 AttributeError。脚本 finally 里 Close/Quit 都要 try 包裹；卡住先 `taskkill //F //IM POWERPNT.EXE`。
6. **放映态验证**：`pres.SlideShowSettings.ShowType = 1`（ppShowTypeWindow，非全屏才能 PrintWindow 截到内容）；`LoopUntilEsc` 是只读属性不要写。放映窗口句柄 `SlideShowWindow` **没有 HWND 属性也没有 HWND() 方法**，用 `win32gui.EnumWindows` 匹配类名 `screenClass` 取。连续快速 `view.Next()` 会撞"被呼叫方拒绝接收呼叫"，每次之间 sleep 1s 以上。
7. **抬字号要按框宽设下限**：内容文字 <11pt 抬到 11pt，但**结点圆内单字母（Oval 28×28pt）、窄条徽标（框宽 <60pt 的 01/必做1/延伸）一律不抬**——放大必溢出。字号分布用 python-pptx 数 `r.font.size.pt` 复核，剩下的 <9pt 应全部是这类标签。
8. **抬完字号必须重新渲染目视**：11pt 常把原本 1 行的短句变 2 行、撑破卡片。定位法：python-pptx 扫 `est_lines * size * 1.35 > height`，再用 LibreOffice 转 PDF → `pdftoppm -png` 逐页 Read 确认真伪（估算偏保守，多数是误报，但每个都要看）。

9. **抬完字号必须重新渲染目视**：11pt 常把原本 1 行的短句变 2 行、撑破卡片。定位法：python-pptx 扫 `est_lines * size * 1.35 > height`，再用 LibreOffice 转 PDF → `pdftoppm -png` 逐页 Read 确认真伪（估算偏保守，多数是误报，但每个都要看）。
10. **演示类动画（遍历/流程逐步）用 Pulse(32) 逐个落点，不要用变色**：变色要设 `EffectParameters.FillColor`，COM 下极易卡住甚至弹模态框；Pulse 视觉已足够（用户确认"能看出来"）。写法：每段 `AddEffect(shape, 32, 0, 0.45)`，段首 `TriggerType=1`、其余 `3` + `TriggerDelayTime=0.05`，结论卡片挂本段最后一个脉冲之后（`3` + 0.15s）。
11. **AddEffect 的分组由添加顺序决定，事后改 TriggerType 改不了**：必须按"骨架 → [脉冲 → 卡片] × N → 收尾"的顺序加。若先把四段的脉冲全加完再加卡片，PowerPoint 会把末段脉冲和全部卡片捆成一组，一次点击全放完。加之前先 `while seq.Count>0: seq.Item(1).Delete()` 清空该页，否则新旧重复、且 COM 会把该页已有 cond 全重置为 onclick。
12. **保存对话框卡死流程的真因**：`DisplayAlerts=0` 对**关闭时的保存提示无效**。可写模式打开 + `Saved=False` → 关闭时弹"是否保存"。解法：①校验/截图/探测脚本一律 `Open(path, WithWindow=0, ReadOnly=1)`，根本不会问；②必须写的脚本在 finally 里 `pres.Saved = 1` 再 Close/Quit，且 Close/Quit 各自 try 包裹。**探测脚本最容易忘**——探完不 save 也不设 Saved，必然弹窗。
**Why**：一次 18 页课件动画优化，前期用脚本手写 `<p:timing>` 注入，结构"看起来对"（每个 par 都合法）但 PowerPoint 放映时退化成每页几十次点击——正是本项目 v5 方案文档早已实证过、却又被新脚本重复引入的坑。改走 COM 后一次成型，且 `<p:timing>` 由 PowerPoint 自己生成，无需再验结构。

**How to apply**：需要增删改 pptx 动画/字号时，先 `tasklist | grep -i powerpnt` 确认有 PowerPoint 可用 → 写 COM 脚本（spid 方案先干跑校验）→ finally 里 Close/Quit 都 try → 保存后用 COM 回读 TriggerType 分布 + python-pptx 数字号分布双重校验 → LibreOffice 渲染目视。只有在完全没有 Office 的机器上才退回 zip 注 XML（那时按 [[qoder-office-pptx-image-and-animation-workarounds]] 第 2/11 条的结构写，且必须让链式步骤各占独立中间层 par、delay 为累计时刻）。

关联 [[qoder-office-pptx-image-and-animation-workarounds]]。
