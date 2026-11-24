---
name: dsh-session-store-and-cleanup
description: DSH 会话分三层（正文/索引/缓存），删会话必须三处同步；会话层 workspace-write 时 ~/.dsh 全盘不可写且 run_code 提权不穿透嵌套工具策略
type: tool
source: default-workspace 会话 2026-11-17 清理 dsh 残留会话实测（12 份正文 / 13 份缓存 → 删 6+7，释放 2.64 MB）
date: 2026-11-17
verified: 2026-11-17
topic: toolchain
---

# DSH 会话存储与残留清理

## 经验

$DSH_HOME（默认 `~/.dsh`）里会话数据分三层，删会话必须三处同步：

| 层 | 位置 | 作用 |
|---|---|---|
| 正文 | `sessions/<项目slug>/<sessionId>/session.v4.jsonl.zstd` | 会话全部消息（zstd） |
| 索引 | `storages/workspace.json`：`global.archivedSessionIds`、`global.pinnedSessionIds`、`tables.workspaces.<id>.sessionIds` | GUI 会话列表的唯一来源 |
| 缓存 | `storages/session_projcache/sessions/<sessionId>.json`（按会话）、`storages/dsh-context/overview-cache.v1.json`（总览，含 identity.path 与用量） | 派生数据，可重建 |

清理顺序：删正文目录 → 删同名 projcache → 从 workspace.json 的 `sessionIds`/`archivedSessionIds` 移 id → 从 overview-cache 过滤 `identity.path` 命中的条目。

**判定残留**：
- 磁盘有正文目录、workspace.json 未登记 = 未登记会话（subagent / blank 空会话 / 历史孤儿）
- projcache 有 json 但正文已不存在 = 纯残留，可直接删
- 当前会话 id 从环境变量 `DSH_SESSION_ID` 取；再用 mtime 是否仍在增长排除正在写入的会话，防误删自己

## Why

- 只删正文 → workspace.json 留悬空 id、overview-cache 继续显示已删会话，GUI 出幽灵条目或点击报错。
- 只删缓存不删正文 → 正文成孤儿继续占盘。
- 用 shell `rm -rf` 硬删绕开文件策略 = 绕沙箱，审计链断；正解是请用户切权限而不是换壳。

## How to apply

- 接到「清理 dsh 残留会话」：先 `env | grep DSH_SESSION_ID` 定当前会话，再列三层做差集，按复选确认范围，一次删完并同步三处；收尾用 `ls ~/.dsh/sessions/*/*/session.v4.jsonl.zstd | wc -l` 与 projcache json 数比对，应一一对应、无孤儿。
- **权限坑（2026-11-17 实测）**：会话层 file policy 为 `workspace-write` 时 `~/.dsh` 在工作区外，`ops_remove`/`ops_edit_file` 一律返回 `POLICY_DENIED`；run_code 的 `sandbox_permissions` 参数**不能穿透嵌套工具策略**（嵌套工具保留自身策略与审批）。解药只有一个：让用户在 DSH 权限选择器切到 `danger-full-access` 后重跑。
- 改完 workspace.json 与 overview-cache 都要 `JSON.parse` 复核一次，避免手搓 JSON 把 GUI 启动搞挂。
