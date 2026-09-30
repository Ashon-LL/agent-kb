---
name: github-git-data-api-push-without-git-transport
description: git 传输死/被限时用 GitHub Git Data API 零 git 二进制建分支推提交（blobs→tree(base_tree)→commit(parents)→ref）；递归 tree + 本地 blob SHA1 预验证远端 diff
type: tool
source: ps-heredoc-todie（mokuyoaxis/PowerShell-Reliability-Framework PR #1，2026-09-21 实测）
date: 2026-09-21
---

**经验**：`git fetch/push` 被网络掐死（`Recv failure: Connection was reset`，`--depth 1`、
`HTTP/1.1` 都救不了）而 `api.github.com` 可达时，Git Data API 可**零 git 二进制**建分支推
提交：

1. **构造提交**：`POST /repos/{o}/{r}/git/blobs`（base64 + `encoding: base64`）传变更文件
   → `POST /git/trees` 带 `base_tree` = 当前分支树 SHA（树是快照叠加，只发 delta）→
   `POST /git/commits` 带 `parents: [当前 head]` → ref 不存在用 `POST /git/refs`，已存在
   用 `PATCH /git/refs/heads/{b}`（`force: false`）。
2. **提交前先算远端 diff，别靠猜**：本地 `blob SHA1 = sha1("blob <len>\0" + bytes)`；
   `GET /git/refs/heads/{b}` → commit SHA → `GET /git/commits/{sha}` → tree SHA →
   `GET /git/trees/{sha}?recursive=1` 拿全量路径+SHA1 逐文件比对，得出「哪些与上游字节
   一致、哪些是 delta」；再用 compare API（`ahead_by`、每文件 +/- 行数）交叉验证。
3. ⚠ 踩过的坑：`GET /git/ref/{b}` 是**弃用端点**（返回 commit SHA，别当 tree SHA）；
   不加 `?recursive=1` 只回顶层 12 条、所有文件都像"新增"；`gh api` 输出是字符串，
   取字段必须 `-q`（jq）。变更文件注意行尾：Python 文本模式写盘会 LF→CRLF，撞仓库 LF
   政策把 diff 污染成全文件（见 [[windows-scripting-terminal-gotchas]]）。
4. 权限：Git Data API 走 `Contents: write`——**能推 ≠ 能开 PR**，PR 创建是独立 scope
   （见 [[github-fine-grained-pat-pr-write-403]]）。

**Why**：推送向死路在特定网络反复出现（[[github-china-network-workarounds]]），
Git Data API 是不依赖 git 传输的第二条出路，且自带可复算的 diff 预验证。
**How to apply**：git 传输报 reset/超时 → 先确认 api.github.com 可达 → 按 1 构造提交、
按 2 预验证；开 PR 走已登录浏览器会话（[[github-pr-form-is-a-details-disclosure]]）。
