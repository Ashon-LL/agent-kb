---
name: multi-account-claim-per-person-dedup-hides-second-account
description: 官方文档写「每账号」、服务端实作「每人」的签到/领取活动：同机多账号的第二号活动被从列表隐藏、直接 claim 被 503/BLOCKED——列表缺失≠无此活动，别拿账号缓存字段下「没得领」结论；修复=跨账号发现活动 ID 直接 claim（幂等）
type: pitfall
source: APIShow / qoder 尾号4600 每日领取排查（2026-10-05 端到端实证）
date: 2026-10-05
verified: 2026-10-05
topic: reverse-engineering
---

**经验**：多账号池里做「每日签到/领奖励」时，服务端常按**人/机器指纹**去重而不是按账号
（厂家文档写「每账号」，实作「每人」）。后果典型到可当模式认：

- 同一指纹下的**第二个账号**：活动**从列表整体消失**（只剩消费向 VIEW_DETAILS 类）；
- 直接对活动 ID 发 claim → `BLOCKED + SAME_PERSON_ALREADY_CLAIMED`，或
  `503 SAME_PERSON_DEPENDENCY_UNAVAILABLE`（同人去重依赖暂不可用）；
- 结果：网关按列表驱动领取 → 第二号永远显示「暂无可领取」，**连 claim 都没真正发过**，
  一年下来一个子儿都没有，还以为是账号侧没有活动。

**Why**（2026-10-05 全程实测，qoder 国际双号池）：

- 对照组实证：同窗口内账号 A（先建、先领）列表有每日活动（CLAIMED +100 且余额 +100）；
  账号 B（第二号）同一接口 raw JSON 里该项**整体缺失**。换机器头（B 的 Bearer + A 的三身份头）
  **无差别**地缺 → 排除请求头，服务端按账号/人给。
- 我第一轮错判：凭账号缓存字段（credits size=0、campaignCodes={}）就下结论「Free 号无活动可领」，
  被用户当场戳穿（同池 A 明明领到了）。**缓存字段是快照不是事实，列表缺失≠无此活动**，
  必须对活动 ID 真发一次 claim 看返回码。
- 修复验证：批量签到层**跨账号发现**每日 Credits 活动 ID（任一账号可见即可），对列表隐藏
  的账号**直接 claim 兜底**——幂等（已领 replayed / 同人 BLOCKED 都不重复发放），
  **余额差为正才算到账**。上线后第二号每次签到都真发 claim，服务端 503 期间原样记录、下窗口重试。

**How to apply**：

1. **「列表里有没有」先和「别人有没有领到」对表**：同池/同窗口其他账号领到了，本号列表却缺
   该项 → 别急着报「无活动」，先对已知活动 ID 发一次 claim 看真实返回码。
2. **别拿账号文件/缓存字段下「没得领」结论**：credits/campaignCodes 是上次刷新的快照，
   只能佐证余额，不能证明活动不存在。
3. **列表驱动领取要留「隐藏补偿」**：批量签到器跨账号发现活动 ID 兜底直领；claim 幂等
   所以随便重试；到账只认余额差（flag/success 都不算）。
4. **同人去重的本质**：同一机器指纹/登录环境的多账号=同一「人」，每日/限次奖励只发一份。
   要让第二号独立领取，必须让服务端识别为独立人（per-account 原生机器身份），宿主没有
   官方客户端组件时这是已知限制，别硬造。

**相邻**：「到账与否只认余额差」同 [[desktop-app-points-reverse-proxy-via-usage-report]]；
「缓存字段不是事实」见 [[env-claims-must-be-reverified]]；「枚举前缀即结论」类误判见
[[report-what-you-did-not-what-you-meant-to-do]]。
