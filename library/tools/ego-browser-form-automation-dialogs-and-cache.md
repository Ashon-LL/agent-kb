---
name: ego-browser-form-automation-dialogs-and-cache
description: ego-browser 自动化老式表单站（以 Editorial Manager 稿件重交为例）的破障与取证：浏览器级权限气泡会卡死 Input 分发、jQuery UI 的 ui-dialog 才是"点了没反应"的真因、EM 上传拒绝重名必须"先删后传"、EM 的 fileDownload.asp 不带 authVer=true 返回旧版成品、pdftotext -layout 会把 PDF 表格式封面错读成"元数据错位"
type: tool
source: 2026-10-21 本机 Neurocomputing 稿件（NEUCOM-D-26-23431）被退回作者后的修正版重交全程
date: 2026-10-21
verified: 2026-10-21
topic: browser
---

**经验**：

1. **交互被"卡住"时先分清是哪一层**。ego-browser 里出现 `CdpRequestTimeoutError: Input.dispatchMouseEvent` 而 `page.mouse.move()` 正常、`page.evaluate()` 正常，说明**渲染器活着、输入分发被浏览器级 UI 挡住**（本例是站点触发的「下载多个文件」权限气泡）。此时不要重试同一 click：改用 DOM 级点击 `el.click()`（走页面 JS，不经过 Input），导航/提交都能过。ego 的 CDP 白名单**不含** `Browser.grantPermissions` / `Browser.setPermission`，别指望用它预授权。

2. **DOM 点击"没反应"十有八九是弹了 jQuery UI 对话框**。EM 这类 ASP.NET 老站用 `$(document).on('click', '#btn...', ...)` 委托 + jQuery UI 弹确认框。`el.click()` 其实是生效的，只是弹窗在等确认。判据：`.ui-dialog` 里 `offsetParent !== null` 的元素；EM 的删除确认按钮文案是 **Proceed**，ORCID 提示是 **Proceed without ORCID iD**，确认提交是 **OK**。⛔ 只点 `Close` 等于什么都没做（我第一次就栽在这里，连着三轮以为按钮失效）。

3. **EM 上传拒绝重名，替换必须先删后传**。上传"成功"但列表不变时，先看页面里的错误条：`File not uploaded: duplicate filename detected <name> <size>`。EM 是选好文件即自动上传（无需点 "Attach This File"），所以修法是：勾选旧行 → 点 Remove → 弹窗点 Proceed → 再传同名新文件。

4. **判 EM「重交是否真的生效」只认 `authVer=true`**。`fileDownload.asp?...&file=XXX.pdf`（不带 `authVer`）返回的是**上一版审批产物**——本例表现为 35 页、CreationDate 是退回前的日期、旧占位仍在，差点据此误判"构建没生效"。**必须 `&authVer=true`** 才是本次新构建（37 页、CreationDate 是刚才构建时刻）。HEAD 请求的 content-length 在该端点不可靠（同一 URL 每次不同），别用它判版本。

5. **`pdftotext -layout` 会把 PDF 表格式封面错读成"字段错位"**。EM 生成稿首页是「标签列 | 数值列」的表格，`-layout` 按不同基线交错输出后，看起来像 "Corresponding Author: Deep Learning / Abstract: 作者名"，极易误判成元数据整体错位。**必须渲染成图再看一眼**（`pdftoppm -f 1 -l 1 -r 110 -png`）——本例渲染后封面完全正确。

6. **ego-browser 的 popup 会被拦**。`window.open` 出来的窗口在无用户手势时不产生 `waitForEvent("popup")`；EM 的 View Letter 之所以能开，是因为它走 `<a href="javascript:...">.click()`。别再试图用 `page.click` 去点（Input 被挡），直接读该 link 指向的 JS 函数源码拿真实 URL（`String(w.viewPDF)`），再用 `page.fetch(url, {saveAs})` 借页面会话把文件取回来验。

7. **EM 的时间是站点时区**。列表里的 `Status Date Oct 20 1:30PM` 实际是北京时间 2026-10-21 01:30（EM 侧按美东记）。对时间线时先换算，别把"今天的动作"读成"昨天的旧状态"。

**Why**：老式表单站（EM/投稿系统/政企后台）的失败面几乎都在"浏览器层的弹窗 + 站点的委托事件 + 服务端多版本产物"这三处，而不是选择器写错。把这三处分开取证，每一步都能给出"到底是哪一层没生效"的确定答案；混在一起就会陷入"重试→报告有进展→其实没动"的循环。

**How to apply**：① 输入超时先测 `mouse.move` / `evaluate` 分辨"渲染器死"还是"输入被浏览器 UI 挡"；② 换 DOM 点击并把**所有可见 `.ui-dialog` 的按钮文案打出来**再选；③ 上传/删除后**必须回读列表**核对条目类型与文件名，不认"点过了"；④ 判产物新旧用**构建时间 + 内容特征串计数**（如某段落 grep 计数），并对可疑端点试权威版参数；⑤ 判 PDF 版式类问题时渲染成图，不信 `-layout` 文本。

⛔ **落点纪律（本技能自带的最大陷阱）**：本技能文档示例把工作目录写成 `C:/Users/<name>/ego/<goal>-YYYYMMDD-HHMM/`，**那只是示例**。团队纪律是工作产物放**项目目录本身**（本次被用户当场纠正两次：不该在用户主目录另开 `C:\Users\<user>\<task>\`，也不是 `~/.zcode/workspace/<项目>/`）。照抄示例路径会制造仓库外的孤儿目录。相关：[[tencent-browser-skill-setup]]、[[browser-extension-migration-mechanism-first]]。
