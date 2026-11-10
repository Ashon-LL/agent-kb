# ADR-0008: 仓库是源，运行时副本按安装器同步

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

实际运行时存在多份副本：

- `~/.agents/kb/*.py`：部分与仓库硬链接，部分是独立副本。
- `~/.agents/skills/kb/SKILL.md`：独立副本。
- `~/.zcode/commands/kb*.md`：独立副本，`/kb-harvest` 实际读这里。
- ZCode hook 配置：`~/.zcode/cli/config.json`。
- ZCode 插件市场：`agent-jev/zcode-plugin`。

只改仓库不会自动覆盖所有运行时副本；直接改运行时会与仓库漂移。

## Decision

- **仓库是唯一源**；运行时副本由安装器/同步步骤生成。
- 硬链接能同步的（`kb_core.py`、`kb_search.py` 等）优先硬链接。
- 独立副本（commands、SKILL、miner/harvest）改动前先备份，再复制，最后比对哈希。
- 改 hook 配置或脚本后必须新建会话；ZCode 在会话启动时快照。
- 插件市场路径变更必须重新添加市场，不能只改本机目录。

## Consequences

- 同一改动可能需要“仓库 + 运行时副本”两处验证。
- 运行时副本可能暂时领先/落后仓库，必须用哈希核对。
- `.bak` 备份是同步流程的一部分，不是可选步骤。
- 新会话前，当前会话可能仍用旧 hook 配置。

## Alternatives considered

- **全部 symlink**：部分平台/工具不跟随链接，已否决。
- **只改运行时**：会与仓库漂移，已否决。
- **每次自动覆盖运行时**：会破坏用户本地改动，已否决。

## References

- `scripts/install.ps1` / `scripts/install.sh`
- `commands/kb.md` / `commands/kb-harvest.md`
- `skill/SKILL.md`