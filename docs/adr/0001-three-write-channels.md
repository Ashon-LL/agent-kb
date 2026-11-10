# ADR-0001: 三条沉淀通道

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

Agent 经验有不同产生方式：用户明确要求记住、定期批量复盘、会话中的自动提醒。
若全部自动写入，会污染库；若只靠手动，又会漏掉大量可复用经验。
ZCode 项目记忆关闭后，自动通道不能再依赖平台 memory。

## Decision

保留三条通道，共用同一份 `skill/SKILL.md` 规程与 `kb_validate.py`：

| 通道 | 触发 | 写库 |
|---|---|---|
| `/kb add` | 用户明确要求 | 立即写，写完必须 `kb_validate [PASS]` |
| `/kb-harvest` | 定期/手动 | 先出候选，用户逐条确认后写 |
| kb hooks | SessionStart / UserPromptSubmit / Stop | **不写库**，只注入提醒与规程 |

## Consequences

- 自动通道保持“增强而非阻塞”，不会替用户做写入决定。
- 批量通道需要人工确认，吞吐低于自动，但可审计、可回滚。
- 文档必须同时讲清三条通道，不能只写 `/kb-harvest`。
- 三条通道共享校验器，规则不会因入口不同而分叉。

## Alternatives considered

- **只保留手动**：漏采集体经验，已否决。
- **hooks 自动写入**：误报会污染全局库，且难以追责，已否决。
- **harvest 自动整批写入**：候选未确认就落盘，违反“经验是资产”的可控原则，已否决。

## References

- `commands/kb.md`
- `commands/kb-harvest.md`
- `hooks/kb_hooks.py`
- `hooks/kb_harvest.py`