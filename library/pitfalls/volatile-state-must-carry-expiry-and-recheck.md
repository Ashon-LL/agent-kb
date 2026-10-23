---
name: volatile-state-must-carry-expiry-and-recheck
description: 通用原理与项目级易变状态必须分层——原理留正文，状态句写成 `⏰ 时效状态（日期，未复核）`+`⚠️ 用前必须实测：<命令>`；写「已删除/已失效/现行=」必须带实测证据与失效条件（删除后重建是常态）；状态句被复制到手册与 kb 多处会放大成「真理」；含状态的条目 description 必须提状态主题，否则检索摸不到
type: pitfall
source: MH-Agent-Open 派单入口误记（2026-10-16 写「apigogo/x 已删、入口=@i.o/x」，10-19 仓库重建，10-23 照旧记录误派单，用户纠正）
date: 2026-10-23
verified: 2026-10-23
topic: verification, methodology
---

**教训**：经验库里的「事实」分两类——**原理**（不随时间变）和**状态**（某仓/某地址/某版本此刻是否存在）。
两类混写在同一条目里，状态一过期，整条经验就成了定时炸弹。

## 事故时间线（真实案例）

| 时间 | 事件 |
|---|---|
| 2026-10-16 | 手册记录「入口 = `@apigogo/x`」；当天该 fork 确实不在（判断未实测） |
| 2026-10-17 | 任务书批量改成「fork 已删 · 入口 = `@i.o/x`」，给 10 篇历史文档加失效注脚 |
| 2026-10-19 | **`apigogo/x` 被重建**（带密钥 imports + 4 核 runner） |
| 2026-10-20 | 该状态被搬进 kb 条目正文尾部（通用 pitfall 里挂项目级状态） |
| 2026-10-23 | 照「已删」口径派单失败，用户纠正「回归 apigogo/x(中书令)」 |

根因不是「写错」：改写时仓可能真不在。错在**写了一个有时效的状态，却没标时效、也没给复核方法**；
然后这个状态被复制到手册 + 知识库两处，**复制面越大越像真理**。

## 五条规则

1. **原理与状态分层**：通用 pitfall 只留原理；项目级易变状态单独放，
   或至少用显式状态块包起来：

   ```
   > ⏰ 时效状态（2026-10-16 记录，**未复核**）：apigogo/x 已删除、入口=@i.o/x
   > ⚠️ 用前必须实测：cnb repositories get-by-id --repo apigogo/x
   ```

2. **否定结论必须带实测证据**：写「不存在/已删除/已失效」要给命令 + 输出 + 时间点
   （见 [[stated-provenance-needs-evidence-and-conditions]]：事实/推断/未见记录三档）。
   没有证据的否定结论不许进库。

3. **状态句必须写失效条件 + 复核命令**：不是「fork 已删」，而是
   「fork 于 10-16 不在（当时实测）；若重建则此状态失效，复核 = `get-by-id`」。
   任何否定式状态都要自带**复活路径**——仓/分支/配置被删后重建是常态。

4. **description 要覆盖状态主题**：若条目含派单入口、服务地址、版本可用性等状态，
   description 必须带上该主题词；否则状态埋在正文第 N 行，检索永远摸不到
   （本次「派单/入口/NPC」类查询全都没命中）。

5. **定期体检逐条实测**：见 `VERIFICATION-BACKLOG.md` 的「时效状态体检」；
   `python kb_validate.py --audit-volatile` 列出所有含状态词的条目，
   逐条核实现行状态——不能只查 schema 与索引。

## How to apply

- 写条目时先问：这句一年后还成立吗？不成立的就是状态，按 ⏰ 块写。
- 引用他处状态时先实测再抄；抄来时保留「记录日期 + 未复核」标记。
- 改状态时同步所有副本（手册、kb、团队记忆），并注明改动依据与时间。
- 校验器会对「含时效状态句但无 ⏰/复核命令」的条目给 `[volatile]` 提示。

关联 [[stated-provenance-needs-evidence-and-conditions]]、
[[fork-sync-force-update-wipes-local-customizations]]、[[cnb-npc-dispatch-essentials]]、
[[backlog-records-rot-verify-before-dispatch]]、
[[automation-artifacts-lie-existence-and-freshness]]、[[kb-search-miss-is-not-kb-empty]]。
