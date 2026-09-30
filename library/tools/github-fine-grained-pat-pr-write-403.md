---
name: github-fine-grained-pat-pr-write-403
description: gh pr create / POST .../pulls 在细粒度 PAT 缺 pull requests: write 时返回 403 Resource not accessible；Git Data API 能推 ≠ PR 权限够；两条出路（浏览器会话提交 / 用户加 scope）
type: tool
source: ps-heredoc-todie（mokuyoaxis/PowerShell-Reliability-Framework PR #1，2026-09-21 实测）
date: 2026-09-21
verified: 2026-09-21
topic: git, browser, security
---

**经验**：fork PR 用 `gh pr create` 或 `POST /repos/{owner}/{repo}/pulls` 返回
`403 Resource not accessible by personal access token`——先别怀疑网络或仓库设置，几乎
总是**细粒度 PAT 缺该仓库的 `pull requests: write`**。仓库可见、推送可写都不能推出
"PR 权限够"：Git Data API（blobs/trees/commits/refs）走 `Contents: write` 一档，
PR 创建是**另一个 scope**。

- **诊断签名**：`gh pr create` 报 GraphQL `createPullRequest` 同句 403；REST
  `POST /repos/.../pulls` 也 403 同句；但 `GET /repos/.../pulls`（读）正常 200。
- **两条出路**：① 用户改配置——Settings → Tokens → 该 token → Repository access → 加
  仓库 → Pull requests = Read and write（须用户操作，不能代办）；② 不改配置——用
  **已登录的 GitHub 浏览器会话**走 UI 提交，登录态即身份、不占 token scope
  （compare 页表单填法见 [[github-pr-form-is-a-details-disclosure]]）。
- ⚠️ 用 `--head owner:branch` 时别把 owner 拼错——`GET /pulls` 的 404 会冒充成"仓库
  不存在"；对照浏览器 compare URL 里的真实 owner 段。

**Why**：同一台机子反复撞这句 403 会被误判成网络或仓库权限配置问题，整条提交链路
空转。
**How to apply**：撞到这句 403 → 先 `gh api repos/{o}/{r}/pulls?state=all` 确认读接口
通（区分"权限不足"与"网络/仓库不存在"）→ 再决定走浏览器提交还是请用户加 scope。
