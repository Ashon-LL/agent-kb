---
name: fork-sync-force-update-wipes-local-customizations
description: 把 fork 与上游「同步」通常是一次 force update（历史被重写），fork 上的本仓定制行会被**静默覆盖**——同步后必须按清单逐行 grep 复核再补回。实测：apigogo/x 同步 i.o/x 后 `659b146 → 701e038`（+1071 行），三处定制（密钥库 imports / `timeout: 6h` / 3 处回落地址）全部消失，且没有任何报错或提示
type: pitfall
source: MH-Agent-Open（apigogo/x fork 同步上游 i.o/x 后实测；用户 20261009 要求复核「我们自己的设定哪里变了」）
date: 2026-10-09
verified: 2026-10-09
topic: git
---

**经验**：「同步上游」在平台侧是 **force update（重写历史）**，不是 merge。
fork 上所有**本仓定制行**（配置、锚点、超时、地址…）**会被静默覆盖**，没有任何告警——
下次会话照跑，但跑的是被覆盖后的配置。⇒ 每次同步后必须**按清单逐行复核 + 补回**。

## 症状（真实案例）

`apigogo/x`（NPC 框架 fork）同步上游后，main 由 `659b146` → `701e038`（force update，+1071 行）。
本仓三处定制**同时消失**：

| # | 定制 | 复核判据（同步后 grep） |
|---|---|---|
| ① | `.npc` 锚点 `imports: …/apigogo/secret/…/envs.yml`（评论会话密钥注入） | `grep -c 'apigogo/secret' .cnb.yml` = **1 → 0** |
| ② | `npc go` 阶段 `timeout: 6h` | `grep -c 'timeout: 6h'` = **0** |
| ③ | 3 处回落评论地址（曾改为本组织 fork 地址） | 改过的 3 处**回到上游写法** |

⛔ 危险点：**没有报错、没有提示**——`git fetch` 只见 `+ 659b146...701e038 main -> origin/main  (forced update)`；
若只看「构建能不能跑」会以为一切正常（配置被覆盖后照样能跑，只是少了密钥/超时/地址）。

## 对策

1. **定制行必须带「可 grep 的标记」**：本仓做法 = 每处定制行上方写 `# ⛔ <日期> 用户裁定：…` 注释，
   并在仓库文档里维护一张**定制清单**（本项目落在 `docs/dispatch/CNB-DISPATCH-MANUAL.md` §4.6）。
2. **同步后逐项复核**（拿清单跑一遍 grep，与同步前值比对）；缺的**按用户口径补回**（分支 + PR + 合并）。
3. **尽量少定制**：每多一行定制就多一个「同步即丢」的面；能用上游原生的就不改。
4. ⛔ **别把「同步」当无害操作**：它等价于对 fork 的 `reset --hard`（历史级），
   动手前先记录 fork 相对上游的**全部 delta**（`git log --oneline <upstream>..<fork>` 或逐文件 diff）。

## 验证

- 复核命令（本仓实测）：`git cat-file blob <old-main>:.cnb.yml` 与 `git cat-file blob <new-main>:.cnb.yml`
  各跑清单 grep，逐项打表（1→0 即被覆盖）。
- 补回后复验：`yaml.safe_load` 通过 + `git diff --stat` 恰 N 行（防顺手改坏别的）。

## 2026-10-16 后续（**2026-10-23 更正：那条「已删除」是误记**）

⛔ **原文写「`apigogo/x` 已于 2026-10-16 被用户删除、现行入口 = `@i.o/x(中书令)`」——该记录有误**（当时的判断，未实测仓库是否存在）。2026-10-23 用户明确「回归 apigogo/x 那个中书令的模式」并纠正，实测证据：

- `cnb repositories get-by-id --repo apigogo/x` ⇒ **存在**，`flags=NPC`，2026-10-19 重建、10-21 仍在更新；
- `git clone https://cnb.cool/apigogo/x.git` ⇒ `.cnb.yml` 的 `.npc` 锚点带 `imports: apigogo/secret/envs.yml`（我方密钥库）、`.runner-dispatch = cpus 4`；
- **现行派单入口 = `@apigogo/x(中书令)`**（口径见 `docs/dispatch/CNB-DISPATCH-MANUAL.md` §4.6，派单前必须 `get-by-id` 实测入口仓存在）。

⇒ 本 pitfall 的**原理仍完全成立**（fork 同步 = force update、本仓定制会被静默覆盖；凡维护 fork 定制，同步后一律按清单 grep 复核再补回）——2026-10-19 重建后的 apigogo/x 正是带着密钥 imports + 4 核 runner 这些定制回来的。

相关：[[automation-artifacts-lie-existence-and-freshness]]（「看起来还在」不等于「生效」同族）、
[[backlog-records-rot-verify-before-dispatch]]（记录会腐烂：同步后现值以实测为准）。

关联 [[diff-deployed-vs-vcs-before-reimplementing]]、[[git-remote-ownership-check]]。
