---
name: delete-hook-script-after-config-invalidated
description: 删除任何 hook 脚本前，必须先让 hook 配置失效并新开会话——旧会话内存里仍挂着该脚本，直接删文件会让所有 Bash 调用 fail-closed 卡死；同理改插件源码后必须同步升 plugin.json 的 version，否则界面不提示更新
type: pitfall
source: trae_huanjing 工作区 AGENTS.md（本机 hook/插件运维契约）
date: 2026-10-23
verified: 2026-10-23
topic: toolchain, zcode
---

**教训**：hook 脚本的「文件」和「配置」是两件事；先删文件会让仍在运行的会话直接卡死。

## 两条硬规则

1. **删除任何 hook 脚本前，先让 hook 配置失效**（从 `config.json` 移除对应条目），
   并**新开一个会话**确认不再加载该脚本，再删文件。
   旧会话在内存里仍挂着该脚本，直接删文件会让**所有 Bash 调用 fail-closed 卡死**——
   连修复用的命令都跑不了。

2. **改插件源码后必须同步升 `.zcode-plugin/plugin.json` 的 `version`**，
   否则界面不会提示更新，用户会以为改动没生效。

## How to apply

- 顺序固定：改配置 → 新会话验证 → 再删文件；不要「先删了再说」。
- 删除前记下原路径与配置片段，便于回滚。
- 插件改动提交前检查 version 是否递增（可写进发布脚本自检）。

关联 [[zcode-platform-verified-facts]]、[[kb-accident-three-layer-lessons]]、
[[codex-hooks-are-claude-compatible]]。
