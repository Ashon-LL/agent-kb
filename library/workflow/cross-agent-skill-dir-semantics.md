---
name: cross-agent-skill-dir-semantics
description: 跨工具装技能先弄清目录语义——~/.agents/skills 是共享约定但各工具支持不一（zcode 双目录直读；workbuddy 对自己 skills 目录做 symlink auto-discover，junction 接入是正规装法）；动手前先看同目录既有形态再搜文档，未实测的能力不要断言
type: workflow
source: workbuddy 装配实测 + Agent Skills spec 与 awesome-dsh 文档检索（2026-10-04）
date: 2026-10-04
verified: 2026-10-04
topic: agent-orchestration, reporting
---

**经验**：给多工具装同一份技能时，每个工具的「技能目录语义」都不同，装法跟着语义走：

1. **zcode**：原生直读 `~/.agents/skills/`（跨工具共享层）+ `~/.zcode/cli/skills/`（专属层），放共享层即可。
2. **workbuddy**：与 CodeBuddy（腾讯）**不是一个产品**（用户 2026-10-04 纠正，安装器旧版曾误装到 ~/.codebuddy）。对 `~/.workbuddy/skills/` 做 auto-discover 且**原生支持 symlink**（awesome-dsh 文档佐证）→ 正规装法是建 junction/symlink 指向共享目录，本机 35 个技能皆此形态且实测识别。Windows 用 `_winapi.CreateJunction`（无需特权）。
3. **通用**：`.agents/skills` 是 Agent Skills 规范的跨 agent 共享约定（用户级 `~/.agents/skills/`、项目级 `./.agents/skills/`），Claude Code / Codex / Copilot CLI 等原生支持——但「支持到什么程度」因工具而异，不能假设全部直读。

**Why**：误判语义的代价双向——把链接当实体复制会产生多副本漂移源；把实体当链接支持而直接建链接，不识别链接的工具里技能就静默缺失。本次先错装成真目录（没看本机 35 个链接先例），后靠「同目录惯例 + 官方文档」双证改回。

**How to apply**：给新工具装技能的固定顺序——① `ls` 该工具 skills 目录看**既有条目的形态**（链接还是实体，跟多数走）；② 搜该工具文档确认 symlink 支持与目录名；③ 动手后让工具实际识别一次再收工。用户对平台行为的口头陈述是**线索不是定论**，先用 ①② 取证。相关：[[hardlink-unify-shared-scripts-across-tools]]、[[zcode-platform-verified-facts]]。

关联 [[npc-iterate-by-sending-failure-text-back]]、[[approval-is-explicit-not-analogous]]、[[two-agents-waiting-on-each-other-is-deadlock]]。
