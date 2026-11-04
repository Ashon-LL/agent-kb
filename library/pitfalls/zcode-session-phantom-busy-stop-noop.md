---
name: zcode-session-phantom-busy-stop-noop
description: 【作用域=ZCode Desktop】会话"假卡死"：按停止无效、发消息无响应。日志特征 v4.stop.foreground_execution_inspected 连发且 runtimeStopKind=idle 而 expectedForegroundExecutionId 不变；为客户端幻忙（运行时已空闲仍等旧前台执行）。过去常伴 database is locked 失败链。恢复=关该会话窗口即可，数据无损。
type: pitfall
source: 解崩会话 sess_6285da1c（zcode改造项目，2026-11-02）
date: 2026-11-02
verified: 2026-11-02
topic: zcode
---

# ZCode 会话幻忙卡死（停止无效/消息无响应）

## 经验
症状：某个会话一直像在忙，按停止没反应，发新消息石沉大海；但同机其他会话正常。

诊断（读 `~/.zcode/cli/log/zcode-YYYY-MM-DD.jsonl`，**时间戳是 UTC，本地 = UTC+8**）：
1. grep 该 `sessionId`：若 `v4.stop.foreground_execution_inspected` 连发、`runtimeStopKind:"idle"`、`expectedForegroundExecutionId` 恒定不变（如 `runtime_command_4`）→ 客户端幻忙：运行时其实空闲，客户端还在等一个早已结束的前台执行。停止按钮的实现是"发 stop → 运行时回报状态"，运行时空闲时 stop 是 no-op，永远清不掉客户端的忙标志。
2. 往前找破坏点：本例 22:57 出现 `"error":"database is locked"`（会话 SQLite 库竞争）→ `target.run_start.failed` → `turn.failed` 链条，之后簿记开始与运行时脱节。判定"最后一轮是否已完成"看两处：`core.runtime` 的 `turn.completed` 事件，与 `~/.zcode/cli/rollout/model-io-<sessionId>.jsonl` 里的 `finishReason:"stop"`。

恢复：**关掉该会话所在窗口**（必要时重启客户端）。运行时侧没有任何东西在跑，不会杀掉真实任务；最后一轮已完成并持久化，数据无损。不要反复点停止——只会刷无意义的 idle 检查日志。

诱因：会话超长（本例 1183 条消息 / 72.7 万 input token，已触发过 compact）+ 同机多开 10 个以上 ZCode.exe 进程共写同一会话库，SQLite 锁竞争概率大增。长会话及时开新会话继续，别在几十万 token 的会话里接着干活。

## Why
把幻忙当成"模型或网络卡住"会一直等、反复点停止，全部无效；以为关了窗口会丢进度而不敢动，反而把会话永久卡死。日志里的 `runtimeStopKind:"idle"` 是决定性证据：真正在跑的任务不会报 idle。

## How to apply
ZCode 桌面端任何"停不下来 / 发了没反应"的会话，先按上面两步 grep 日志定性；确认是幻忙就关窗口恢复，并把后续工作迁到新会话。相关：[[zcode-session-db-real-user-extraction]]（从会话库提取真实消息，用于找回卡死会话里的输入）。
