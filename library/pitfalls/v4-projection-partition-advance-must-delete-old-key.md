---
name: v4-projection-partition-advance-must-delete-old-key
description: 流式投影的「新帧取代旧帧」缓存必须显式 delete 旧 key；WeakMap 不延长寿命的假定在旧数组另有强引用时失效，会堆出上 GB 的会话历史
type: pitfall
topic: reverse-engineering
source: zcodepro v29.19（2026-11-07，三份堆快照 + 官方/果冻/上游源码三方对照）
date: 2026-11-07
verified: 2026-11-07
---

**经验**：聊天/流式 UI 里「每帧生成新 rows 数组、用 WeakMap 缓存按数组引用派生的 history/tail」这类优化，
**只 set 新 key、不 delete 旧 key** 时，不能指望 WeakMap 自动回收——只要模块作用域里还有任何闭包、
Map、渲染单元缓存间接引用旧数组，那份数组连同它 slice 出来的历史就全活着。长会话会稳定堆出上 GB。

**Why**：真案例——ZCode 3.17.2 官方/果冻/我方三个产物里，
`advanceConversationRowsPartition(previousRows, nextRows, deltas)` 每帧
`rowsPartitions.set(nextRows, {history: previous.history, tail: nextRows.slice(...)})`，
源码注释还写着「WeakMap 不延长数组寿命」。实测 11-06 16:50 重启后 8 小时，
渲染层 JS 堆 51 → 1745 MB；三份堆快照（11-05/11-06/11-07）支配树根 retained
1511 / 786 / 1732 MB，路径全是 `GC roots → 模块作用域 → Map → array → store/binding 闭包 → history`。
`heap_find` 在路径里看到会话消息、工具输出、用户贴的源码文本和 Tabs JSON。

**关键判读陷阱**：V8 快照把 WeakMap 内部表边标成 `internal`（强边），
普通支配树工具会把 ephemeron 误判为强持有。不要只凭支配树下结论——
补一个「从根只走非 weak/非 shortcut 边」的强可达检查，确认前驱真的可达
（本项目 `tools/strong_reach.cjs`），再动刀。

**How to apply**：
1. 先查上游源码与官方/二次开发各版本产物，确认是不是共有缺陷（本例三方逐字相同，
   不是任何一方的补丁回归）；装机时刻指标无跳变也能交叉印证。
2. 找齐 `history` 的**全部消费者**再决定能不能裁：本例 `vvn` 用它拼 virtualizedUnits、
   `wRt` 读每行做用量/高速卡统计、`h0e` 用数组引用做缓存身份 ⇒ **裁剪会丢显示/统计**。
   所以正解是「取代时显式 delete 旧 key」，不是「限制行数」。
3. 别照抄项目里已废弃的方案（ADR-0008 行池上限方向无效；window-bound v2 明确不加上限不裁剪）。
4. 同时检查**模块级注册表**（本例 `eH`：transportIdentity → pane → `tBt`）的清理回调是否真的
   清掉了普通 Map 成员；只 `delete(map, key)` 而实例里的 `subscribers` 还挂着闭包，等于没清。
5. 行为级测试要把真实产物里的 `advance` 和 cleanup 闭包抽出来执行，断言
   「旧 key 已删 / 新 key 在 / 需整窗重建的 early-return 分支不误删 / onEmpty 仍触发」。
6. 验收回到 [[memory-curves-need-event-boundaries-and-time-axis]] 的双轴：
   装机后按新的重启事件切段，看段内 30min 窗地板斜率与峰值，不许用刚更新完的单点值。

关联 [[renderer-reload-is-not-context-loss]]、[[measurement-must-verify-control-group]]。

---

## 后续裁定（2026-11-07 02:00）：本条的「delete 旧 key」结论被实测推翻

继续做「删该边后重算强可达」的模拟（`zcodepro/tools/simulate_partition_gc.cjs`、
`rank_holders.cjs`）后发现：

- 删掉 81/82 个 WeakMap 条目 → 可回收 **0 MB**（786.5 → 786.5 MB）；
- 82 个旧 window 数组全被 `property:window`（77 个 snapshot 对象）强引用，
  逐类删单一持有者最多 0.5 MB ⇒ 分布式累积，不是单点缓存泄漏；
- 真正根因是**自动补拉无界分页**：去重键含 `rows.window[0].rowId`，`loadOlder()`
  前插后首行变化 → 键变 → effect 立刻重跑 → 一页页把整个会话历史拉进窗口。
  实测 8189 次/天 `conversationRowsRangeV4`，97.7% 是同一秒连发 ≥3 次。
  正解是**去重键去掉首行 ID**（ADR-0057），不是删分区缓存。

**保留本条作为反面教材**：支配树把 V8 WeakMap 的 ephemeron 内部边标成 `internal`
（强边）会高估 retained；支配树只给线索，必须补「删边后重算强可达」的模拟才敢下补丁。
本次第一版补丁凭支配树推断、未做模拟，回收 0 MB，已撤回进 `legacy/`。
检索「渲染层内存涨 / WeakMap 泄漏」时请优先看 ADR-0057 与
`memory-curves-need-event-boundaries-and-time-axis`。
