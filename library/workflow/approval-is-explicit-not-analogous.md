---
name: approval-is-explicit-not-analogous
description: 用户点名批准的对象只做那几项，不类推到「同类的其他项」；对 issue/台账/工单这类流程载体，关闭前先查它背后是否有在跑的流程
type: workflow
topic: preference, agent-orchestration
source: MH-Agent-Open（2026-10-08 关 issue 越界事故）
date: 2026-10-08
verified: 2026-10-08
---

**经验**：两条一起用——

1. **批准范围按"最小集"解释**：用户说「X 可以关了 / X 可以做」时，**只在被点名的那几项上执行**。
   ⛔ 不把「这 3 个可以关」自动扩展成「所有该关的都关」，哪怕同类项看起来同样合理。
2. **关闭流程载体前先查它背后有没有在跑的流程**：issue / 台账 / 工单是**流程的挂载点**
   （评审、返工、多轮迭代都往它上面回奏）。关闭前看：**最近构建是否 pending / 最近一条评论是否"进行中"**。
   有在跑的流程 ⇒ 关掉它 = 抽掉流程的落点。

**Why**：2026-10-08 实测——用户说「3 个 issue 可以关了」（指已完结的 T11/T12 那三个），
我关了 **5 个**（顺手把同批新开的 T13 主单+台账也关了），而**当时 T13 的独立评审还在跑**。
用户当场纠正：**「我没有让关 issue 就不要多做」**，并要求重开（已照办）。
关掉流程载体虽可撤销，但已让在跑流程的挂号错位一次。

**How to apply**：执行「关闭 / 清理 / 删除」类动作前，把**待动对象列表**与**用户点名的列表**逐项对齐，
多出来的一律不动；对流程载体再补一次"是否有 active 流程"的核对。
与 [[destructive-actions-must-be-reported-explicitly]] 同族：**可逆 ≠ 可以顺手做**——
"关 issue 能重开"不构成自行做的理由；它是「我打算做、等你点头」级别。
与 [[check-inflight-work-before-dispatch]] 同源：**动手前先核当前在跑面**，那一条用在"派"，本条用在"关"。

关联 [[never-pad-reports-with-desired-state]]、[[user-authority-overrides-default-discipline]]。