# ADR-0004: 收割是只读候选管线

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

ZCode 项目记忆已关闭，`~/.zcode/cli/memories/projects/` 为空；
但会话库 `~/.zcode/cli/db/db.sqlite` 仍保存真实用户消息。
直接让 Agent 读 1.15 GB 会话库并整批写入，既慢又容易把项目专属内容写进全局库。

## Decision

`kb_harvest.py` 只做**只读候选提取**：

1. 会话库只读（`mode=ro`），只取 `real_user` 顶层会话，排除 subagent / 运行时注入。
2. 当前工作区扫描经验型 Markdown；空沙箱时停下问路径。
3. 项目 memory 只是可选来源，不作为必需项。
4. 默认只收强信号（`TRIGGER_PATTERN`：记住/沉淀/以后别/纳入 kb 等）。
5. 弱信号需显式 `--include-weak`，并在报告中保留噪声提示。
6. 输出 Markdown/JSON 候选，**不调用 LLM、不写入库**；确认后才按 SKILL 规程落盘。

## Consequences

- 采集快：最近 1 天 76 条消息约 0.16s。
- 噪声低：真实样例由 25 条宽筛降到 4 条强信号。
- 写入仍由人确认，避免自动污染；代价是不能无人值守批量入库。
- 会话库 schema 变化时需要更新提取器，并补测试。

## Alternatives considered

- **继续依赖项目 memory**：已关闭且为空，已否决。
- **自动整批写入**：候选未确认，已否决。
- **用 LLM 做提取**：违背零第三方依赖与可复现原则，暂不采用。

## References

- `hooks/kb_harvest.py`
- `hooks/kb_trigger_miner.py`
- `commands/kb-harvest.md`
- `tests/test_kb_harvest.py`