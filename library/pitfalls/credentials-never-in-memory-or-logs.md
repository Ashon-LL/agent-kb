---
name: credentials-never-in-memory-or-logs
description: 凭据原文不进记忆/kb/日志——只记取值位置不记取值，装凭据走管道不 echo
type: pitfall
topic: security
source: apishow
date: 2026-10-03
verified: 2026-10-03
---

**经验**：凭据原文不进记忆文件/kb 条目/会话内新建的任何文件/任何被跟踪文件。真值只允许落在两处：① 平台凭据库（Windows 凭据管理器/keyring）② `.local_secrets/`（仓库内已 gitignore）。需要"记住凭据相关事实"时写脱敏占位符+取值指针。

**Why**：把完整 PAT 明文写进记忆文件，用户要求"从上下文删除"时才发现。记忆/日志里的凭据副本既不会被 gitignore 覆盖也不会随凭据轮换自动清理。脱敏时用前缀正则整体替换（如 `github_pat_[A-Za-z0-9_]+`），别只遮尾巴。

**How to apply**：装凭据走管道不 echo（`printf '%s\n' '<token>' | gh auth login --with-token`），日志/exec/artifacts 天然零明文。任何"把这个凭据记下来"的冲动出现时先问：我记的是取值位置还是取值本身？位置才是持久信息，真值不是。
