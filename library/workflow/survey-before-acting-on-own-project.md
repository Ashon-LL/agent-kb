---
name: survey-before-acting-on-own-project
description: 对连续迭代的自有项目，动手前必须先只读盘点"已有什么"再定"缺什么"
type: workflow
topic: reverse-engineering
source: apishow
date: 2026-10-03
verified: 2026-11-15
---

**经验**：对"加功能/接协议/改配置"类任务，先花时间只读盘点现状：grep源码关键词（功能名/端点/配置键）、查DB/配置事实源、列"已有什么vs缺什么"清单，再决定动什么。子代理派发前主代理先完成现状调研，派工内容="已查证的缺口"，不是"去开发猜的功能"。连续踩墙（同主题2次以上卡壳）→停止盲试，回到只读盘点。

**Why**：没查协议面就动手改造撞三轮墙回退——如果先只读盘点：responses2chat本就带/v1/responses转换、anthropic_adapter现成在线、nginx早反代/v1/messages。没查网关已有功能就派3个子代理并发开发——自查源码才发现指纹隔离/抽奖/连登兑换/补签本就存在，真正缺的只有两处小补丁。

**How to apply**：生产改动（尤其adapter/渠道/网关）动手前先列：现在有什么、要改什么、怎么回滚。APIShow是长期迭代的自有项目，功能经常"早已存在"（只是没在文档里或分散在各包），靠猜"缺什么"会重复造轮子、乱改、浪费配额。

## 2026-11-15 补：二次开发跟随上游，必须把「权威功能页 + 可解包产物」当事实源

zcodepro 跟进果冻 `features.html` 的「失败自动重试」时，用户已经给出页面原文和可解包安装包，
我却先按旧记忆和日志猜测，把「已删除视图」归成我方自建，又派多个代理分别看日志/源码/产物；
用户再次明确「直接看果冻怎么实现」后，才从果冻 CLI 抽到真实补丁符号：`Ymt()` 窄白名单放在
`classifyProviderBusinessFailure` 最前面、`isZsmTransientStreamMessage` 接流恢复、`1e5` 流恢复预算等。
真实根因是 provider 通用业务失败 `MODEL_CALL_FAILED / 400 / 模型 X 调用失败，请提供 traceId...`
先在我方 `eIn()` 被判 `invalid_request + retryable=false`；我方旧补丁只挂在 `mL()`/`aha()`，
没覆盖这个分类入口。结果是错误明细看起来相似，状态机却从「后台重试后完成」变成 `turn.failed`。

**教训**：可解包 + 有功能清单时，不许用「凭印象推断」或「多代理并行猜」代替逐符号落点。
先固定验收清单，按功能逐条抽取上游真实符号、分支顺序和调用点；再对照我方分类链找缺失入口；
最后写执行型测试证明目标错误从终态变为可重试、且取消/鉴权/欠费/上下文超限仍是终态。

**How to apply（补）**：
1. 把上游功能页/发布说明/清单原文落盘，标为验收基准；用户贴出的功能文案优先级高于旧报告和记忆。
2. 对每条功能记录「上游符号/偏移 → 我方锚点 → 最小补丁 → 反例测试」，不写「应该差不多」。
3. 功能归属以清单和解包产物为准；「我方移植后移除」不能写成「我方自建/原创」。
4. 修完同步候选包、CURRENT-META、manifest、报告归属和测试；不要只重建 out/ 就宣称完成。
5. 用户说「先修好刚才的」时，新错误/新会话必须排队，不能把当前修复切成半截；反省在闭环后做。
6. 历史脚本名（如 `3180`）若与当前基线（3.18.2）不一致，明确它是文件名残留并单独清理，
   不要让它把当前状态、旧哈希、旧测试结果混进结论。

关联 [[quantity-and-config-claim-three-errors]]（归属/数字/状态别张口就来）、
[[tautological-assertion-and-self-scoped-recheck]]（测试必须来自真实产物并做变异反证）、
[[survey-false-negatives-substring-and-enumeration]]、[[browser-extension-forensics-and-migration]]。

<!-- hook-reviewed 2026-11-15: INDEX 已覆盖上游功能页/可解包产物/归属/半路分叉/旧哈希 -->
