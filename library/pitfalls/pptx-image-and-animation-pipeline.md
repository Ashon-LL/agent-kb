---
name: pptx-image-and-animation-pipeline
description: PPTX 动画用 COM 原生接口而非手写 XML；Qoder Office MCP 图片管线故障与页内动画 zip 注 XML
type: pitfall
source: 合并自 pptx-anim-com-not-handwritten-xml, qoder-office-pptx-image-and-animation-workarounds；二叉树遍历课件动画优化实弹（18 页 / 374 效果重排）; Qoder Presentations Office MCP 演讲稿打磨实弹（落盘日无明确记录，取入库日）
date: 2026-09-30
verified: 2026-10-19
topic: office, windows, mcp
---
**经验**：PPTX 动画用 COM 原生接口而非手写 XML；Qoder Office MCP 图片管线故障与页内动画 zip 注 XML

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## pptx-anim-com-not-handwritten-xml

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
13. **动画分组必须在建板时显式声明，绝不能事后按坐标猜**。用 y 阈值聚类分组的实测结果：14 页坏 4 页——目录页 24 个元素被切成 8 段逐条冒（行距 52pt，锚点累计后超阈值）、五卡页后半段同时蹦出（`k*GAP` 撞上限截断）、封面先闪一帧亮图（图与遮罩被分成两组）、互动页整页没动画（改代码时漏掉）。正解：建板脚本里 `begin(auto=)/end()` 包裹语义块（不动缩进，比 `with` 好插入），导出 `plan.json`，动画脚本照单执行。**判据**：一份 14 页课件合理的点击数是每页 1-2 次，超过 4 次说明组被切碎了。
14. **组内错峰要分批，不要线性递增**：`(k // 6) * 0.05`，不是 `k * 0.06`。线性递增在元素多时撞上 delay 上限，表现为"后半段元素同时出现"——这是"动画不对劲"最隐蔽的一种。
15. **满幅背景图与遮罩必须同一组**，否则图先淡入、遮罩后到，中间闪一帧无遮罩的亮图。
16. **`Shapes(x)` 只接受名称或 1-based 位置索引，不接受 `Shape.Id`**。用 Id 索引会命中错误形状或抛错，表现为"每页总有 1 个形状加不上动画"。必须 `by_id = {sh.Id: sh for sh in s.Shapes}`。
17. **`AddEffect(Shape, EffectId, Level, Trigger)` 第 4 参是 Trigger 不是时长**。误传时长（`AddEffect(sh, 10, 0, 0.32)`）会让部分形状抛 `-2147352567`，报错完全不提参数问题。时长一律事后 `eff.Timing.Duration = 0.35`。
18. **配图检索的免费判定**：Unsplash URL 里 `images.unsplash.com/photo-xxx` 免费可用，`plus.unsplash.com/premium_photo-xxx` 是付费图库不能用。搜图后必须**逐张目视**——标题写"classroom"的可能是欧美青少年，与中文课件场景违和；换成 `Chinese students classroom` 才拿到中国教室。图片按目标比例用 PIL `cover_crop` 预裁（`add_picture` 给 w/h 会直接拉伸变形），输出 2x 像素。
19. **python-pptx 会自动去重相同媒体**：同一张图在封面和结束页各插一次，`ppt/media/` 里只存一份（实测 5 个图片形状 → 4 个媒体文件）。所以满幅图跨页复用时不必手动复用 rel，直接两次 `add_picture` 即可。
20. **删中间产物前先确认下游能重建**：配图流程是「下载原图 → `prep_images.py` 裁切 → `img/final/` 成品」。若把下载的原图删了，裁切脚本就再也跑不动，只能靠 README 里记的 photo ID 重新下载。**结论：源素材（外部获取的）必须留 ID/URL 记录，否则管线不可复现**——中间产物（如 `plan.json`）才是可以随手删的。
**Why**：一次 18 页课件动画优化，前期用脚本手写 `<p:timing>` 注入，结构"看起来对"（每个 par 都合法）但 PowerPoint 放映时退化成每页几十次点击——正是本项目 v5 方案文档早已实证过、却又被新脚本重复引入的坑。改走 COM 后一次成型，且 `<p:timing>` 由 PowerPoint 自己生成，无需再验结构。

**How to apply**：需要增删改 pptx 动画/字号时，先 `tasklist | grep -i powerpnt` 确认有 PowerPoint 可用 → 写 COM 脚本（spid 方案先干跑校验）→ finally 里 Close/Quit 都 try → 保存后用 COM 回读 TriggerType 分布 + python-pptx 数字号分布双重校验 → LibreOffice 渲染目视。只有在完全没有 Office 的机器上才退回 zip 注 XML（那时按 [[pptx-image-and-animation-pipeline]] 第 2/11 条的结构写，且必须让链式步骤各占独立中间层 par、delay 为累计时刻）。

关联 [[pptx-image-and-animation-pipeline]]。

## qoder-office-pptx-image-and-animation-workarounds

