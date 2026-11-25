---
name: hook-injection-short-but-not-simplified
description: Hook/系统注入文案要短而不简：压缩上下文占用，但保留路径、命令、判据、例外与自愈条件；删解释性理由，不删会改变行为的限定词
type: workflow
source: 用户 2026-11-25 要求（agent-kb 注入文案优化；原话：短是为了减少上下文，不简要是为了防止偏离原意、理解错误）
date: 2026-11-25
verified: 2026-11-25
topic: preference, methodology
---

**经验**：所有 hook/系统注入文案按“短而不简”写。短是压 token；不简是保留执行所需的最小完整信息：脚本路径、命令、判据、例外、自愈条件。删解释性理由和重复背景，不删会改变行为的限定词。

**Why**：注入文案每次模型调用都占上下文。过度压缩会丢掉“同族优先扩充”“[FAIL] 不绕过校验器”“若并非要求则忽略”这类限定，模型会按错误默认执行；只删形容词和解释，才能既省 token 又不偏原意。

**How to apply**：
- 保留：可执行命令与绝对路径、判据（[PASS]/[FAIL]）、分支条件、禁止项、自愈句。
- 删除：为什么这样设计的解释、重复的背景、显而易见的结果（“正常干活”）。
- 改完用桥接脚本实测三类输入：正常开工、命中触发词、普通消息不触发；并跑 `python ~/.agents/kb/kb_validate.py` 见 [PASS]。
- agent-kb 的消息唯一真相源是 `kb_core.py`；OpenCode 桥接副本 `~/.config/opencode/hook-bridge/agent-kb/kb_core.py` 需同步复制。

关联 [[error-message-is-product]]。