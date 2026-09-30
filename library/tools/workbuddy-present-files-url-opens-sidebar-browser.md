---
name: workbuddy-present-files-url-opens-sidebar-browser
description: WorkBuddy 里给 present_files 传 URL 会直接在侧栏内置浏览器打开该网页（不是打开文件、不是 artifact 卡片）
type: tool
source: MH-Agent-Open（20260918 用户确认）
date: 2026-09-18
verified: 2026-09-18
---

**事实**：`present_files` 的 `files` 数组元素既可以是**本地绝对路径**，也可以是 **http/https URL**。

- 传 **URL** → WorkBuddy **在侧栏内置浏览器面板打开该网页**（用户会看到右侧栏跑了浏览器）。
- 传 **本地 .html/.htm** → 既开实时预览面板、又列 artifact 卡片。
- 传**本地其它文件**（图片/报告/pptx/视频/代码）→ 只列 artifact 卡片，不启浏览器。

**Why**：这解决了"需要让用户看我刚推的 PR / 刚起的本地服务 / 某个在线页面"的需求——
不必再让用户手动复制链接。用户 20260918 原话："你刚才是打开了侧栏浏览器吗？这个我要表扬你一下。"

**How to apply**
- 要让用户直接看到 PR / Issue / 在线文档 → 把它作为 `files` 里的 URL 传给 `present_files`。
- 要展示本地 dev server → `files` 传 `http://localhost:<port>`（先确实起好服务；工具会做可达性检查）。
- 工具回执里带 `previewed` / `@share-html#<host>%2F...:<url>` 这类标识串时，**不要**把它当成"打开了某个 share-html 文件"——那只是回执元数据，实际行为就是打开该 URL。
- ⛔ 不要传 Ardot 设计文件 URL（`ardot.tencent.com/file/...`）：那类画布已由 MCP App artifact 面板承载，`present_files` 会跳过。

**与"打开本地文件"的区分**：若用户说"你打开了文件？"，先看当时传的是路径还是 URL——
是 URL 就是侧栏浏览器，是本地 html 就是预览面板 + artifact 卡片，两者表现形式不同。
