---
name: codex-hooks-are-claude-compatible
description: OpenAI Codex 的生命周期 hooks 与 Claude Code 同构（事件名/输入输出一致），用户级配置源是 ~/.codex/hooks.json（config.toml 内联 [hooks] 已过时且会被第三方工具冲掉）
type: tool
source: default 会话 2026-10-13 初写（beta 26.727 上推断）、2026-10-14 订正（正式版 26.1007.2314.0 实测：用户级源是 hooks.json）
date: 2026-10-13
verified: 2026-10-14
topic: llm
---

**经验**：Codex（CLI/桌面版）内置生命周期 hooks，**与 Claude Code 同构**，可直接复用同一批脚本：

- 事件名一致：`PreToolUse` `PermissionRequest` `PostToolUse` `PreCompact` `PostCompact` `SessionStart` `SessionEnd` `UserPromptSubmit` `SubagentStart` `SubagentStop` `Stop` `Interrupt`。
- 协议一致：**stdin** 收 `hook_event_name` / `prompt` / `cwd` / `tool_name` 等 snake_case 字段；**stdout** 回 `{"hookSpecificOutput":{"hookEventName":…,"additionalContext":"…"}}`。为 Claude Code / ZCode 写的 hook 脚本**原样可用**（上游甚至带 `external-agent-migration/hooks_cla.rs` 做 Claude 迁移）。
- 开关：正式版 `config.toml` 的 `[features] hooks = true`；beta 时是 feature key `hooks`（`Feature::CodexHooks`，Stable 且默认开）。
- **⛔ 用户级配置源 = `~/.codex/hooks.json`（2026-10-14 订正）**。早期"只能写 `config.toml` 的 `[hooks]` 表"是 2026-10-13 在 beta 26.727 上据源码"用户层没有 hooks_config_folder"**推断**出来的，正式版实测该结论**不成立**——又被 [[negative-feasibility-claims-need-a-probe]] 那条教训命中一次。分层与 Claude Code 一致：user `~/.codex/hooks.json`、project `<project>/.codex/hooks.json`、plugin `plugin_root/hooks/hooks.json`，另有 admin/managed 层；**`~/.agents` 不是 hook 目录**。
- JSON 形态：`{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"…","timeout":3,"statusMessage":"…"}]}]}}`——事件 → matcher 组数组 → handler 数组，与 TOML 的 `[hooks]` 表同构。
- TOML 形态：用 array-of-tables（双中括号那个写法）先声明 `hooks.SessionStart`、再声明它的子表 `hooks.SessionStart.hooks`；handler 用 `type="command"` + `command`（**整条命令字符串**，经 shell 执行）+ `timeout`（**秒**）+ `statusMessage`。
- 桥接：命令里含带空格的可执行路径（如 `C:\Program Files\Python313\python.exe`）时，**套一层无空格的 `.cmd` 包装**最稳，免去 shell 引号地狱。`.cmd` 必须 **CRLF 行尾**（LF 在 cmd.exe 下行为不稳，2026-10-13 实测迁移过来的桥接脚本是 LF，已修）。
- 跨 shell 路径：hook 提醒文案里让 Agent 跑的脚本路径，**用正斜杠绝对路径**（`C:/Users/...`）——cmd.exe 不展开 `~`，bash 会把反斜杠当转义；可从 `Path(__file__).resolve().parent.parent` 动态推导后 `.as_posix()`。
- **共享 hook 脚本改后必须复测**：fail-open 设计会把脚本自身的 NameError/ImportError 吞成"静默无输出 + exit 0"，与"事件不该注入"表面完全一致（本次实测抓到漏 import Path 的回归）。

**Why**：hooks 解析失败**只产生 warning、不会整份配置失败**（不同于 `model_catalog_json` 那类"指向文件"的键），所以配错不易察觉——表现为"hook 静默不触发"。另外第三方工具（如 Codex++）会**整份重写** `config.toml`：内联的 `[hooks]` 表会被冲掉，而 **`~/.codex/hooks.json` 它不动**——这才是优先用 hooks.json 的真实理由（比"版本差异"更关键）。

**How to apply**：跨工具统一钩子行为时，把同一批脚本挂到各平台 hook 配置上，别维护多份文案副本（避免漂移）。改完先用**模拟事件入参直接跑脚本**验证 stdout 的 JSON，再让应用重读配置；若 hook 静默不触发，依次查：`hooks.json` 是否还在 → JSON 是否合法 → `[features] hooks` 是否为 true → 脚本自身是否 fail-open 吞了异常。相关：[[zcode-platform-verified-facts]]、[[negative-feasibility-claims-need-a-probe]]
