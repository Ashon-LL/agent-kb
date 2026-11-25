---
name: git-history-sync-traps
description: squash 合并破坏祖先判据、fork force 同步覆盖定制、上游 CRLF 噪声与锚点补丁
type: pitfall
source: 合并自 squash-merge-defeats-ancestor-check, fork-sync-force-update-wipes-local-customizations, upstream-merge-crlf-noise-and-anchor-patches；MH-Agent-Open（2026-10-06 监看 ArHub 批次1，用户指出「还有东西在构建中」）; MH-Agent-Open（apigogo/x fork 同步上游 i.o/x 后实测；用户 20261009 要求复核「我们自己的设定哪里变了」）; APIShow Trae v1.0.5 升级（2026-10-15）：上游 main.py 带 11820 个 CR，working copy 是 LF
date: 2026-10-09
verified: 2026-10-15
topic: git, cnb
---
**经验**：squash 合并破坏祖先判据、fork force 同步覆盖定制、上游 CRLF 噪声与锚点补丁

> 本条由 3 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## squash-merge-defeats-ancestor-check

**教训**：squash 合并会重写提交，原 SHA 不会出现在主线历史里。用「祖先关系」判合入，结果恒假。

### 三次错判（同一批次）

1. **`git merge-base --is-ancestor <sha> origin/feat`** ⇒ 报「T1~T5 未在 feat」，
   实际内容早已合入（PR `mergeable_state: merged`）。
2. **`git ls-remote | grep refs/pull`** ⇒ 数的是累积的全部 pull ref（实测 160 条），
   既非本单、也非 open 态。
3. **只盯已知构建单** ⇒ 漏掉额外派的 FINAL 册，用户当场指出「你没有看完整的 CNB 状态」。

### 正确判据

- **PR 状态**：`cnb pulls list-pulls --repo <org/repo>`，核对 `state: closed` +
  `mergeable_state: merged`（或 `is_merged`）；不要只看 `state: open`。
- **监看全量**：每轮跑 `cnb build get-build-logs --page-size 40`，先列全量再筛非终态，
  不要只盯自己派出去的单。
- **分支删除**：合并后再确认「分支是否有独有提交」（NPC 常在合并后补推报告），
  有实质内容先 cherry-pick 再删。

### How to apply

任何「这个改动到底进没进主线」的问题，先查 PR 合并态；git 祖先只适用于 merge commit，
不适用于 squash/rebase 合并。监看批次时以全量构建列表为准。

关联 [[cnb-npc-dispatch-essentials]]、[[cnb-quota-runner-cli-notes]]、
[[success-status-is-not-no-abort-evidence]]、[[git-remote-ownership-check]]。

## fork-sync-force-update-wipes-local-customizations

**经验**：「同步上游」在平台侧是 **force update（重写历史）**，不是 merge。
fork 上所有**本仓定制行**（配置、锚点、超时、地址…）**会被静默覆盖**，没有任何告警——
下次会话照跑，但跑的是被覆盖后的配置。⇒ 每次同步后必须**按清单逐行复核 + 补回**。

### 症状（真实案例）

`apigogo/x`（NPC 框架 fork）同步上游后，main 由 `659b146` → `701e038`（force update，+1071 行）。
本仓三处定制**同时消失**：

| # | 定制 | 复核判据（同步后 grep） |
|---|---|---|
| ① | `.npc` 锚点 `imports: …/apigogo/secret/…/envs.yml`（评论会话密钥注入） | `grep -c 'apigogo/secret' .cnb.yml` = **1 → 0** |
| ② | `npc go` 阶段 `timeout: 6h` | `grep -c 'timeout: 6h'` = **0** |
| ③ | 3 处回落评论地址（曾改为本组织 fork 地址） | 改过的 3 处**回到上游写法** |

⛔ 危险点：**没有报错、没有提示**——`git fetch` 只见 `+ 659b146...701e038 main -> origin/main  (forced update)`；
若只看「构建能不能跑」会以为一切正常（配置被覆盖后照样能跑，只是少了密钥/超时/地址）。

### 对策

1. **定制行必须带「可 grep 的标记」**：本仓做法 = 每处定制行上方写 `# ⛔ <日期> 用户裁定：…` 注释，
   并在仓库文档里维护一张**定制清单**（本项目落在 `docs/dispatch/CNB-DISPATCH-MANUAL.md` §4.6）。
2. **同步后逐项复核**（拿清单跑一遍 grep，与同步前值比对）；缺的**按用户口径补回**（分支 + PR + 合并）。
3. **尽量少定制**：每多一行定制就多一个「同步即丢」的面；能用上游原生的就不改。
4. ⛔ **别把「同步」当无害操作**：它等价于对 fork 的 `reset --hard`（历史级），
   动手前先记录 fork 相对上游的**全部 delta**（`git log --oneline <upstream>..<fork>` 或逐文件 diff）。

### 验证

- 复核命令（本仓实测）：`git cat-file blob <old-main>:.cnb.yml` 与 `git cat-file blob <new-main>:.cnb.yml`
  各跑清单 grep，逐项打表（1→0 即被覆盖）。
- 补回后复验：`yaml.safe_load` 通过 + `git diff --stat` 恰 N 行（防顺手改坏别的）。

### 2026-10-16 后续（**2026-10-23 更正：那条「已删除」是误记**）

⛔ **原文写「`apigogo/x` 已于 2026-10-16 被用户删除、现行入口 = `@i.o/x(中书令)`」——该记录有误**（当时的判断，未实测仓库是否存在）。2026-10-23 用户明确「回归 apigogo/x 那个中书令的模式」并纠正，实测证据：

- `cnb repositories get-by-id --repo apigogo/x` ⇒ **存在**，`flags=NPC`，2026-10-19 重建、10-21 仍在更新；
- `git clone https://cnb.cool/apigogo/x.git` ⇒ `.cnb.yml` 的 `.npc` 锚点带 `imports: apigogo/secret/envs.yml`（我方密钥库）、`.runner-dispatch = cpus 4`；
- **现行派单入口 = `@apigogo/x(中书令)`**（口径见 `docs/dispatch/CNB-DISPATCH-MANUAL.md` §4.6，派单前必须 `get-by-id` 实测入口仓存在）。

⇒ 本 pitfall 的**原理仍完全成立**（fork 同步 = force update、本仓定制会被静默覆盖；凡维护 fork 定制，同步后一律按清单 grep 复核再补回）——2026-10-19 重建后的 apigogo/x 正是带着密钥 imports + 4 核 runner 这些定制回来的。

相关：[[automation-artifacts-lie-existence-and-freshness]]（「看起来还在」不等于「生效」同族）、
[[backlog-records-rot-verify-before-dispatch]]（记录会腐烂：同步后现值以实测为准）。

关联 [[diff-deployed-vs-vcs-before-reimplementing]]、[[git-remote-ownership-check]]。

## upstream-merge-crlf-noise-and-anchor-patches

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
