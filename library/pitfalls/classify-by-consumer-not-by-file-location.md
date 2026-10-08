---
name: classify-by-consumer-not-by-file-location.md
description: 划分「哪些代码属于哪个子系统」时要看谁在调用它，不是看它住在哪个文件——同一文件里常混着多方共用的工具函数
type: pitfall
source: MH-Agent-Open（20261005 下线「编辑器 Agent 通道」，同型三次）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
related: [[bulk-delete-requires-reverse-dep-check]], [[user-instruction-is-not-evidence-of-no-dependency]]
---

**经验**：要下线/搬移某个子系统时，判断「某个符号属不属于它」的唯一依据是**谁在调用它**（grep 它的引用方、看调用链是否可达），**不是它住在哪个文件**。一个文件里常混着多方共用的工具函数与常量。

**Why**：2026-10-05 下线编辑器 Agent 通道（删 761 行），我按「看它跟被下线的东西放在一起」划界，**同型错了三次**，每一次都是「被守卫/测试抓出来的功能会坏」：

| 符号 | 我以为 | 实际 | 后果 |
|---|---|---|---|
| `_declares_noop` / `_NOOP_PHRASES` | Agent 专属 | 轻量通道 `_parse_reply` 也在用 | 编辑器 AI 运行时崩 |
| `_load_mode_hints` / `_MODE_HINT_FALLBACK` | Agent 专属 | 读场景包提示词，通用能力 | 「场景包改提示词」失效 |
| `stop_agent` / `_kill_proc` | Agent 专属 | 「终止任意 CLI 进程」通用能力（真身在另一模块） | 差点打断进程终止路径 |

**Why 错三次同型**：文件名与目录会**骗人**——`editor_agent.py` 里既有 Agent 通道的私有实现，也有被别人复用的公共件。看到「它在这个文件里、而我要删这个文件的一部分」，就顺手归类了，**没问「谁在调它」**。

**How to apply**：
- 划界时对每个候选符号做一次 `grep -rn "<符号名>"`，命中里出现**与被下线子系统无关的模块**（尤其「另一模块通过 re-export 转发」的情况）⇒ 它是共用件，不能删。
- 特别注意 **re-export / 转发层**：真身可能已迁到别处，原文件只留一行转发（`return other._kill_proc`）。此时「它在我们要删的段里」但「它的真身在别人身上」——把转发删掉会打断别人。
- 判据写成可测的：**「一调用它就抛 NotImplemented」**的存根 = 真的下线了；仍能正常工作的 = 划错了。
- 下线前把「共用件」清单先列出来给用户看，比事后靠 CI 抓便宜得多。

相关：[[bulk-delete-requires-reverse-dep-check]]（删除动作的核实清单）、[[user-instruction-is-not-evidence-of-no-dependency]]（用户指令 ≠ 依赖已消失）。
