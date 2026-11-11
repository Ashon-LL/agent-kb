---
name: idle-window-authorization-needs-work-event-classification
description: 「无活跃会话可自行重启/升级」类长期授权，准入判据必须按事件语义分类而不是只看「最后一条日志距今几秒」；账本心跳不算忙，turn/tool/model 事件才算；且助手自己的探测会制造事件，靠等待空闲往往不成立，需请用户定夺
type: workflow
source: zcodepro v29.21 会话并排运行态验收（2026-11-10）
date: 2026-11-10
verified: 2026-11-10
topic: verification, safety
---

**经验**：执行「无活跃会话时可自行升级/重启」这类长期授权前，把最近日志按**事件语义分类**：
`zcode_protocol.process.memory_sample`、`config.*`、账本采样等只是心跳/状态事件，不构成「正在干活」；
`turn.phase.started`、`model.request.started`、`tool.call.started`、`session.event.persistence.started`、
`mcp.pool.lease.acquired` 才是真实工作事件。只要窗口内存在后者（尤其有 started 而无对应 completed），
就判「有活跃会话」，按授权原文停下等用户确认，不要重启/覆盖正在运行的实例。

**Why**：连续几轮只报「最后一条 CLI 事件距探测 3~8 秒」就停，理由不够精确——那可能只是心跳。
本轮分类实测：最近 5 分钟 151 个事件里有 **39 个真实工作事件**，最后一条 `tool.call.started`
在探测前 15 秒，属正在执行的任务；同时多个 `app-server --stdio` 进程在跑。
更重要的是：**助手每轮探测/对话本身就在产生事件**，所以「等它自己变空闲」在与用户持续对话的
会话结构下几乎不会成立。这不是靠多等几轮能解决的外部阻塞，把它伪装成「再查一次就好」会原地打转。

**How to apply**：
1. 判据先分类事件，再给结论（忙/闲 + 证据计数），不要只报时间差。
2. 结论是「忙」时**立即停**，不重复探测、不重复问同一问题；把最小用户动作一次说清。
3. 需要重启/写 Program Files 的动作，若授权判据不满足或语义不明，一律等用户明确确认；
   与 [[idle-reclaim-criteria-must-be-work-not-attention]] 同族：判据要看「有没有事在做」。
4. 静态全绿只是代理信号（[[runtime-acceptance-needs-user-install-not-static-proxies]]）；
   运行态结论必须由用户装机 + 使用产生，助手不得用实现完成度替代。
5. 「探测制造事件」这一自反性要写进结论：等待不是有效策略，别把外部阻塞伪装成进度。
