# ADR-0003: ZCode 配置落点

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

旧安装器按 `~/.zcode/hooks.json` 生成独立配置文件，但新版 ZCode 实际从
`~/.zcode/cli/config.json` 的 `hooks.events` 读取 hook。旧落点不会生效，
且会让人误以为已安装。

## Decision

- 配置文件：`~/.zcode/cli/config.json`。
- 适配器：`kb_hooks.py`（只做协议转换，不存文案或触发词副本）。
- 合并方式：事件级合并 `hooks.events`，保留其他 key 与其他 hook 事件。
- 事件：SessionStart / UserPromptSubmit / Stop；Stop 为收尾提醒。
- 修改后必须新建会话，ZCode 在会话启动时快照 hook 配置。

## Consequences

- 安装器必须 merge，不能覆盖整个 `config.json`。
- 合并失败时不得整文件覆盖，必须保留原文件并报错。
- 备份 `.bak`；改完 hook 必须新建任务才生效。
- 其他 ZCode 用户的自定义 hook 不会被本工具删除。

## Alternatives considered

- **继续用 `~/.zcode/hooks.json`**：ZCode 不读取，已否决。
- **整文件覆盖 config.json**：会丢用户其他配置与 hook，已否决。
- **只写独立脚本、不合并配置**：用户还需手工接线，体验差，已否决。

## References

- `templates/zcode-hooks.json`
- `scripts/install.ps1` / `scripts/install.sh`
- `hooks/kb_hooks.py`