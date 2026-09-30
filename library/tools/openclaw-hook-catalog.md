---
name: openclaw-hook-catalog
description: OpenClaw 拦工具调用的 hook 叫 before_tool_call 不是 tool_call；kind 分 Observe/Modify/Gate/Claim 决定能否做门禁；该 hook 超时 15s 且 fail-closed
type: tool
source: agent-jev 派单（20260924，NPC 依官方 reference 纠正任务书里的错名）+ openclaw/openclaw docs/plugins/hooks/reference.md
date: 2026-09-24
---

**经验**：OpenClaw **没有** `tool_call` 这个 hook；要拦截工具调用挂 **`before_tool_call`**
（kind = Modify/gate，官方原文「Rewrite tool params, block execution, or require approval」）。
配套 `after_tool_call`（Observe）。相关：`before_prompt_build`（Modify，可注入上下文）、
`session_start`（Observe，**返回值被忽略**，改不了数据）。

**Why**：kind 决定能不能做门禁 —— `Gate` 的 block 会中止后续 handler，`Observe` 的返回值被丢弃。
挂错 kind（如用 `session_start` 想改数据）**不报错、静默无效**。

**How to apply**：
- 要接「工具调用前拦截 + 索要审批」⇒ 挂 `before_tool_call`，回 `requireApproval`（只问不杀）。
- ⚠️ `before_tool_call` 默认超时 **15s 且 fail-closed**：超时或 handler 抛错会**挡掉工具调用**。
  ⇒ 桥接脚本必须自带超时兜底，否则「脚本慢」被翻译成「命令被拦」，与设计意图相反。
- `matcher` 吃 canonical tool id（`exec` / `apply_patch` / `spawn_agent`…），省略=全部；
  空列表/通配符/厂商别名是非法值。
- 注册走 `package.json` 的 `openclaw.extensions` → `index.ts`（不是 `main`/`exports`）；
  TS 回调不读 stdin ⇒ Python 侧只能当子进程桥被 `spawnSync` 调起。
