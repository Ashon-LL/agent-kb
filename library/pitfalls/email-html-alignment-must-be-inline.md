---
name: email-html-alignment-must-be-inline
description: 邮件 HTML 的对齐/布局关键属性必须内联在单元格上——客户端会剥掉 <style>，导致"只有部分列跑偏"这种看起来像自己写错的症状
type: pitfall
topic: reporting
source: APIShow 巡检/告警邮件对齐（2026-10-18 用户两次反馈「部分列没做到」）
date: 2026-10-18
verified: 2026-10-18
---

**经验**：用 `<style>` 里的类给邮件表格定对齐，**在部分邮件客户端里会失效**：客户端把 `<style>` 整块剥掉后，
浏览器默认样式接管 —— `th` **默认居中**、数字列常被客户端设成右对齐。结果是同一个表格里
**一部分列（正好是带 class 的那些）看着偏了、另一部分正常**，症状很像"我代码写漏了"，
但在自己的浏览器里用同一份 HTML 渲染又是好的（因为浏览器不剥 style）。

**Why**：APIShow 的巡检报告与每小时告警都走自研 HTML 邮件。CSS 里已写明 `th{text-align:left}`、
`td{text-align:left}`、并去掉了 `td.num{text-align:right}`，但用户连着两次反馈
「第二部分渠道列、条数列没有做到；第四部分密钥列、请求列、总token列没有做到」（要求"文字水平居中靠左对齐"）。
本地用 Edge 渲染同一份 HTML 完全正常 ⇒ 差异在客户端渲染，不在我的标记。

**How to apply**：
1. **关键对齐一律内联**：每个 `<th>`/`<td>`（含 `colspan` 的整行单元格）都带 `style="text-align:left"`；
   宽度/换行这类"锦上添花"可以留在 `<style>`，但**对齐不要只靠它**。
2. **别用"数字列右对齐"**做默认审美 —— 用户往往要的是"全部靠左"；真要右对齐也得内联写清。
3. **验收看客户端，不看浏览器**：自查"我这边渲染没问题"不能证明用户看到的没问题；
   交付后**让用户直接看一封真实邮件**是最快的判据（本次就是靠用户截图+我逐格 grep 标记定的案）。
4. 自查手段：把生成的 HTML 里的每个单元格标签抓出来，断言都带内联左对齐（比截图更硬）。

## 追加（2026-10-18 第二轮：内联左对齐 ≠ 水平居中）

用户第二轮纠正：「**左对齐是正常的，我看没有做到的是水平居中**」。说明"居中"指的是
**卡片/表格这一块在邮件里水平居中**，而"没做到"的那些列指的是**格内文字左对齐** ——
**两件事要同时满足**，别把"居中"读成"格内文字居中"。

- ⛔ 块居中同样会被剥 `<style>` 打掉：CSS 的 `table{margin:6px auto}` 一没，表格就贴左。
  正确做法用**结构与属性**（这些不会被剥）：
  `<table role="presentation" width="100%"><tr><td align="center">` 包一层，
  内层表格再加 `<table align="center">`（等价于原 `margin:6px auto`，**不改变有样式时的表现**）。
- ⛔ 顺带一个隐蔽坑：`cellpadding="0"` 在**剥样式**的客户端会真的把格子压成 0 内边距 ⇒
  数字**挤成一坨**（`戌 (32 号) 151458147858+3600`）。改成 `cellpadding="6"` 兜底：
  有样式时 CSS 的 `padding` 优先级更高 ⇒ **零副作用**，剥样式时可读。
- ✅ **验证姿势（可复用）**：把生成 HTML 用 `re.sub(r"<style>.*?</style>", "", html)` **剥掉样式**，
  再交给无头浏览器截图 —— 直接复现最坏客户端。Edge：
  `msedge.exe --headless=new --disable-gpu --window-size=820,1500 --screenshot=<Windows 绝对路径> file:///<绝对路径>`
  ⛔ 相对 `--screenshot=` 的落点**不在当前目录**（找不到文件）；必须给 Windows 绝对路径。
- ✅ 更硬的断言：抓出所有 `<t[hd][^>]*>`，断言每个都带内联 `text-align:left`（或刻意写的 `:center`），
  再加一条"表格带 `align="center"` / 卡片有居中包裹"。

关联 [[aggregate-report-missing-values-must-be-none-guarded]]（同一交付物的另一族健壮性问题）、
[[account-pool-friendly-naming]]（同属"面向用户的呈现"口径）

关联 [[imap-mailbox-ops-qq-folder-quirks]]。
