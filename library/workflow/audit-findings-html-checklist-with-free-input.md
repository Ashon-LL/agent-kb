---
name: audit-findings-html-checklist-with-free-input
description: 审查发现较多时做本地 HTML 复选项页；方案可多选、逐题自由输入、导出选择，不替用户决定
type: workflow
topic: reporting
source: zcodepro 2026-11-15 全包/全项目/全功能审查（用户要求逐项选择）
date: 2026-11-15
verified: 2026-11-15
---

**经验**：全面审查后若问题/方案很多，直接把“让用户在对话里逐条回复”改成**本地 HTML 复选项页**更省事：
每题展示证据、归因、3–6 个方案与代价，支持多选、推荐项、自由输入、逐题或全部展开、localStorage 自动保存、复制 Markdown/JSON、下载结果。

## 为什么

- 用户明确说“我一个个进行选择，这样子更方便”；长表格在终端里难逐项勾选。
- 审查报告是**事实与候选方案**，不是授权；用户经常要对不同风险选不同力度，甚至写自定义方案。
- 把归因写清楚（已证实 / 条件性 / 环境因素 / 已修待确认）可以减少把观察当结论、把环境问题归咎补丁的错误。
- 用户刚更正过一次需求（“抱歉我说错了”），这时更要**只生成选择页，不继续执行前面的发版/Manifest动作**。

## 做法

1. 每个问题一个对象：`id / level / title / categories / attribution / evidence[] / options[3..6]`；每个 option 写清 `label + cost`。
2. 第一项可作推荐并显式标注；**推荐不是默认勾选**。
3. 每题都有 `自由输入`，并另设全局备注；未选择的题也要列出来，便于用户说“其他全部不动”。
4. 导出 Markdown/JSON 时包含：`package / generatedAt / globalNote / selectedOptions / freeInput / unselectedIssueIds`。
5. 页面必须本地运行：不联网、不上传、不发布；用 localStorage 保存，脚本语法与导出函数用 Node/vm 做静态验证。
6. 生成前确认上一句被撤回的指令没有残留执行；页面只负责收集选择，不触发代码修改。

关联 [[judgment-correction-is-not-change-authorization]]、[[ask-with-options-early-never-at-end]]。
