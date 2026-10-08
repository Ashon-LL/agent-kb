---
name: vite-build-output-names-track-source-eol
description: 【作用域=vite+@vitejs/plugin-vue】生产构建的 scope id=sha256(相对路径+源码原文)，源码行尾 CRLF↔LF 会改 data-v-* 并级联改全部 chunk 哈希名；git text 归一不显示该差异，对拍 dist 时别把「命名代差」误判为内容差异/构建过期
type: pitfall
source: MH-Agent-Open 安装区新鲜度核验（20261005）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
---

**经验**：vite + @vitejs/plugin-vue 生产构建里，每个 SFC 的样式作用域 id = `sha256(相对路径 + 源码原文)[:8]`（插件内 `descriptor.id = getHash(normalizedPath + (isProduction ? source : ""))`，`normalizedPath = path.relative(root, filename)`）。源码原文**含行尾字节** ⇒ 同一份逻辑内容，CRLF 版与 LF 版算出**不同的 scope id**；scope id 同时被写进该组件的 JS 与 CSS ⇒ chunk 内容哈希变 ⇒ 入口 chunk 的 `__vite__mapDeps` 表与动态 import 引用的文件名变 ⇒ **整个 JS 资产图（加受影响的 CSS）全部改名**。所有文件字节大小逐一不变，只有 8 位哈希名与 `data-v-*` 标记不同；构建本身是确定性的（连跑两次完全一致）。

**Why**：git 的 `text=auto`/`eol=lf` 行尾归一让 `git status` 全干净、内容 diff 为零，但构建读的是**磁盘原文** ⇒「仓库干净」不等于「产物可复现」。拿新构建对拍旧 dist 时：diff 满屏 Only in、文件全改名，极易误判成「dist 过期/内容不一致」，实际功能零差异（同一构建内 JS 渲染的 `data-v-*` 与其 CSS 选择器自洽，样式正确）。

**How to apply**：① 对拍构建产物先比「文件大小多重集」+「逐文件首个差异偏移」；若差异只落在哈希名/`data-v-*` 标记，按命名代差处理、不报内容问题。② 钉根因：对可疑组件各算一次 `sha256("src/.../Foo.vue" + 原文)`（LF 与 CRLF 两版），与产物中的 `data-v-*` 双向对照，命中即坐实。③ 要字节级一致：构建前先 `git checkout -- <files>` 把源文件行尾归一（eol=lf）再构建。相关：[[windows-scripting-terminal-gotchas]]（Edit/Write 保留原行尾、切分支后行尾可能已变）。
