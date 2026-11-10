# ADR-0009: 文档分层

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

文档曾出现多处漂移：README 同时承担用法、架构、决策与历史；
测试数字、供应商、平台形态分散在多处；同一结论被反复复述。
结果是改动一处、过期三处，Agent 与人都难以判断哪份是权威。

## Decision

按“回答什么问题”分层，禁止跨层复述：

| 层 | 文件 | 只回答 |
|---|---|---|
| 使用层 | `README.md` | 怎么用、支持哪些平台、安装/测试入口 |
| 规程层 | `skill/SKILL.md` | 写入/检索/收割的操作规程（唯一权威） |
| 决策层 | `docs/adr/` | 为什么这样设计、替代方案、后果 |
| 契约层 | 工作区 `AGENTS.md` | 跨项目强制边界与命令 |
| 变更层 | 工作区 `references/decision-changelog.md` | `AGENTS.md` 规则旧值 → 新值 |
| 契约验证 | `tests/` | 可执行的行为契约 |

## Consequences

- 新增架构决策必须写 ADR，README 只留索引。
- 操作规程变更只改 SKILL；README 给指针，不复制规程全文。
- 旧 ADR 不重写；变更用新 ADR + `Superseded` 链接。
- 文档审查时先判断“这属于哪一层”，再决定写哪里。

## Alternatives considered

- **单一大 README**：必然膨胀、漂移，已否决。
- **只写提交信息**：不可检索、不可链接，已否决。
- **ADR 与 decision-changelog 合并**：一个记架构、一个记规则变更，职责不同，保持分离。

## References

- `docs/adr/README.md`
- `../../README.md`
- `../../skill/SKILL.md`