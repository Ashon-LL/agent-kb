# 派单 #1 完成报告

**分支**：feat ｜ **commit 数**：18（要求 ≥8）｜ **测试**：58 项全过

## 交付

| 项 | 状态 | 关键文件 |
|---|---|---|
| P0 适配器真实平台差异 | ✅ | `hooks/{claude,codex,hermes,pi,opencode,openclaw,workbuddy,kimi,qoder,trae_zcode}_adapter.py` |
| P1 环境变量统一 | ✅ | `hooks/adapter_base.py`（新建） |
| P2 install.ps1 全平台 | ✅ | `scripts/install.ps1` |
| P3 install.sh | ✅ | `scripts/install.sh`（新建） |

## 平台真实差异速查

| 平台 | stdin 事件字段 | stdout 格式 | 配置载体 |
|---|---|---|---|
| Codex CLI | `event` | `systemMessage` | `~/.codex/hooks.json` |
| Claude | `hook_event_name` (+`source`) | `hookSpecificOutput.additionalContext` | `settings.json` hooks 子树（merge） |
| Qoder | `hook_event_name` | 同上 | `~/.qoder/settings.json`（merge） |
| WorkBuddy | `hook_event_name` | 同上 | `.codebuddy/settings.json`（merge + Git Bash） |
| Kimi | `hook_event_name` | **纯文本** | `config.toml` `[[hooks]]`（TOML） |
| OpenClaw | `hook_event_name`（原生 `session_start`/`before_prompt_build`） | `additionalContext`（插件桥） | TS 插件 |
| OpenCode | 嵌套 `event.type`/`event.properties`（原生 `session.created`/`tui.prompt.append`） | `additionalContext`（插件桥） | JS 插件 |
| Trae / ZCode | `hook_event_name` | `additionalContext` | `hooks.json`（`version:1`，PowerShell 调用式） |
| Hermes / PI | ⚠️ 未核实 | ⚠️ 未核实 | ⚠️ 占位 |

## 环境变量

- `AGENT_KB_PATH`：env > `sys.argv[1]` > `~/.agents/kb`
- `AGENT_KB_DEBUG=1`：stderr 输出 `[agent-kb debug] ...`

## 验证证据

```
python3 -m unittest discover tests/   → Ran 58 tests OK
python3 scripts/smoke_test.py         → [PASS] 3/3
pwsh install.ps1 -Platform <p>        → 11/11 成功（pwsh 7.6 / Linux）
bash install.sh -p <p>                → 11/11 成功
bash install.sh -l  vs  pwsh -List    → 输出完全一致
生成的 hooks.json/settings.json        → 逐字节一致（路径归一化后）
剥离 pwsh 的 PATH 下复跑               → 58 项 OK（2 项 ps1 按预期 skip）
```

## 已知不确定项

Hermes 与 PI **无公开官方 hook 文档**。未编造链接，文件头标 `⚠️ 未核实`，
契约标为占位，改动点收敛到 `emit()` 一处。补齐只需提供官方文档链接。

## 过程修复的真实缺陷

1. `$env:USERPROFILE` Linux 下为 null → 安装器崩溃（改 HOME 回退）
2. 模板 `_comment` 泄漏进真实 settings.json（改写入前剥离）
3. trae/zcode 模板反斜杠路径（改正斜杠）
4. `normalize_event` 漏 `tui.prompt.append` / `message_received`
5. 两安装脚本 `-l` 顺序不一致
