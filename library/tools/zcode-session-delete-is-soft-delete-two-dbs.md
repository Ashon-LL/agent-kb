---
name: zcode-session-delete-is-soft-delete-two-dbs
description: ZCode 的"删除会话"是纯软删——UI 状态在 v2/tasks-index.sqlite 的 tasks 表（archived/deleted/pinned），正文全在 cli/db/db.sqlite 且该库**没有任何删除标记**，所以删完 585MB 仍占着；session.time_archived 是死列别信；定位存储时 grep -rlc 会假阴性
type: tool
source: 2026-09-30 用户问「已归档且已删除/已删除的会话为什么仍然存在」，只读排查 ZCode 3.11 会话存储
date: 2026-09-30
verified: 2026-09-30
topic: zcode, database, sqlite
---

**经验**：ZCode 的会话**删除/归档是纯软删，两个库分职**，排查前先认清这个分层，否则会一直在错的地方找：

| 库 | 表 | 存什么 |
|---|---|---|
| `~/.zcode/v2/tasks-index.sqlite` | `tasks` | **UI 列表的全部状态**：`archived` / `deleted` / `pinned` / `task_status` / `title_overridden`，主键 `(workspace_key, task_id)`，`task_id` 就是 `sess_<uuid>` |
| `~/.zcode/cli/db/db.sqlite` | `session` / `message` / `part` / `session_entry` / `tool_usage` / `model_usage` / `todo` | **全部正文内容**，一条删除标记都没有 |

2026-09-30 实测：用户点删除只把 `tasks.deleted` 翻成 1，`db.sqlite` 里那 60 条会话的 **325,257 条 message/part/entry 记录、585.4 MB JSON 一个字节没少**（该库总 1387 MB）。同一次实验里，用户"取消归档"两个会话后 `db.sqlite` 的 `time_updated` 与 `time_archived` **完全没变**，日志里也搜不到 archive/unarchive —— 反证了 UI 状态与正文库**完全解耦**。

**三个会踩的坑**：

1. **`session.time_archived` 是死列**。483 行**全是 NULL**，`session_entry` 的 7 种 type 里也没有任何删除类目。别拿它判断归档状态——真状态只在 `tasks-index.sqlite`。这正是"日志字面/字段名不是规格"同族：列存在 ≠ 它被写。
2. **子会话占绝大多数**。`session` 表 483 行里只有 77 行是顶层（`parent_id IS NULL`），其余 406 行是子代理/侧聊/fork 子会话。算占用要沿 `parent_id` 展开，否则只算出零头。
3. **`grep -rlc` 是假阴性**。`-c` 会**覆盖** `-l`，结果是"每个文件打了多少个匹配"的计数、**不带文件名**，看起来像"啥也没找到"。我据此误判「Local Storage 里没有 `sess_`」，自检换成 `-rla` 立刻命中 3 个文件。**定位存储一律用 `-rla`，或 `-o | sort | uniq -c`。**

**How to apply**：
- 只读查询 sqlite 用 URI：`sqlite3.connect(f"file:{path}?mode=ro", uri=True)`，物理上杜绝误写；`journal_mode=wal` 下**照样能读到 WAL 里的新数据**，自检方法 = 查一条刚写入的记录时间戳，不用担心读到旧快照。
- 判断"哪些是活的"以 `tasks-index.sqlite` 为准：`archived=0 AND deleted=0` 是活会话，`archived=1 AND deleted=0` 是仅归档，`deleted=1` 是已删。

**✅ 已实证跑通的清理流程（2026-09-30 实跑，不退出 ZCode 也做完了）**：

1. **先备份**：`sqlite3.Connection.backup()`（分批 `pages=2000`）拿**一致性快照**，能扛住 WAL 与 ZCode 并发写；再逐表比 `COUNT(*)` 确认一致。**别用文件复制**——WAL 里的新数据会丢。
2. **`foreign_keys` 默认是 0，`ON DELETE CASCADE` 不会触发** ⇒ 必须按 `PRAGMA table_info` 枚举所有含 `session_id`/`parent_id`/`parent_session_id`/`child_session_id` 的表**逐张显式删**。漏一张就留一地孤儿行。实测要删 17 处：`message`/`part`/`session_entry`/`session_input`/`session_target`/`todo`/`tool_usage`/`turn_usage`/`model_usage`/`input_history`/`dwf_actor`/`session_task_link`(父+子两列)/`dwf_run`/`workflow_run`/`workflow_activity`。
3. **子会话必须展开**：沿 `parent_id` 递归下钻。**同时要扣掉"保留集的子孙"**——万一有活会话挂在被删会话底下，不扣就会误杀。本次 72 顶层展开成 435，扣除后仍是 435（无冲突）。
4. **当前会话硬排除**，脚本里 `assert` 兜底。
5. `PRAGMA busy_timeout=60000` + `BEGIN IMMEDIATE` 单事务提交；跑完 `PRAGMA integrity_check` 必须 `ok`。
6. `PRAGMA wal_checkpoint(TRUNCATE)` 把 `-wal` 压回 0。
7. **目录层必须扫全三层 `agents/` `artifacts/` `exec/`，都是纯文件直接 `shutil.rmtree`，不碰数据库、不需要退出程序**。⚠️ 2026-09-30 首清只扫了 agents+artifacts，`exec/`（每会话的命令输出日志目录）整个漏掉——2026-10-04 二清时它积成 394 项/1GB，其中 368 项是首清已删会话的孤儿。归属判定：目录名 `sess_<uuid>` 直接查 id；`sess_subagent_agent_<uuid>` 要去掉前缀回填 `sess_` 再查；id 既不在 session 表也不在 tasks 表 = 前次清理遗留孤儿，删；`sess_dwf-*`（workflow actor）与不带 sess_ 前缀的（如 bash-startup）留。两清合计：首清 1212 MB + 二清 1329 MB 目录层。
8. **能不能不重启就把磁盘空间要回来？实测能——但有两个坑**：
   - `auto_vacuum=0`（本机实测）⇒ 增量回收不可用，只能 `VACUUM`。而 **`VACUUM` 在 ZCode 运行时照样能跑通**（实测 2.9s 成功）：ZCode 平时只是持连接、不持活跃读事务，独占锁能拿到。**我一度断言"VACUUM 必须退出 ZCode"，被实测证伪**。真失败时报的是 `database is locked`，不是打不开。
   - ⚠️ **VACUUM 的结果先进 WAL、不落回主库**：做完立刻 `os.path.getsize(db.sqlite)` 会看到**大小完全没变**，极易误判成"没生效"。真相是主库已降到 279 MB、而 `-wal` 涨到 284.9 MB。必须补一步 `PRAGMA wal_checkpoint(TRUNCATE)`，WAL 才归零。**判据看 `page_count`/`freelist_count`，不要看文件大小。**
   - 本次实测终值：`page_count` 338,801→68,119、`freelist` 267,146→0、**1387.7 MB→279.0 MB**（连同副产物与备份共回收约 2.3 GB）。
