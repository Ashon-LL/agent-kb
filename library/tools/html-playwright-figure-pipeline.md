---
name: html-playwright-figure-pipeline
description: 出版级中文配图用「HTML/CSS 卡片 + 无头浏览器元素截图」，2x 清晰度、中文字体可控；优于 matplotlib（设计型图版式死板）与 AI 生图（中文必乱）
type: tool
source: WorkBuddy 参赛帖配图（2026-09-23，一次产出 8 张）
date: 2026-09-23
verified: 2026-09-23
topic: office, browser
---

**经验**：要给文章 / 帖子 / PPT 出**设计型**中文配图（流程卡、对比表、终端风格卡、柱状图），别用 matplotlib 硬凑版式，也别用 AI 生图（中文必然乱码）。

**三步做法**（一个脚本跑完，秒级）：

1. 写一个 `figs.html`：每张图一个 `<div class="fig" id="fig-x">`，宽度固定（正文图 1040px 够用），样式全走 CSS 变量；中文用 `Microsoft YaHei`，代码用 `Consolas`（本机系统字体，不要指望 webfont）。
2. Playwright **元素级**截图，不要整页截：
   ```python
   page = browser.new_page(viewport={"width": 1180, "height": 1000}, device_scale_factor=2)
   page.goto(Path("figs.html").resolve().as_uri())   # 必须 file:// URI
   page.wait_for_timeout(600)                        # 留一点字体就位的余量
   page.locator("#fig-x").screenshot(path="images/01-x.png")
   ```
3. 改图只改 HTML，重跑脚本即可；源文件（html + shot.py）与产物同目录留存，别当临时脚本删。

**为什么这样最省事**：
- `locator().screenshot()` 自动按元素内容高度裁切 ⇒ 不用预设画布尺寸，也不会截断长文卡片。
- `device_scale_factor=2` 出 2x 图，社区 / 公众号上传压缩后仍锐利。
- 8 张图放同一个 HTML 里一次批量截完，比开多进程或逐张渲染快得多。
- 深浅混搭效果好：封面用深色渐变、正文图用浅色底（配白底阅读页更协调）。

反例：用 `page.screenshot(full_page=True)` 会把多个 fig 一起截进来，还得自己算裁剪框。

相关：[[html-to-docx-windows-venv-layout]]、[[workbuddy-present-files-url-opens-sidebar-browser]]

关联 [[qoder-office-pptx-image-and-animation-workarounds]]。
