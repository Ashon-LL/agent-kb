---
name: qoder-office-pptx-image-and-animation-workarounds
description: Qoder Office MCP put_page 的 imageFiles 管线可能整体故障（OPERATION_FAILED），改用 put_page(无图)+put_image 两步；页内动画只能 zip 注 XML，MCP 会自动重同步且保存不丢
type: pitfall
source: Qoder Presentations Office MCP 演讲稿打磨实弹（落盘日无明确记录，取入库日）
date: 2026-09-30
verified: 2026-09-30
---

**经验**：
1. `put_page` 带 `imageFiles`/image 元素时可能连续 `QODER_OFFICE_OPERATION_FAILED`（即使同格式的 PNG/JPEG、同路径此前成功过）——这是图片管线整体故障，不是参数错误。正确绕法：**put_page 先放白边框 rect + 全部文字（不含 image 元素），再对每张照片调 `put_image(frame={x,y,w,h})` 插入**。put_image 走另一条管线，验证可用；图片按追加顺序在 z 序顶部，只要与文字不重叠就无副作用。
2. Office MCP 无元素动画能力（COM 也拿不到 AnimationProperties）。页内动画要**直接往 pptx zip 注入 `<p:timing>`（mainSeq + presetClass="entr" presetID="10" fade 的 clickEffect/withEffect 分组）+ `<p:bldLst>`**，spid 按 spTree 中 sp/pic/cxnSp 的文档序取得。
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
