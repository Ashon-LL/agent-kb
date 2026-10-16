---
name: zcode-platform-verified-facts
description: ZCode 平台实测事实合集——扩展资源落点语义（skill 分 zcode/agents、记忆仅项目层、MCP 权威在 cli/config.json、AGENTS.md symlink 拒写、skill/subagent 需重启但 provider_config.json 热生效）与 hooks 行为（默认关、项目级启动加载+trust 门控、always-allow 会话级旁路）
type: tool
source: ailika + default（2026-08~09 本机 Windows 实证）；2026-09-15 合并 hooks 与资源落点两条
date: 2026-09-15
verified: 2026-10-16
topic: mcp, zcode
---

改 ZCode 配置/自动化前先认落点与实测行为，避免"改了不生效""hook 没触发"。以下均本机实证，非文档转述。

## 一、扩展资源落点语义

- **skill 目录语义**：`~/.zcode/cli/skills`（或 `~/zcode/...`）= **仅 ZCode 可见**；`~/.agents/skills` = **跨工具共享**。要"只有 ZCode 认"放前者，要"别的工具也认"放后者。
- **自动记忆按项目隔离**：`~/.zcode/cli/memories/projects/<项目>/memory/`，**没有全局层**——全局通道只有 `~/.zcode/AGENTS.md` + `~/.agents/skills`（外加 `~/.agents/kb` 这个人工经验库）。
- **MCP 权威位置是 `~/.zcode/cli/config.json` 的 `mcp.servers`**；`~/.agents/mcp.json` 只是同作用域回退，**config.json 里一旦有 server 段，整个回退文件被忽略**——改 mcp.json 不生效。
- **AGENTS.md 可能是符号链接**：如 `cloudflare_temp_email/AGENTS.md → CLAUDE.md`，Edit/Write 拒写"穿 symlink"，须改真实目标文件。
- **自定义子代理/技能需重启会话**才被识别（启动时扫描缓存）。
- **`~/.zcode/v2/provider_config.json` 改动热生效、无需重启 ZCode**（2026-10-06 用户实证，推翻旧误解）：改 `modelConfigRules.providerModelRules`（如某 provider 的 `maxOutputTokens.max`）保存后即自动应用，**不存在"重启前仍是旧值"的观察窗**——别再把"没重启"当修复未生效的借口。注意与上面 skill/subagent 相反：那两类资源才需要重启会话。
- 全局 `~/.zcode/AGENTS.md` 每次会话注入，是唯一可靠的"跨项目规则"落点。

## 二、hooks 行为

- 配置在 workspace `<repo>/.zcode/config.json` 或用户 `~/.zcode/cli/config.json`：`{"hooks":{"enabled":true,"events":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"process","command":...,"timeoutMs":N}]}]}}}`。**默认禁用**，必须 `enabled:true`。仅 7 个事件（SessionStart/UserPromptSubmit/PreToolUse/PermissionRequest/PostToolUse/PostToolUseFailure/Stop）；exit 0 过、exit 2 拦（stderr 喂模型）；JSON stdout 严格 schema，`permissionDecision:"ask"` 实测可用（弹真实权限提示）。
- **项目级 hooks 只在会话启动加载，且受 workspace trust 门控**：中途装的 hooks 不生效（日志看 `config.project_hooks.pending_trust`）。
- **"始终允许"是会话级旁路**：保存项目权限规则后同会话内被覆盖的 Bash 调用**跳过 hooks**（连 BLOCK 类也短路）；重启会话后 hooks 恢复触发，规则未被删除；规则存应用内部 DB，不在任何可编辑配置里。
- 排"hook 没触发"：先查已保存的 allow 规则，再重启验证。无独立 `zcode` CLI（桌面应用）；ZCode 日志时间戳是 UTC。

## 三、后台任务（`run_in_background`）生命周期

- **ZCode 重启后，先前启动的后台任务成为「孤儿」**（2026-10-16 实测）：任务进程可能**继续存活**（两次实测两种结果——崩溃时子进程被带走、优雅重启时反而存活），但**新 ZCode 实例不再列管它**（任务列表看不到、TaskOutput 不可达）⇒ 用户问「后台任务呢」= 孤儿态；正解 = 停止孤儿（按命令行取 PID 再 Stop-Process，拆两步各自验证）+ **在当前实例重新拉起**（用户才看得见）。
- 需要「与 ZCode 生命周期解耦」的长驻进程（保活类），别只靠后台任务形态：改由独立系统进程承担（PowerShell `Start-Process` 拉起的独立脚本），或双形态并行（可见性 + 抗崩溃兼得）。

**How to apply**：动 ZCode 扩展前先按"落点语义"定位文件；新增 skill/subagent 后重启会话再验证；跨项目规则写全局 AGENTS.md，项目专属状态写项目 memory；装 hooks 默认关要显式 enabled:true 且重启。相关：[[mcp-stdio-install-smoke-test]]、[[github-china-network-workarounds]]。

关联 [[kb-accident-three-layer-lessons]]、[[zcode-provider-config-group-enum-standard-personal]]、[[zcode-workflow-cwd-drift-and-amend-same-name]]。
