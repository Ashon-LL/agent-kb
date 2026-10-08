---
name: user-instruction-is-not-evidence-of-no-dependency.md
description: 用户说「删掉/清掉」只定义了目标，不构成「代码里已无人依赖」的证据；把指令当证据会打坏活功能
type: pitfall
source: MH-Agent-Open（20261005 用户指令「删而且清掉」→ 编辑器功能被打坏）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
related: [[bulk-delete-requires-reverse-dep-check]]
---

**经验**：用户指令描述的是**意图与目标**，不是**代码现状的事实陈述**。「删掉那个 X」里，X 是否还有人用，是你要去查的事实，不能默认成立。

**Why**：2026-10-05 用户说「删而且清掉」（指安装区的 claude.exe），我把它读成「这东西已经没人用了」就直接删 —— 但 `editor_agent._run_round` 当时仍在 spawn 这个进程，编辑器 AI 通道因此彻底不可用。同一轮我还按目录连带删掉了 `@anthropic-ai/sdk`，让机器人网关起不来。两次都是同一个认知错误：**把用户指令当成了依赖关系的证据**。

根因是「指令说得笃定」与「事实是否如此」在心理上被合并了：用户对自己产品里哪些东西还活着可能有记忆偏差（这很正常），而我的默认倾向是照办。

**How to apply**：
- 收到「删 / 清掉 / 下线 X」时，把它当**待验证的假设**：「X 已无人依赖」。先 grep 反向依赖 + 看调用方是否活链，再动手。
- 验证到与指令矛盾时**当场报告而不是硬办**：「X 仍被 Y 调用（活链路），删了会导致 Z 失效 —— 要不要连 Y 一起下线，还是只删 X？」让用户做真正该做的决策。
- 用户答「彻底下线」时，把范围确认到**具体清单**（哪些端点/工具/配置项留、哪些删），因为「下线 X」在代码里往往牵连一片。
- 配套：[[ask-with-options-early-never-at-end]]（当场给多选项）；[[bulk-delete-requires-reverse-dep-check]]（删除动作的核实清单）。
