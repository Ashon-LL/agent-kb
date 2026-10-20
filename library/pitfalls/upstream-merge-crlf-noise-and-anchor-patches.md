---
name: upstream-merge-crlf-noise-and-anchor-patches
description: 合并上游新版本时整文件级 diff 多为行尾噪声（上游常是 CRLF）——先 git diff --ignore-cr-at-eol 判真伪；合并后归一 LF 再重跑锚点型补丁脚本；补丁脚本自身写盘也要 newline="
"
type: pitfall
source: APIShow Trae v1.0.5 升级（2026-10-15）：上游 main.py 带 11820 个 CR，working copy 是 LF
date: 2026-10-15
verified: 2026-10-15
topic: git
---

**经验**：三步。

1. **判真伪**：合并前跑 `git diff --ignore-cr-at-eol --stat`；若忽略 CR 后 diff 从"整文件"缩到几十行，
   多出来的全是 CRLF 噪声（本次 Trae 上游 `main.py` 有 11820 个 CR、我方可执行副本是 LF）。
2. **归一**：合并/检出后先把待打补丁的文件归一 LF（`raw.replace(b"
", b"
")`），**再**跑锚点型
   补丁脚本——锚点以 `
` 书写而目标为 `
` 时全数失配。
3. **挑单点**：落后的 fork 用 `git apply --3way <commit.patch>` 按 SHA 挑 fix，不整体升；报
   "does not exist in index" 说明该文件在旧树没有对应版本 ⇒ 手工同语义落实，改完用符号检查验收。

**Why**：行尾噪声会让人误判"上游改了一整个文件"，也让补丁锚点静默失效（返回"锚点命中 0 次"时才暴露）；
本次还发现补丁脚本自身若把含 CRLF 的字符串常量写盘，会把 CRLF 污染进目标文件——写盘一律
`open(..., newline="
")`。

**How to apply**：升级流程固定为「备份 → 存自有补丁（`--ignore-cr-at-eol`）→ merge/checkout → 归一 LF →
重跑补丁脚本（锚点必须全中）→ 重建/部署 → e2e」；挑完单点回查自有补丁是否还在（逐文件 git status）。

相关：[[oneoff-script-file-edit-rules]]、[[container-image-source-patches-need-replay-script]]、[[read-upstream-specs-before-probing]]。

关联 [[vite-build-output-names-track-source-eol]]。
