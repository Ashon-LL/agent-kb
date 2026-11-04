---
name: renderer-reload-is-not-context-loss
description: Electron 应用里 webContents.reload() 只重建渲染层，会话/任务上下文若在后台进程或数据库里就不会丢；别把「UI 被打断」说成「任务被重置」
type: pitfall
source: zcodepro（2026-10-26 ZCode v29，用户当场纠正）
date: 2026-10-26
verified: 2026-10-26
topic: browser, diagnosis, verification
---

**事故**：内存看门狗在硬阈值（3.6GB）会 `webContents.reload()` 主窗口。我在说明里写成
「代价是**任务上下文被重置**」，用户直接反问：「我们只推导渲染层，为什么会牵扯到上下文？」

**Why**：这个应用的架构是 **渲染层（UI）+ 后台 agent（执行）+ SQLite（持久化）** 三层：

- 会话消息、任务状态、模型输出都在 agent 与 `cli/db/db.sqlite` 里；
- 渲染层只是视图 + 输入。`reload()` 只重建视图进程；
- 真正丢的是**界面状态**：滚动位置、展开/选中的面板、输入框焦点与选区、过渡动画；
- 代码证据：看门狗里 `reloadSoon()` 只调 `wc.reload()`，没有重启 app、没有杀 agent。

**How to apply**：
1. 描述崩溃/重载后果前，先确认**状态归属**：这份状态在哪个进程/存储里；
   "进程重启"≠"数据丢失"，"UI 重置"≠"任务中断"。
2. 看代码而不是看现象：`reload()` / `webContents.destroy()` / `app.relaunch()` 三者后果完全不同，
   只有最后一种会动到后台进程（如果后台是 app 的子进程）。
3. 对外表述用可验证的句子：「重载渲染层会丢滚动位置与面板展开态；会话与任务在 agent/DB 里，不丢」。
4. 如果确实会出现"任务丢失"，那要去找**谁在持有任务状态**（是不是只在渲染层内存里），
   而不是笼统归因给"内存治理"。

关联 [[react-node-reuse-vs-imperative-dom]]
