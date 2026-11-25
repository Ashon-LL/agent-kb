---
name: coverage-must-include-active-platform
description: 收割/挖掘/守卫的覆盖范围必须包含当前实际使用的平台；只按历史平台写扫描器，会在主平台切换后静默漏掉全部会话
type: pitfall
source: 2026-11-26 审查 kb 技能：kb_harvest / kb_trigger_miner 原来只扫 ZCode，漏掉 OpenCode 的 ~/.local/share/opencode/opencode.db
date: 2026-11-26
verified: 2026-11-26
topic: agent-orchestration, methodology
---

**经验**：给「收割会话 → 沉淀知识」这类工具加数据源时，先列出**当前实际在用的平台**，再写扫描器；只按历史平台写，主平台切换后功能表面正常、实际入库为零。

**Why**：`kb_harvest.py` 自动发现了 DSH/Claude Code/Codex，却漏掉 OpenCode；`kb_trigger_miner.py` 也只读 ZCode。用户已把主会话切到 OpenCode，收割候选仍只来自旧平台，最丰富的近期教训静默不入库。扫描器“能跑、有输出”不等于“覆盖了主来源”。

**How to apply**：
- 新增平台先查数据源 schema，再写适配；OpenCode 用只读 `opencode.db` 的 `session_message` + `session_v2`，优先 `metadata.displayText`。
- 每个来源加独立开关（`--no-opencode` / `--opencode-db`），并在报告 `来源` 行写出实际扫描到的平台。
- 验证用最近 2 天真实数据：候选数 >0，且能看到当前会话的已知消息；不能只测空库。
- 同步更新 SKILL、`/kb-harvest` 命令和集成盘点，避免文档仍写“仅 ZCode”。

关联 [[guard-must-cover-the-changed-layer]]。