**经验**：
1. `put_page` 带 `imageFiles`/image 元素时可能连续 `QODER_OFFICE_OPERATION_FAILED`（即使同格式的 PNG/JPEG、同路径此前成功过）——这是图片管线整体故障，不是参数错误。正确绕法：**put_page 先放白边框 rect + 全部文字（不含 image 元素），再对每张照片调 `put_image(frame={x,y,w,h})` 插入**。put_image 走另一条管线，验证可用；图片按追加顺序在 z 序顶部，只要与文字不重叠就无副作用。
2. Office MCP 无元素动画能力（COM 也拿不到 AnimationProperties）。页内动画要**直接往 pptx zip 注入 `<p:timing>`（mainSeq + presetClass="entr" presetID="10" fade 的 clickEffect/withEffect 分组）+ `<p:bldLst>`**，spid 按 spTree 中 sp/pic/cxnSp 的文档序取得。
   ⚠️ **但"COM 拿不到动画"只在无本机 PowerPoint 时成立**——本机装了 Office（POWERPNT.EXE 在册）时，`win32com` 直连 PowerPoint.Application 的 `Slide.TimeLine.MainSequence` 完全可用，且**改已有动画首选 COM、不要手写 timing XML**。手写失败模式实证：把若干效果平铺成同层 `clickEffect`（或 afterEffect 同 par 平铺），PowerPoint 只认组首效果为触发点，其余退化成"单击一次出一条"——这正是 374 个效果全平铺、每页要点 20~41 次的根因。COM 正确做法：`e.Timing.TriggerType = 2/3`（2=WithPrevious 同组齐出、3=AfterPrevious 自动接续）+ `e.Timing.TriggerDelayTime`，PowerPoint 自己重写 timing 树并补上正确的中间层 `<p:par>`，结构 100% 合法。详见 [[pptx-image-and-animation-pipeline]]。
3. 外部 zip 改完后 MCP 会在下一次读取时**自动重同步磁盘**（revision+1、dirty:false），之后的 apply_ops/save_document **不会丢掉注入的 timing**（实测保存后 47 组 clickEffect 全保留）——但每次保存后仍要 `count('nodeType="clickEffect"')` 复核。
4. 重排/替换页面（put_page）会**丢失该页已注入的动画与切页转场**：所有布局返工完成后必须重新枚举形状序号、更新分组字典、重新注入，并对全部页重发 `setTransition fade`。
5. `apply_ops addElement kind:"textbox"` 带 stroke 生成的形状**没有 `<a:prstGeom>`**，PowerPoint 导出时完全不画边框（MCP audit 不报）。绕法：zip 直改，在 spPr 的 xfrm 后插入 `<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>`；或改用 kind:"rect" 再 setFill "none"。
6. 新字体**只装到 per-user（HKCU\...\Fonts + AppData\Local\Microsoft\Windows\Fonts）时 PowerPoint 不识别**（渲染回退成黑体，且无报错）；需管理员装到 `C:\Windows\Fonts` + HKLM 注册表，重启 POWERPNT 后 COM 导出才生效。装前用 PIL `ImageFont.truetype(f).getname()` 核对内部 family 名与 pptx 里 `<a:latin/ea/cs typeface>` 完全一致。
7. Google Fonts 的中文书法体（Ma Shan Zheng 马善政毛笔楷书、Long Cang、Liu Jian Mao Cao，OFL 免费商用）GitHub raw 直连常挂（curl exit 56），用 `https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/<dir>/<File>.ttf` 镜像秒下；PIL 在深红底渲染样图再 Read 审字效，是最快的选型方式。
8. **图片框"循环播放"用 GIF 直替最省事**：PIL 生成多帧 GIF（Ken Burns+crossfade，`loop=0` 即无限循环；建议全局调色板重量化 `f.quantize(palette=pal)` 更稳），zip 注入 `ppt/media/x.gif` + `[Content_Types].xml` 加 `Default Extension="gif"`，再把目标 pic 的 `a:blip r:embed` 指到新 rel——放映时 GIF 自动动，不需要任何 timing XML。
9. **slide rels 的 Target 相对 slide part 解析**：必须写 `../media/x.gif`，写成 `media/x.gif` 会指向不存在的 `ppt/slides/media/`，PowerPoint 显示"无法显示该图片"占位符且**不报任何错**（MCP/zip 写入都成功）。排查先 grep rels 里其他正常图片的 Target 前缀对齐写法。
10. `addElement` 的 `fill` 只接受 `"#RRGGBB"/"#RRGGBBAA"`，传 `"none"` 直接 `QODER_OFFICE_PPTX_OP_INVALID`（整批回滚）；要无填充边框就**省略 fill 字段**（默认无填充、只画 stroke）。`setFill` 才接受 `"none"`。
11. **进页即自动播第一组动画**（避免翻页后空白）：该组外层 group par 的 `<p:stCondLst><p:cond delay="0"/>`（其余组 `indefinite`），组内所有形状节点 `nodeType="withEffect"`（其余组首形状仍 clickEffect）。背景图/遮罩/边框/角饰一律不注册进 mainSeq/bldLst，保持常显。
12. `put_page` PageSpec 每个元素必须给全 `x,y,w,h`（缺 h 直接参数校验失败）；`apply_ops` 必须带 `operationId`。

**Why**：一次 12 页演讲稿 PPT 打磨中，put_page 图片管线突然全挂，按报错盲改参数浪费多轮；动画注入与 MCP 草稿的先后顺序若搞反，白做一轮注入；GIF rels 路径少写 `../` 导致放映页"无法显示该图片"，导出 PNG 才暴露。

**How to apply**：用 Qoder Presentations Office MCP 生成含真实图片/页内动画的 pptx 时。诊断顺序：read_context 确认 revision 未变（失败操作不落版本）→ 最小页面二分 → 确认是图片管线则直接切 put_image，不要反复换 operationId 重试同结构。渲染自查用 PowerPoint COM `Slide.Export(png,1280,720)`，兼容性验收用 `SaveCopyAs(tmp,24)` 后重数 timing 节点。

关联 [[html-playwright-figure-pipeline]]。
