---
name: dynamic-workflow-agent-identity-and-gates
description: ZCode 动态工作流三个实测坑——循环内建同名子代理必炸 DuplicateActorName（3h/112M tokens 整跑中止）、门禁顺序必须让"闸的拦截对象"在过闸前清空、子代理自述不算门禁必须主代理亲跑复算
type: pitfall
source: MH-Agent-Open 20260925~26 实弹（dwfrun-73349ee4 / 3h01m / 112.1M tokens 中止后主代理接手）
date: 2026-09-26
verified: 2026-09-26
---

## ⛔ 坑 1：`agent(name)` 建在 for 循环里 ⇒ 第二轮必炸 DuplicateActorName

门禁重试循环（`for round in 1..N`）里写 `agent("验收员", {...})` 时，第二轮会同名复用：

```
DuplicateActorName: Subagent name "视觉与玻璃验收员" is used twice in this run
(actor#5@1 and actor#5@2). A named subagent is the identity an amended re-run
matches its cache by, so names must be unique.
```

**代价不是重跑一轮，是整跑中止**：MH-Agent-Open 那次跑到 3h01m / 112.1M tokens、
32/32 steps 已 settled（构建与全量测试都过了）时，在「阶段 6→7 之间」被这一个
异常打死，交付阶段根本没开始。**代码本身没问题**——纯脚本缺陷。

**为什么名字必须是身份**：动态工作流用「命名子代理」当 cache key（`AmendWorkflow`
按名字沿会话前缀导入已完成的工作）。同名 = 身份冲突，引擎只能拒绝。

**做法**：
- 循环内要建的子代理，名字带上轮次/用途：`agent(\`验收员-r${round}\`, ...)`；
- 或者**建到循环外**（同一子代理多轮 `ask()` 是允许的，名字只在创建时占坑）；
- 或干脆匿名（`agent({...})`，但那样就没有跨 run 的缓存身份了）。

## ⛔ 坑 2：门禁顺序必须让「闸的拦截对象」在过闸前清空

同一跑里连撞两次的另一个根因：`sync_to_install.py` 的 preflight 会因为存在
**任何 active 状态的工作流**（`ACTIVE_STATES = {pending, running, waiting, paused}`）
而拒绝同步——而为了视觉/性能取证专门铺的**种子工作流**恰好就是 `pending`。

正确顺序（修正后实测一次过）：
```
构建 → 全量测试 → 铺种子 → 视觉验收（静态服务/路由拦截新构建，**不经安装区**）
     → 清种子（此刻 0 active）→ 同步安装区 → 性能探针
```
关键：**取证不必碰安装区**。用 playwright 路由拦截把 `frontend/dist` 当站点、
`/api/*` 放行真实后端即可——既绕开闸门，也让「被验的构建」明确可控。

## ⛔ 坑 3：子代理自述 ≠ 门禁，判定必须主代理亲跑复算

子代理的总结里写着「覆盖全过 / 不浊不灰通过」，但主代理复算时发现：
- 那份 `glass_after.json` 早于最后一次源码改动（时间戳对不上）⇒ 对终版**不成立**；
- 对比度一项子代理判 `contrastPass:false`，主代理逐项复算才发现其中一项
  **是子代理自己的采样假象**（见下条），另外 6 项是真失败且已被后续修复。

**做法**：终态门禁由主代理亲自跑一遍可复算脚本，并**核对取证数据的时间戳
与所验构建的 mtime**。子代理的结论只当线索，不当结论。

## 附：一个真实的「测量假象」形态（值得单独记住）

判按钮文字对比度时，若背景取「元素矩形内像素中位数」，**文字像素会污染中位数**：
同一枚 `.btn-primary` 在 `/skills` 页读出 3.55（FAIL）、`/workflows` 读出 5.40（PASS），
而两页的**计算样式逐位相同**（`rgba(91,141,239,.86)` on `rgb(5,10,20)` = 5.41）。

**做法**：半透明填充的对比度用**解析法**算 —— `getComputedStyle` 取 `background-color`
与 alpha，再在**元素紧邻外侧**采样真实底（避开文字像素），按 alpha 合成后算 WCAG 比。
纯色实底直接用它自己的 fill 值。

**How to apply**：写动态工作流时先把「循环内建 agent」和「门禁过闸顺序」两处审一遍；
把门禁脚本设计成主代理可直接复跑且**自带时间戳/构建指纹**；任何对比度/像素类判定，
先问「我的采样区里有没有会污染判定的东西」。

相关：[[automation-artifacts-lie-existence-and-freshness]]、[[defect-localization-methodology]]、
[[subagent-orchestration-lessons]]、[[zcode-platform-verified-facts]]
