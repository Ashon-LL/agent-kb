---
name: split-large-component-by-dependency-density
description: 拆巨石组件前先按「行数 × 模板引用的外部符号数」给每块打分——依赖密度高＝业务内聚，不该拆；拆完总行数不降（新增 props/emit 管道）就是净负收益；动手前先确认 git status 只有这一轮改动，回退才干净
type: pitfall
source: MH-Agent-Open（Settings.vue 1928 行 / 6 pane 拆分实测，2026-10-05）
date: 2026-10-23
verified: 2026-10-05
topic: methodology
---

**教训**：把一个巨石组件拆成 N 个子组件前，先给每个待拆块算两个数——**行数**和**模板引用的外部符号数**。
依赖密度高 = 业务内聚 = 不该拆。

## 实测（Settings.vue，1928 行，6 个 pane）

| pane | 行数 | 依赖符号 | 结论 |
|---|---|---|---|
| cap | 26 | 3 | 先拆它 |
| model | 160 | 41 | 过重 |
| run | 321 | 28 | 过重 |
| bot | 93 | 22（10 个是有状态的异步动作） | 过重 |
| env | 72 | 19 | 过重 |
| behav | 81 | 10 | 尚可 |

先拆了依赖最少的 `cap`：构建过、88 条守卫全绿，看起来成功。但**总账是 1918 + 51 = 1969 行，比拆前的 1929 还多 40 行**，可读性提升近乎为零。
`bot` 拆出去要传 22 个 prop + 20 个 emit——**代码总量不降，只是把「一个大耦合」换成「一个小耦合 + 一堆管道」**。
最终 `git checkout` 回退整次拆分。

## How to apply

1. 拆前逐块列出（行数、外部符号数）；符号数明显高于行数/20 的块列为「不拆」。
2. 拆完对比总行数与 props/emit 数：总量不降就回退，别拿「构建绿」当成功。
3. 回退前先 `git status` 确认工作区只有这一轮改动，否则 checkout 会误伤。
4. 真正值得拆的是「依赖少 + 行数多」的块；高依赖块应保持内聚，最多做内部函数级整理。

关联 [[dont-open-frontline-for-edge-features]]、[[minimal-change-and-no-scope-creep]]、
[[user-list-to-plan-must-diff-each-item]]。
