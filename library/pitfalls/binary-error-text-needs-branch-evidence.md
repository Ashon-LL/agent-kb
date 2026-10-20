---
name: binary-error-text-needs-branch-evidence
description: 「A，或 B」式错误文案不能挑自己顺眼的分支当结论；CNB 的「构建环境异常终止，或流水线超过最大运行时长(2h)」必须靠终点可观测物取证落在哪支（容器 No such container / exit 137 / 被杀时刻）；文案里的数字不等于配置来源，也不等于上限来源
type: pitfall
source: MH-Agent-Open cnb-eke 构建日志（第一次误读为「超时」）
date: 2026-09-18
verified: 2026-09-18
topic: diagnosis, cnb
---

**教训**：最终错误文案把两个原因用「或」并列时，它只是一份**候选清单**，不是结论。

## 实例

CNB 的中止文案：

> `Agent aborted: the build environment terminated unexpectedly,`
> `or the pipeline exceeded its max run time (2h).`

第一次直接读成「超时（2h）」。但终点证据（被杀后 `Error response from daemon: No such container`
⇒ 容器已销毁）指向的是**前一个分支**（构建环境异常终止）。两者在文案里权重相同，靠猜必错一半。

## 正确姿势

1. 先列出文案给的每个候选分支。
2. 为每个分支找**终点可观测物**（不是文案本身）：
   - 超时分支 → 被杀时刻、`exit 137`、平台注入的时长变量；
   - 异常终止分支 → 容器是否存在、daemon 报错、进程信号。
3. 文案里的数字（如 2h）不要直接当「上限来源」或「配置来源」——
   它可能只是模板里的标称值。真值去 prepare 日志/环境变量里取。

**How to apply**：看到「A，或 B」式失败文案，先取证再归因；归因结论要能指出落在哪一支的证据。
⛔ 同一段文案同时出现在多条失败单时，更要逐单核对，别用一条的解释套全部。

关联 [[cnb-pipeline-2h-hard-cap]]、[[success-status-is-not-no-abort-evidence]]、
[[log-text-is-not-spec-read-emitting-code]]、[[defect-localization-methodology]]。
