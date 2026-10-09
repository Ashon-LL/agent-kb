---
name: check-inflight-work-before-dispatch
description: 派单/派活前先查「是否已有在跑的同题工作」（开放 PR / 远端分支 / 最近构建三查）——不查就把同一件事派了两遍，本仓实测一次
type: workflow
topic: agent-orchestration, cnb
source: MH-Agent-Open（2026-10-08 T14 重复派单事故）
date: 2026-10-08
verified: 2026-10-08
---

**经验**：发起「派单 / 开 issue / 写任务书」之前，先跑**三查**确认没人正在做同一件事：

```bash
cnb pulls list-pulls --repo <owner>/<repo> --state all   # ① 开放 PR 里有没有同题
git ls-remote --heads origin                             # ② 远端分支里有没有同题
cnb build get-build-logs --repo <owner>/<repo> --page-size 8  # ③ 最近构建标题里有没有同题
```

三查任一命中 ⇒ **不要派**；改为「给在跑的那支补充信息 / 收窄它的范围」。

**Why**：2026-10-08 实测——派单方基于「自己记的 follow-up 待办」派了 T14（工具面计数 35→37 订正），
而执行方（NPC）**早已开 PR #164 在做同一件事**，且已过评审。结果两支都做了同一段改动：
派单方须收窄 T14 范围、force-update 分支、补发范围说明评论，纯属重复劳动 + 制造合并面。
根因：只核对了「我记的待办」（历史面），没核对「别人正在做什么」（当前面）。

**How to apply**：任何派单动作前跑三查，**和"读自己台账"同等重要**。发现重叠时的优先级：
① 让在跑的那支继续（它的上下文最全）；② 把新发现**收窄成差集**补给在跑的那支；
③ ⛔ 不要停掉在跑的重派（丢上下文、白烧已完成的量）。
与 [[backlog-records-rot-verify-before-dispatch]] 互补——**那条查「历史是否已做」（记录会腐烂），
本条查「当前是否有人在做」（在跑的工作不在你的记录里）**；两条合起来 = 派单前的两个核对面。
与 [[two-agent-iteration-via-dispatch-board]] 同族：派活板是异步档案，**不实时反映在跑状态** ⇒ 板子之外还要查在跑面。
