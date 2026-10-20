---
name: cnb-pipeline-2h-hard-cap
description: CNB 流水线有约 2h 硬性中止，真值是平台注入的 CNB_PIPELINE_MAX_RUN_TIME=7200000（2h 整），与 `.cnb.yml` 的 timeout 声明无关（声明 6h 照样在 2h 被 SIGKILL 137）；取证分两层——prepare 级日志的 maxPipelineRunTime: 2h、runner 日志里的环境变量；api_trigger_npc 固定 2h，issue.comment@npc 档位动态（2h/4h，重发可回 4h）；对策=单命令有界 + 开工即推/增量推送
type: tool
source: MH-Agent-Open 全量构建记录反查（cnb-sdo/cnb-eke 对照）+ 用户 20260919/20261009 实测裁定
date: 2026-09-18
verified: 2026-10-09
topic: cnb, delivery
---

**结论**：CNB 流水线整体受一个**约 2h 的硬性中止**约束，来源是平台注入的环境变量
`CNB_PIPELINE_MAX_RUN_TIME=7200000`（毫秒，= 2h 整）。`.cnb.yml` 里把 `timeout` 写成 4h/6h
**改不了它**（实测声明 6h 仍在 2h 被 SIGKILL）；脚本 Job 同样被掐（20260919 用户反复实测裁定）。

## 两层取证（各查各的日志，别混）

| 位置 | 形态 | 取值 | 取证命令 |
|---|---|---|---|
| prepare stage（pipeline init） | `maxPipelineRunTime: 2h` | 人类可读 | `cnb build get-build-stage --sn <SN> --pipelineId <SN>-001 --stageId prepare`，读 `data.content` |
| runner 容器内（env dump） | `CNB_PIPELINE_MAX_RUN_TIME=7200000` | 毫秒 | `strings <runner日志>.bin \| grep -o 'CNB_PIPELINE_MAX_RUN_TIME=[0-9]*'` |

prepare 原文片段：

```
"Pipeline actual limit cpus: 8, memory: 16","maxPipelineRunTime: 2h","quota size: {...}"
```

⛔ **查错日志层会误判**：只在 runner 日志 grep `maxPipelineRunTime` 会 0 命中，
从而错误以为「字段不存在」。**平台限制声明看 stage/prepare 级；实际进程行为看 runner 级。**

两份不同构建的 runner 日志独立命中同值 `7200000`，与真实被杀时刻
`02:01:03` / `02:01:05` 精确吻合（2h + 数十秒处置延迟）。

## 与 `timeout` 的关系：两条限制并存，不矛盾

- `timeout`（Job 级）：脚本 Job = 任务总时长 + 无输出超时；`npc:go` = **单次工具执行**时长。
  官方允许放宽到 12h，但它**管不到流水线整体**。
- `CNB_PIPELINE_MAX_RUN_TIME`：约束**流水线整体**，本仓无法通过 `.cnb.yml` 改。
  `npc:go` 与脚本 Job 都是它先到顶。

⇒ 见 [[same-config-key-different-semantics-per-step-type]]（同一字段在不同步骤类型的语义差异）。

## 不同类型/入口的档位

- **`api_trigger_npc`（派单子单）= 固定 2h 硬顶**：声明更长 timeout 无效（实测 6h 照样 137）。
  ⇒ 子单只做短平快（建议 ≤~1.5h 能收口），长跑塞子单会白做。
- **`issue.comment@npc`（评论会话）= 档位动态**，不是定死 2h：同仓相隔 3 分钟两个样本分别取到
  `2h` 与 `4h`（20261009 实取 Prepare 日志）；官方原文「为防止滥用，集群可能会对最大时长进行动态管控，
  以实际管控为准」。⇒ 拿到差档就**停掉重发**（实测重发即回到 4h）；生效与否只看新会话的 Prepare 日志。

## 已证伪：「2h 被杀是无输出超时」

失败单日志 `[00:08:10]` 最后一条有输出，`[02:01:05 +1.9h]` 才被 137——中间静默 1.9h。
若真是 10min 无输出超时，`[00:18:10]` 前后就该被回收。平台日志 grep
`no output` / `无输出` / `idle timeout` 均 0 命中 ⇒ 判据是**总时长**，不是无输出。

## 对策（边界不可配时的唯一可靠手段）

1. 单条命令永不无限等待：禁裸 `wait`、整段 `timeout -k`、`trap ... EXIT` 释放常驻进程、
   单条命令 ≤5min、常驻进程重定向不继承 stdout。
2. **开工即推 + 增量推送**：已推的能留下，没推的随容器销毁全部丢失。
3. 不要在注释/文档里用「官方 20h/12h」去反驳实测的 2h——文档是标称，注入的环境变量才是真相。

**How to apply**：设计任何 CNB 长任务前，先假设墙钟上限 2h；把任务切成 ≤1.5h 可收口的段，
并把「有界命令 + 增量推送」写进任务书。

关联 [[same-config-key-different-semantics-per-step-type]]、
[[success-status-is-not-no-abort-evidence]]、[[binary-error-text-needs-branch-evidence]]、
[[bare-wait-deadlocks-on-long-lived-children]]。
