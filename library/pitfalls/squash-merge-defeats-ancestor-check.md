---
name: squash-merge-defeats-ancestor-check
description: 判「提交是否已进主线」不能用 `git merge-base --is-ancestor`——squash 合并后原 SHA 不在历史里，祖先判据恒假；正确判据是 PR 的 `state: closed` + `mergeable_state: merged`；也不能用 `git ls-remote | grep refs/pull`（累积 ref 必误判）
type: pitfall
source: MH-Agent-Open（2026-10-06 监看 ArHub 批次1，用户指出「还有东西在构建中」）
date: 2026-10-23
verified: 2026-10-06
topic: git, cnb
---

**教训**：squash 合并会重写提交，原 SHA 不会出现在主线历史里。用「祖先关系」判合入，结果恒假。

## 三次错判（同一批次）

1. **`git merge-base --is-ancestor <sha> origin/feat`** ⇒ 报「T1~T5 未在 feat」，
   实际内容早已合入（PR `mergeable_state: merged`）。
2. **`git ls-remote | grep refs/pull`** ⇒ 数的是累积的全部 pull ref（实测 160 条），
   既非本单、也非 open 态。
3. **只盯已知构建单** ⇒ 漏掉额外派的 FINAL 册，用户当场指出「你没有看完整的 CNB 状态」。

## 正确判据

- **PR 状态**：`cnb pulls list-pulls --repo <org/repo>`，核对 `state: closed` +
  `mergeable_state: merged`（或 `is_merged`）；不要只看 `state: open`。
- **监看全量**：每轮跑 `cnb build get-build-logs --page-size 40`，先列全量再筛非终态，
  不要只盯自己派出去的单。
- **分支删除**：合并后再确认「分支是否有独有提交」（NPC 常在合并后补推报告），
  有实质内容先 cherry-pick 再删。

## How to apply

任何「这个改动到底进没进主线」的问题，先查 PR 合并态；git 祖先只适用于 merge commit，
不适用于 squash/rebase 合并。监看批次时以全量构建列表为准。

关联 [[cnb-npc-dispatch-essentials]]、[[cnb-quota-runner-cli-notes]]、
[[success-status-is-not-no-abort-evidence]]、[[git-remote-ownership-check]]。
