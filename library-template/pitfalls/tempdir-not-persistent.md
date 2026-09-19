---
name: tempdir-not-persistent
description: /tmp 会被系统清理，跨会话留东西放专门持久目录
type: pitfall
source: 首次搭建 agent-kb 时踩坑
date: 2026-09-20
---

**经验**：`/tmp` 下的文件不要指望能留到明天。Windows 用 `%TEMP%`、macOS/Linux 用 `/tmp`，两者都可能被系统定期清理或在重启后消失。

**Why**：临时目录的语义就是"用完就扔"。把 kb 库或配置写进临时目录，下次会话就找不到了。

**How to apply**：所有需要跨会话保留的内容，统一放在 `~/.agents/` 或 `~/.config/` 这类专门的持久目录下。
