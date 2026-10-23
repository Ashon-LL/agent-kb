---
name: kb-search-miss-is-not-kb-empty
description: kb_search 返回「无结果」≠ 库里没有——换症状词/口语多轮检索 + 直接 ls 目录与读 INDEX.md，把「检索失败」和「库空」分开；2026-10-23 实测漏读 6 条直接相关条目
type: pitfall
topic: verification, methodology
source: MH-Agent-Open（2026-10-23 派单 #209 前被用户当场纠正「你好好看看经验库，绝对是有的」）
date: 2026-10-23
verified: 2026-10-23
---

**经验**：`kb_search.py` 返回「[无结果] 换个说法」时，**只能得出「我这几个词没命中」**，不能得出「经验库没有相关经验」。这两者的差值在 MH-Agent-Open 2026-10-23 是 **6 条直接命中本轮每一条错误的条目**。

## 实锤（2026-10-23）

任务：派单让 NPC 独立检验我做的审计 P0/P1 交付。动手前跑 `kb_search.py "派单 验收 独立复算 中书令"` → 无结果；换「审计修复派单验证」「NPC 交付 落盘 验收」→ 仍无结果 ⇒ 我写下「经验库无相关条目，这些教训都在团队记忆和仓库手册里，已足够」。

用户当场纠正：「**你先别盯，你好好看看经验库，绝对是有的**」。随后认真检索，命中 **6 条直接相关**：

| 条目 | 内容 | 我本轮对应的错误 |
|---|---|---|
| `backlog-records-rot-verify-before-dispatch` | 自己维护的「未做/待办」台账会腐烂，拿它当任务书输入前必须先在代码里复核（实测 6 条「未做」全部已闭环） | 拿登记册「待办 65 条」旧快照派 #207（A 批 21 条），NPC 那时已做完 ⇒ 重复派单 |
| `check-inflight-work-before-dispatch` | 派单前三查：open PR / 远端分支 / 最近构建；与上一条互补（一条查历史是否已做、一条查当前是否有人在做） | 同上；且 2026-10-08 已犯过同一错（T14），当天是第 2 次 |
| `no-assertion-with-with-measurement`（实际名 `no-assertion-without-measurement`） | 对工具/平台能力零实测零断言；固定顺序：本机先例→官方文档→实跑一次 | 派单入口照手册写「apigogo/x 已删除」就用 `@i.o/x`，没跑一条 `get-by-id` |
| `stated-provenance-needs-evidence-and-conditions` | 「没找到记录」≠「不存在」；出处强制分事实/推断/未见记录三档 | 同型：手册写「已删除」我就当事实，连仓是否存在都没验 |
| `minimal-change-and-no-scope-creep` | 最小改动、闭环即止、不做表面修补 | 解合并冲突用 Python 写文件，引入 1047 处 CRLF，超出必要改动面 |
| `defect-localization-methodology` §7 | 别把「我能想到的机制」当根因，先问/先反证 | 镜像侧拿相邻提交性质外推「1f9e3e8d 是纯文档」，漏掉它的后端改动 |

## 为什么会漏（三个机制）

1. **关键词是我自己概括的任务名词，不是条目作者写的症状词**：我搜「派单 验收 独立复算」，而条目 description 写的是「台账会腐烂」「派单前三查」「零实测零断言」——**语义相关但字面零重叠**。kb 的钩子提示早就写了「症状词/口语也能命中」，我用了书面概括词。
2. **只试了 2~3 个词就收手**：每次「无结果」都该触发「换说法」而不是「下结论」。
3. **完全没走「枚举」这条路**：kb 是**分目录的经验库**（`pitfalls/` `workflow/` `tools/` 各上百条 + `INDEX.md`），`ls` 一下目录、肉眼扫文件名，`backlog-records-rot-verify-before-dispatch` / `check-inflight-work-before-dispatch` / `cnb-npc-dispatch-essentials` 这三个名字**直接就能看到**——这是比关键词检索更可靠的兜底路径，我一次都没用。

## How to apply

- **判定纪律**：`kb_search` 无结果 ⇒ 只说「我这几个词没命中」，⛔ 不许写「经验库没有」。
- **三步检索法**（缺一不可）：
  ① `kb_search.py` 用**症状词/口语/错误现象**（如「派重了」「台账腐烂」「已删除」）多轮换，≥3 轮；
  ② `ls ~/.agents/kb/pitfalls/ ~/.agents/kb/workflow/ ~/.agents/kb/tools/` **扫目录名**；
  ③ 读 `INDEX.md` 全量扫一遍（条目少时这步最可靠）。
- 命中后**读全文再干**，⛔ 不许只看钩子行——本次 6 条里有 4 条的「How to apply」段才是我真正缺的动作。
- 与 [[survey-false-negatives-substring-and-enumeration]] 分工：那条管「盘点/逆向任务里 grep 命中数当证据」，本条管「**检索工具无结果被当成对象不存在**」——同族不同层。
