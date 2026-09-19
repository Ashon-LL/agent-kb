# 全局经验库索引（kb）

> 一事实一文件，本索引每次会话按 hook 被扫视。
> 收录标准：**跨项目可复用**。项目专属的记忆留在该项目的 memory 库，不进这里。
> 目录：`tools/` 环境与工具链 · `workflow/` 流程与协作 · `pitfalls/` 失败教训与反模式

## pitfalls/ 教训与反模式

- [不要把临时目录当持久存储](pitfalls/tempdir-not-persistent.md) —— `/tmp` 会被系统清理；跨会话留东西放专门持久目录

## workflow/ 流程与协作

- [任务闭环时主动总结经验](workflow/summarize-on-task-close.md) —— 写完代码别急着走人，花 5 分钟想：换个项目还能用吗？能用就沉淀进 kb

## tools/ 环境与平台

- [CLI 工具名 Windows/macOS 形态不同](tools/cli-name-platform-diff.md) —— npm 装的 CLI 在 Windows 上有 .cmd 扩展名，Python subprocess 直接 `run(["工具名"])` 会 ENOENT

## 条目格式

```markdown
---
name: kebab-case-slug
description: 一句话摘要（检索靠它）
type: tool | workflow | pitfall
source: 来源项目或事件
date: YYYY-MM-DD
---

**经验**：直接说怎么做。
**Why**：（可选）不这样做会怎样。
**How to apply**：（可选）什么场景、如何应用。
```