9. **路径要在"跑命令的那个 shell"里对得上**。本机同时有 Git Bash（`~` = `C:\Users\MECHREVO`）和 WSL/Kali（`~` = `/home/xxx`）：在 WSL 里敲 `os.path.expanduser('~/.zcode/...')` 会拼出不存在的位置，报的是 **`unable to open database file`**（看着像被占用/没权限，其实就是路径错了）。连库前先 `print` 一次展开后的绝对路径确认。
   - ⚠️ **更隐蔽的一个：WSL 里读 `/mnt/c` 上的 SQLite 库会报 `disk I/O error`**，哪怕文件完好。原因是 WAL 模式依赖 `-shm` 共享内存索引，DrvFs 挂载层不支持那套 mmap 语义。**判据 = 同一个文件 `os.path.getsize` 能读出正确大小、却一 `SELECT` 就 I/O error** ⇒ 挂载问题，不是损坏。**解法 = 要么从 Windows 侧查（Git Bash / Windows Python），要么先 `cp` 到 `/tmp` 再查。** 实测：`/mnt/c` 上 `disk I/O error`，`cp` 到 `/tmp` 后 `integrity_check = ok`、48 会话、10 顶层。跨项目通用（任何从 WSL 碰 Windows 上的 SQLite/WAL 库都会踩）。
10. **UI 不会立刻反映**：ZCode 渲染进程的会话列表在内存里，可能仍显示已删项、甚至把 `tasks` 行回写。**数据层已干净，界面要重启才对得上**——这点要事先跟用户讲清，否则会以为没删成功。
11. 留一份 `<标题>\t<id>\t<工作区>` 的清单文件，否则删完只剩 UUID 无法反查。备份本身会**抵消掉清理收益**（本次备份 1396 MB），确认无误后要删掉——用户说"不需要备份"就别留。
12. **默认口径：只删正文，不删账本**。三张 usage 表（`model_usage`/`turn_usage`/`tool_usage`）是自成一体的计费账本——无外键、自带时间戳/模型/token 数/耗时，对 `message` 的引用只是溯源指针、不是统计依赖（字段考证 2026-10-04：model_usage 41 列全自包含，样例行自带 raw_usage_json）。删掉正文（message/part/session_input/input_history/todo/session_entry + 三层目录）后账本依然能聚合出完整用量统计。**默认保留 session 行 + 三张 usage 表**——session 行是账本按标题归属的唯一锚点，行本身几乎不占空间（16,890 行才几十 MB，占大头的是正文 JSON）。连坐删除（删 session 与 usage 行）须用户明确点名。⚠️ **2026-10-06 用户把口径收紧为"只留用量，不留其他"：session 行也一并删（账本从此失去按标题归属，只能靠清理清单反查标题↔id）。执行前先确认按哪种口径。**
13. **连坐删除不可逆，动手前必须告知用户并确认**：外键为零、DELETE 页在 VACUUM + wal_checkpoint 后即物理释放、SQLite 自身不进回收站，**无自愈路径**。唯一救法是 VSS 卷影副本（`vssadmin list shadows`，需管理员权限）拿删前整库快照。2026-10-04 二清连坐删了 usage 后用户想恢复用量——无快照、无备份，数据没了 ⇒ 规程定型：**默认保留账本，连坐必先问**。

14. **按会话记账的目录其实有第 4 层：`cli/rollout/model-io-sess_<id>.jsonl`**（`v2/setting.json` 的 `modelIoFullRetentionEnabled=true` 时记全量模型 I/O）。2026-10-06 实测：单个活跃会话的该文件能涨到 GB 级（当时两个活跃会话合计以约 100 KB/s 持续增长——排查"空间莫名减少"先看这里；关掉该开关后增长立即停止，无需重启 ZCode）。**已删会话留下的同名文件属于要清的残留**（2026-10-06 用户口径"只留用量、不留其他" ⇒ 连它一起删）。

关联 [[config-field-name-is-not-spec-read-consuming-code]]、[[log-text-is-not-spec-read-emitting-code]]、[[parallel-test-run-must-isolate-repo-mutators]]、[[zcode-platform-verified-facts]]。

关联 [[producer-consumer-status-mismatch-silently-noops]]。
