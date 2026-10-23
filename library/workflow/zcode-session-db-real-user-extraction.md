---
name: zcode-session-db-real-user-extraction
description: 从 ZCode 会话库提取真实用户消息做实证分析：删除/归档是软删，正文全在 `~/.zcode/cli/db/db.sqlite`；过滤条件 = `message.data.semantics.origin == 'real_user'` 且 session_id 匹配 `^sess_[0-9a-f]{8}-`（剔除 sess_dwf-* 工作流 actor 与 sess_subagent* 子代理任务书，它们也被标 real_user）
type: workflow
source: agent-kb 会话全量扫描（2026-10-16，906MB / 53924 条消息）
date: 2026-10-23
verified: 2026-10-16
topic: methodology, database
---

**经验**：要分析「用户到底说过什么」，数据源是 ZCode 的正文库，不是导出文件、也不是 UI 列表。

## 数据源

- `~/.zcode/cli/db/db.sqlite`（实测 906MB / 53924 条消息）。
- ZCode 的删除/归档是**纯软删**：状态只在 `v2/tasks-index.sqlite`，正文库**没有删除标记**
  ⇒ 已删、已归档、在用的会话全在里面，「全量」天然成立。

## 过滤真实用户消息（两条件，缺一不可）

1. `message.data.semantics.origin == 'real_user'`（排除 agent_runtime / system 注入）。
2. `session_id` 匹配 `^sess_[0-9a-f]{8}-`（顶层会话）。

⛔ 必须剔除 `sess_dwf-*`（工作流 actor）与 `sess_subagent*`——**子代理任务书也被标为 real_user**
（「你在分析经验库…」这类），不剔会污染分析。

实测结果：real_user 4029 条（去重 1208）、assistant 25782 条。

## 分析产出

- 触发词命中/漏报统计、沉淀意图候选预筛、覆盖率量化、抱怨/纠正聚类；
- 结论只能当线索：片段级匹配是粗判（4-gram），且被「讨论 kb 本身」的元对话污染。

## How to apply

- 先备份数据库或只读打开（`file:...?mode=ro`），不要写库。
- 分析脚本与产物放项目内（如 `.analysis/`），大 JSONL 走 `.gitignore`。
- 不要把「消息条数」当用户诉求数——同一诉求会重复多次，看趋势不看绝对值。

关联 [[zcode-session-delete-is-soft-delete-two-dbs]]、[[kb-search-miss-is-not-kb-empty]]、
[[test-scope-must-be-pinned-by-index-not-walk]]。
