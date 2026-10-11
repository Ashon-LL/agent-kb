---
name: git-bash-ampersand-breaks-gh-auth-login
description: 在 ZCode/bash 里 `gh auth login --with-token <token>` 被 `&` 当后台执行符，token 被拆散报「accepts 0 arg(s), received 1」；正解是管道进 stdin
type: tool
source: 本机 2026-10-02 gh 重新登录实测
date: 2026-10-02
verified: 2026-10-02
topic: git
---

# `gh auth login --with-token` 不接受行内参数（Git Bash 陷阱）

## 症状

```
gh auth login --with-token github_pat_11CFA...
accepts 0 arg(s), received 1
```

看着像 gh 版本/参数不认，**其实是 shell 把命令拆了**：`&` 在 Git Bash 里是后台执行符，
token 里的 `&`（Fine-grained PAT 常见）被当成 job 分隔符，gh 实际收到的参数全乱。

## How to apply

用管道把 token 送进 stdin，**不作为命令行参数**：

```bash
printf '%s\n' '<token>' | gh auth login --hostname github.com --with-token
```

或 `echo '<token>' | gh auth login --with-token`。验证：`gh auth status` + `gh api user --jq .login`。

## 顺带

- **Fine-grained PAT 全选 Account permissions（Metadata 不可取消）就等于「完全权限」**，
  且**不含删除仓库的 API 权限**——删库只能走网页 Settings → Danger Zone 输名字二次确认。
  「完全权限但删不了库」这个组合 GitHub 侧天然成立，不用额外收紧。
- 权限建议 **All repositories**（单账号多项目通用），Expiration 给 1 年（90 天上限太短）。
- token 已在对话里出现过就该 revoke 重发。
- 记 token 用 `gh auth login` 存进 keyring，别让 token 明文留在项目目录。

关联 [[shell-init-files-are-layered-not-one]]、[[ssh-heredoc-delimiter-must-be-quoted]]。