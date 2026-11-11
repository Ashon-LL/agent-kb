---
name: zcode-goal-projection-needs-forcesnapshot
description: ZCode 目标按钮"点击才变绿勾"根因是 v4 投影漏 target_changed 增量；forceSnapshot 拿到的也是 CLI 发布器旧投影（实测无效），权威修复是 getZsmUsage 直接读 DB session_target.status 供面板轮询
type: pitfall
topic: zcode
source: zcodepro（2026-11-04 目标按钮事故，DB complete 但投影 notSatisfied）
date: 2026-11-04
verified: 2026-11-04
---

**经验**：ZCode 目标面板按钮显示播放/暂停、点击后才变绿勾，根因不是按钮逻辑，而是
**渲染层 v4 投影与 DB 不同步**：CLI 写 `session_target.status=complete` 并发 `target_changed`
事件，但投影的增量同步漏掉目标更新（迭代数据也是旧的）；`recoverFromStaleAuthority`
只做增量 resync，**不覆盖目标**；只有 `connect({forceSnapshot:true})` 全量快照重读 DB 才对账。
点击之所以"变绿"，正是因为点击触发了快照。

**Why**：实测 DB `status=complete`、无活动 run，渲染层 `[zsm-goal]` 日志却停在 `notSatisfied`；
forceSnapshot 后 24s 内变 verified。靠启发式猜投影迭代数据不可靠（数据本身是旧的）。

**How to apply**：
1. 诊断先看 DB（`session_target`）与渲染层 `[zsm-goal]` 日志是否一致，不一致即投影滞后；
2. 修复用周期性 forceSnapshot（非 verified/complete 期间每 10s），不要用不覆盖目标的增量 resync；
3. 不要对 notSatisfied 做"最新迭代完成即判 done"的启发式——其迭代数据可能也是旧的，会误判真正在跑的目标；
4. active/paused 的旧投影可用 __done 启发式立即翻绿，但 notSatisfied 交给权威快照。

**检索症状词**：目标按钮、点击才变绿勾、播放暂停、target_changed、forceSnapshot、投影滞后、session_target。


## 更正（2026-11-04 晚）：forceSnapshot 单独无效

第一版修复用「每 10s forceSnapshot」，用户更新后实测**仍停 notSatisfied**——日志显示
forceSnapshot 每 10s 触发但状态不变。原因：forceSnapshot 重新订阅拿到的快照来自 **CLI
发布器的当前投影**（fromSeq:0→currentSeq），而该投影本身就漏了 target_changed，所以快照
也是旧的。forceSnapshot 不是"重读 DB"，只是"重发当前投影"。

**真正修复**：绕开投影，主进程 getZsmUsage 现查 DB `session_target.status`（不走缓存）随
响应返回 targetStatus；目标面板（y8t，传入 rootSessionId）每 3s 轮询，DB 说 complete/verified
就显示绿勾。DB 是唯一权威态。

**教训**：诊断"投影滞后"时，先确认快照到底重读 DB 还是重发内存投影；后者修不好滞后。
权威态优先直接读 DB，别在滞后投影上叠启发式。

**副作用**：周期性 `connect({forceSnapshot:true})` 会重订阅会话流，导致会话视图（左侧滚动概览竖条）周期性重排跳位——已移除该自动重订阅，目标完成态 solely 由 DB 轮询判定。

**检索症状词**：forceSnapshot 无效、快照仍旧、投影滞后、session_target、DB 权威态、滚动概览跳位、界面周期性抖动、minimap 跳。
