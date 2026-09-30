---
name: credential-helper-empty-value-blocks-git-fetch
description: git config 空值 credential.helper 让 fetch 阻塞等待（不是跳过）；gh setup-git 追加不清理产生重复 key；unset-all 误删好条目
type: pitfall
source: agent-guard 2026-09-20 实锤（三轮迭代才收敛：空值阻塞 → 全删 → 另一个 agent 修复好条目）
date: 2026-09-20
verified: 2026-09-20
topic: git, security
---

**经验**：清理 git credential 配置时，⛔ 不能 `unset-all credential.https://<host>.*` 一把梭，⛔ 不能设空字符串 `credential.helper=""`。必须先 `--show-origin --get-all` 列清每个条目的来源和值，**只删空值或明确坏的**。

**Why**：2026-09-20 实锤三轮迭代：
1. 为绕开 credential 冲突，跑 `git config --global credential.helper ""` + `gh auth setup-git` → gh 追加自己的 helper 但**不清空旧 key**，变成多 key：
   `ini
   credential.https://github.com.helper=                                    ← 空值（我设的）
   credential.https://github.com.helper=!'gh.exe' auth git-credential      ← 正确的
   `
   Git 多 helper 按顺序**全部执行**。空值 helper 被调用后**既不返回凭据也不告诉 git"我没有"**，git 永远等待 → fetch 挂住。
2. 发现阻塞后跑 `git config --global --unset-all credential.https://cnb.cool.*` → cnb.cool 的专用 helper（`!cnb.cmd git-credential`，让 cnb 自动 token 鉴权）和 gitee.com 的 provider 也被全清，只剩 system 级 `credential.helper=manager`（Windows GCM）。
3. 另一个 agent 逐条恢复了 cnb.cool 和 gitee.com 的专用条目，fetch 恢复正常。

**How to apply**：
1. 清理前**必先**：`git config --show-origin --get-all credential.helper` 和 `git config --show-origin --get-regexp "^credential\."`——按来源和值决定删哪个。
2. ⛔ `git config --global credential.helper ""` —— 空值 = 阻塞等待，不是"禁用"。禁用 URL 级 helper 要配明确的 `none` 或 `askpass`，或者 unset-all 那个 URL key。
3. `gh auth setup-git` 不是幂等的——它先清再追加，多次调用会产生重复 key。每次运行后检查有没有空值条目。
4. 多远程场景：cnb.cool、gitee.com、github.com 各有专用 helper，URL 级 key（`credential.https://<host>.helper`）优先于 generic `credential.helper`。清理时**按 host 分治**，别用通配 unset。
5. 完整清理单条 key 的安全姿势：`git config --global --unset-all credential.https://<host>.helper`——只清这一项，其他不动。

关联 [[credential-rotation-must-cover-all-entries]]。
