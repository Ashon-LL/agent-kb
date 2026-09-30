---
name: zcode-platform-verified-facts
description: ZCode 平台实测事实合集——扩展资源落点语义（skill 分 zcode/agents、记忆仅项目层、MCP 权威在 cli/config.json、AGENTS.md symlink 拒写、新资源需重启）与 hooks 行为（默认关、项目级启动加载+trust 门控、always-allow 会话级旁路）
type: tool
source: ailika + default（2026-08~09 本机 Windows 实证）；2026-09-15 合并 hooks 与资源落点两条
date: 2026-09-15
verified: 2026-09-15
---

改 ZCode 配置/自动化前先认落点与实测行为，避免"改了不生效""hook 没触发"。以下均本机实证，非文档转述。

## 一、扩展资源落点语义

- **skill 目录语义**：`~/.zcode/cli/skills`（或 `~/zcode/...`）= **仅 ZCode 可见**；`~/.agents/skills` = **跨工具共享**。要"只有 ZCode 认"放前者，要"别的工具也认"放后者。
- **自动记忆按项目隔离**：`~/.zcode/cli/memories/projects/<项目>/memory/`，**没有全局层**——全局通道只有 `~/.zcode/AGENTS.md` + `~/.agents/skills`（外加 `~/.agents/kb` 这个人工经验库）。
- **MCP 权威位置是 `~/.zcode/cli/config.json` 的 `mcp.servers`**；`~/.agents/mcp.json` 只是同作用域回退，**config.json 里一旦有 server 段，整个回退文件被忽略**——改 mcp.json 不生效。
- **AGENTS.md 可能是符号链接**：如 `cloudflare_temp_email/AGENTS.md → CLAUDE.md`，Edit/Write 拒写"穿 symlink"，须改真实目标文件。
- **自定义子代理/技能需重启会话**才被识别（启动时扫描缓存）。
- 全局 `~/.zcode/AGENTS.md` 每次会话注入，是唯一可靠的"跨项目规则"落点。

## 二、hooks 行为

- 配置在 workspace `<repo>/.zcode/config.json` 或用户 `~/.zcode/cli/config.json`：`{"hooks":{"enabled":true,"events":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"process","command":...,"timeoutMs":N}]}]}}}`。**默认禁用**，必须 `enabled:true`。仅 7 个事件（SessionStart/UserPromptSubmit/PreToolUse/PermissionRequest/PostToolUse/PostToolUseFailure/Stop）；exit 0 过、exit 2 拦（stderr 喂模型）；JSON stdout 严格 schema，`permissionDecision:"ask"` 实测可用（弹真实权限提示）。
- **项目级 hooks 只在会话启动加载，且受 workspace trust 门控**：中途装的 hooks 不生效（日志看 `config.project_hooks.pending_trust`）。
- **"始终允许"是会话级旁路**：保存项目权限规则后同会话内被覆盖的 Bash 调用**跳过 hooks**（连 BLOCK 类也短路）；重启会话后 hooks 恢复触发，规则未被删除；规则存应用内部 DB，不在任何可编辑配置里。
- 排"hook 没触发"：先查已保存的 allow 规则，再重启验证。无独立 `zcode` CLI（桌面应用）；ZCode 日志时间戳是 UTC。

**How to apply**：动 ZCode 扩展前先按"落点语义"定位文件；新增 skill/subagent 后重启会话再验证；跨项目规则写全局 AGENTS.md，项目专属状态写项目 memory；装 hooks 默认关要显式 enabled:true 且重启。相关：[[mcp-stdio-install-smoke-test]]、[[github-china-network-workarounds]]。
