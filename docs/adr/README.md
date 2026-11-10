# 架构决策记录（ADR）

> 本目录回答**为什么这样设计**：背景、选择、后果、替代方案。
> 怎么用看 `../../README.md`；写入/检索/收割规程看 `../../skill/SKILL.md`。

## 状态约定

| 状态 | 含义 |
|---|---|
| Proposed | 提议中，尚未生效 |
| Accepted | 已采纳，当前实现以此为准 |
| Deprecated | 不再推荐，但尚未被替代 |
| Superseded by ADR-XXXX | 已被新 ADR 替代 |

已接受的 ADR **不重写**。要改变结论，新建一条 ADR，并在旧 ADR 顶部标 `Superseded by ADR-XXXX`。

## 编号与命名

`NNNN-kebab-title.md`，四位递增，例如 `0003-zcode-config-location.md`。

## 索引

| ADR | 决策 | 状态 | 日期 |
|---|---|---|---|
| [0001](0001-three-write-channels.md) | 三条沉淀通道：手动 / 批量 / 自动 | Accepted | 2026-11-10 |
| [0002](0002-platform-adapter-matrix.md) | 平台接入形态矩阵：hook / skill / plugin / unverified | Accepted | 2026-11-10 |
| [0003](0003-zcode-config-location.md) | ZCode 配置落点：`~/.zcode/cli/config.json` 的 `hooks.events` | Accepted | 2026-11-10 |
| [0004](0004-harvest-readonly-pipeline.md) | 收割是只读候选管线，默认只收强信号 | Accepted | 2026-11-10 |
| [0005](0005-search-idf-ranking.md) | 检索叠加 IDF，保留命中词数优先 | Accepted | 2026-11-10 |
| [0006](0006-readonly-library-audit.md) | 库审计只读：重复 / 零入链 / 过期 / topic | Accepted | 2026-11-10 |
| [0007](0007-markdown-zero-dependency.md) | 纯 Markdown + 标准库，零第三方依赖 | Accepted | 2026-11-10 |
| [0008](0008-runtime-deployment-sync.md) | 仓库是源，运行时副本按安装器同步 | Accepted | 2026-11-10 |
| [0009](0009-documentation-layers.md) | 文档分层：README / SKILL / ADR / 契约 / 变更日志 | Accepted | 2026-11-10 |

## 与其他文档的分工

| 文档 | 回答的问题 |
|---|---|
| `../../README.md` | 怎么用、支持哪些平台、安装与测试入口 |
| `../../skill/SKILL.md` | 写入/检索/收割的**操作规程**（唯一权威） |
| `docs/adr/` | **为什么**这样设计、取舍与后果 |
| 工作区 `AGENTS.md` | 跨项目强制边界与命令 |
| 工作区 `references/decision-changelog.md` | `AGENTS.md` 规则旧值 → 新值 |
| `../../tests/` | 契约与回归验证 |

## 新增 ADR

1. 复制 `template.md`，按 `NNNN-kebab-title.md` 命名。
2. 写清 Context / Decision / Consequences / Alternatives。
3. 更新本文件索引。
4. 在 README 或代码注释加指针；已接受的旧 ADR 只标 Superseded，不重写。
5. ADR 与实现、测试在同一任务内提交，避免“文档说 A、代码做 B”。