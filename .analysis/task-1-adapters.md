# 派单 #1：适配器质量基线 + 全平台安装覆盖

**仓库**：apigogo/agent-kb
**分支**：feat
**NPC 角色**：CodeBuddy
**时间预算**：≤ 1 小时
**增量推送要求**：每完成一个文件的改动就 commit + push，至少 8 次 commit

## 背景

仓库当前 10 个平台适配器，但 NPC 派单 #1 生成的 8 个（claude / hermes / pi / opencode / openclaw / workbuddy / kimi / qoder）是**薄壳**——照搬 trae_zcode_adapter.py 的模板改个 JSON 字段名就完事，没有查过各平台 hook 的真实事件名 / stdin 字段 / stdout 格式。install.ps1 只支持 3 个平台，install.sh 不存在。

## 交付物（按优先级）

### P0. 给 8 个薄适配器补真实平台差异

逐个查各平台官方 hook 文档，修正以下三处：
1. **hook 事件名**：比如 OpenClaw 可能不是 SessionStart / UserPromptSubmit，要改成该平台实际回调的事件名
2. **stdin JSON 字段名**：Codex CLI 可能给的是 vent 不是 hook_event_name，要对齐
3. **stdout 输出格式**：有些平台要 JSON 带 systemMessage 字段，有些要纯文本，按官方文档来

参考来源（必查）：
- Codex CLI hooks: https://platform.openai.com/docs/codex/cli/hooks
- OpenCode hooks: https://github.com/opencode-ai/opencode 文档
- OpenClaw hooks: https://github.com/openclaw-ai/openclaw

每个适配器文件头注释要写清楚：**平台名** + **hook 文档链接** + **stdin 字段映射表** + **stdout 格式说明**。

### P1. 全部适配器支持环境变量配置

统一三件事：
`
AGENT_KB_PATH    覆盖默认 ~/.agents/kb（优先级最高，高于 sys.argv[1]）
AGENT_KB_DEBUG   设为 1 时向 stderr 输出 [agent-kb debug] 事件=xxx prompt_len=xx kb_path=...
`

### P2. install.ps1 扩到全部 10 平台

当前只支持 trae / zcode / codex。扩支持：claude / hermes / pi / opencode / openclaw / workbuddy / kimi / qoder。每个平台要：
- 拷贝正确的 adapter 文件到对应 hooks 目录
- 生成对应 hooks.json（复用 templates/ 下已有模板，替换占位符）
- 打印安装目标路径 + 下一步提示

### P3. 新增 install.sh（bash，Linux/macOS）

功能与 install.ps1 完全对称，支持同样 10 个平台。shebang #!/usr/bin/env bash，必须 set -euo pipefail。

## 验收标准

- [ ] 10 个适配器每个文件头有平台差异注释
- [ ] AGENT_KB_PATH / AGENT_KB_DEBUG 环境变量在所有适配器生效
- [ ] install.ps1 支持 10 平台，install.sh 存在
- [ ] 每个提交都推到 feat 分支，至少 8 次 commit
- [ ] 最终 push 到 apigogo/agent-kb feat 分支
