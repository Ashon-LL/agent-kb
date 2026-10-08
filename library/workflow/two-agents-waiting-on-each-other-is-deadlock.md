---
name: two-agents-waiting-on-each-other-is-deadlock
description: 两个 Agent 互相等=死锁——破解靠给明确到无解释空间的下一步
type: workflow
topic: agent-orchestration
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：两个 Agent 互相等的症状：writerOccupied:true、会话消息数N轮不变、工作区无改动、也无新提交。破解靠给一条明确到没有解释空间的下一步——不许做什么、剩余责任归谁、沉默的语义是什么。

**Why**：发"本轮到此为止/先歇着"这种没有明确出口的话⇒对方回"等你下一条"；又把"等它确认收工"当成下一步继续等⇒闭环。单看每一步都合理（没下新指令、没新产出），合起来就是死锁。

**How to apply**：收工指令模板——"本轮到此为止。不要再改任何仓库文件、不要新开任务。剩下的由我同步给用户。若你之后不再回话，即为正常收工，不是异常。"判"在等"要看三条同时成立：会话文件N分钟无写入 + writerOccupied:true + 我方无待发指令。会话文件mtime仍在动=他还在收尾，不是"在等"。
