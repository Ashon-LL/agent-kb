---
name: temp-files-must-not-be-added-by-add-all
description: `git add -A` 会把当时还在的临时文件一并提交——「先删再 add」只是治标；根治是把 commit message 文件写到仓库外（如 %TEMP%），让 add 天然碰不到；提交后核对 `git show --stat` 里没有 _tmp 文件
type: pitfall
source: MH-Agent-Open（2026-10-05 实例，已用独立 commit 6e1e7af 移除并留痕）
date: 2026-10-23
verified: 2026-10-05
topic: git, methodology
---

**教训**：`git add -A` 是「把工作区此刻所有东西加进来」，不区分临时文件。

## 事故

为避开 heredoc 吃反引号的坑，commit message 写成文件：

```bash
git add -A && git commit -F _tmp_msg.txt && rm -f _tmp_msg.txt
```

⇒ **add 那一刻 `_tmp_msg.txt` 还在**，被一并提交。违反「不提交临时脚本到仓库」的约定。

## 两条做法

1. **先删临时文件，再 `git add`** —— 顺序换了就对，但仍依赖人记得。
2. ⭐ **commit message 文件写到仓库外**（`%TEMP%` / `$TMPDIR`）——`git add -A` 天然碰不到，
   不依赖记忆。实测后再未复发。

## How to apply

- 任何「生成临时文件 → add -A → commit → 删」的流水线，都把临时文件移出仓库。
- 提交后看一眼 `git show --stat` / `git status`，确认没有 `_tmp`、`.bak`、日志类文件。
- 仓库若允许，配 `.gitignore` 兜底（但不要用它替代顺序纪律）。

关联 [[oneoff-script-file-edit-rules]]、[[ssh-heredoc-delimiter-must-be-quoted]]、
[[regex-cannot-span-nested-braces]]。
