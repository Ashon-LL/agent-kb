# ADR-0002: 平台接入形态矩阵

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

早期 README 把 12 个产品统一标成 hook，但实际机制不同：
WorkBuddy 只有 skill 机制；CodeBuddy 是另一个产品且有 hooks；
OpenCode / OpenClaw 原生扩展点是插件；Hermes / PI 尚未找到官方 hook 文档。
统一标 hook 会直接误导安装方式，造成“看起来支持、实际没挂上”。

## Decision

按产品逐项标注真实形态，不使用“都支持 hook”这种统一说法：

| 产品 | 形态 | 落点 |
|---|---|---|
| Trae | Hook | `~/.trae-cn/hooks.json` |
| ZCode | Hook | `~/.zcode/cli/config.json` 的 `hooks.events` |
| Codex | Hook | `~/.codex/hooks.json` |
| Claude Code | Hook | `~/.claude/settings.json` 的 `hooks` 子树 |
| Qoder | Hook | `~/.qoder/settings.json` 的 `hooks` 子树 |
| Kimi Code | Hook | `~/.kimi-code/config.toml` 的 `[[hooks]]` |
| WorkBuddy | **Skill only** | `~/.workbuddy/skills/kb/SKILL.md` |
| CodeBuddy | **Hook（legacy）** | `~/.codebuddy/settings.json` 的 `hooks` 子树 |
| OpenCode | **Plugin bridge** | JS/TS 插件桥 |
| OpenClaw | **Plugin bridge** | JS/TS 插件桥 |
| Hermes | **Unverified** | 适配器占位，无官方文档 |
| PI | **Unverified** | 适配器占位，无官方文档 |

## Consequences

- README 徽章、平台表、安装器分支必须逐项一致。
- WorkBuddy 与 CodeBuddy 使用不同安装路径，不能共用一套说明。
- 未核实产品保持 `unverified`，查清后再升级为 hook/skill/plugin。
- 新增产品必须先写清“机制 + 路径 + 官方依据”，再写适配器。

## Alternatives considered

- **全部按 hook 处理**：实现简单但错误，已否决。
- **只支持已验证产品**：会丢掉 skill-only 与插件桥场景，已否决。
- **用产品名相似度推断机制**：WorkBuddy/CodeBuddy 已证明会出错，已否决。

## References

- `README.md` 平台支持表
- 各 `hooks/*_adapter.py` 文件头
- `scripts/install.ps1` / `scripts/install.sh`