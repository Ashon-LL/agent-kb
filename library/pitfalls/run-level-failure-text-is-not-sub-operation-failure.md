---
name: run-level-failure-text-is-not-sub-operation-failure
description: 外层（run/会话）级失败文案 ≠ 内层子操作失败；带重试/配额的自愈机制要逐层核对 attempt 级结算（succeeded/exhausted）再下"机制失效"结论
type: pitfall
source: mh-agent-open（T19 取证报告误读 → T20 源码+日志逐行证伪）
date: 2026-10-12
verified: 2026-10-12
topic: methodology
---

**经验**：判定"压缩/重试/降级这类自愈机制彻底失效"前，把每一层的结算记录**分开**核对：
子操作/attempt 级（如 `attempt 1/3 … succeeded`）→ 会话/run 级（`failed` / `exhausted` / `blocked`）。
外层文案常是**聚合结果**——实测案例：同一日志里 3 次 auto-compaction **全部 succeeded**，
而 `Auto-compaction failed (…)` 只是 **run 级**失败分支的文案（`isCompactionFailure`）；
真正 blocked 的真因是"同一 run 内第 4 次溢出时配额已满（`overflowCompactionAttempts >= 3`）"——
**与单次溢出大小无关**（超 392 tokens 的第 4 次照样 blocked）。

**Why**：把聚合文案当归因，会写出错误报告和错误修法。该误读曾被我写进 T19 取证报告
（"压缩请求本身被拒"，暗示产品侧要改压缩策略），T20 逐行核对后证伪——机制全程正常工作，
产品侧唯一正确的动作是"什么都不改"。错误归因还会写进下游台账，污染后续所有决策。

**How to apply**：排障 / 写取证报告时——① 先画层（机制 → run/会话 → 子操作 → attempt）；
② 逐层找**该层自己的**结算键（attempt k/N、retrying、exhausted、配额计数）；
③ "机制失效 / 死区"类结论只能落在**最内层操作**的记录上；
④ 重置语义（成功后是否重置、新 run 是否归零）必须单独验证——配额上限的真实含义
常是"每次 run 的预算"而非"终身额度"，两种语义下故障面完全不同。
相关：[[log-text-is-not-spec-read-emitting-code]]、[[stated-provenance-needs-evidence-and-conditions]]

关联 [[config-load-failure-check-file-refs-and-schema]]、[[injected-ui-feature-failure-check-credential-plumbing-first]]、[[multi-line-log-attribution-use-baseurl-not-model]]、[[model-capability-verdict-needs-official-docs-not-probes]]、[[no-assertion-without-measurement]]。
