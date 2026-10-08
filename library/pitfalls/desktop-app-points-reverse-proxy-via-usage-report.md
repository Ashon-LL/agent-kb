---
name: desktop-app-points-reverse-proxy-via-usage-report
description: 要把桌面应用的「积分/额度」反代给 API 用（像 WorkBuddy 扣账号积分那样）时，聊天请求本身通常不扣分——扣分走独立的结算上报端点（usage report / settle），机制必须从客户端代码/日志挖出结算端点和报告 schema 再在网关侧复刻
type: pitfall
source: APIShow / 讯飞 AStudio 积分反代（2026-10-04 端到端实证）
date: 2026-10-04
verified: 2026-10-04
topic: methodology
---

**经验**：用户要求「把软件里的积分反代出来用，像 workbuddy 那样」时，不要假设扣分发生在**请求通道**
（chat/completions / responses）里。实测讯飞 AStudio：聊天/Bearer 请求**会消耗额度，但扣的是
MaaS 订单/套餐那本账（无查询端点、不可见），不是目标软件可见的积分账**——要扣软件积分，
唯一通道是**独立的结算上报端点**（`POST .../points/deduce-balance`，上报 `ClientTurnUsageReport`），
每次调用结束后调用一次，服务端计价（rated/charged points）并从账号积分账本扣减。网关侧照做
即可让 API 消费走软件积分。⚠ 表述纪律：别说「聊天不扣分」（它扣，只是扣在别处），
目标句=「扣分没落到软件积分账，靠结算上报才落到」。

**Why**（2026-10-04 实测，全程证据链）：

- 反证：基线记录 points（总/星火两本账）→ 打真实聊天 200 → 复测 points 不动（Δ0）；
  而 app 内真实调用 → points 按用量掉（6/2/1 积分对应 tokens 量），且 app 端结算记录
  （`rated_points=6/2`）与 UI 显示逐字对上。
- 结算端点与 schema 的取证途径（按可靠性排序）：① 客户端本地状态库（SQLite outbox 表里
  有真实 report_json + 结算 result_json——app 的 turn_billing_outbox 直接给了完整 schema）；
  ② 客户端主 bundle 里找 billing 相关代码（迁移表名 `TurnBillingRuntimeEventConsumer`
  /`TurnBillingOutbox` 是指针）；③ 请求形态：Cookie 鉴权（ssoSessionId/token/account_id 拼接）
  + `X-Trace-Id: turn-billing-<id>` 头 + 报告 JSON。
- ⛔ **报告字段校验严格**：`billing_turn_id/root_turn_id/session_id/thread_id` 必须是
  **UUIDv7**（时间戳前缀 `01a...`），非随机 UUID；必须带 `schema_version`（如 1.3）；
  `model_usages[]` 含 requested/effective model 与各 token 分项。字段不符 → 业务错误
  「参数无效」（端点是真的、请求到了，只是被校验拒）。
- ⛔ **扣分发生在结算上报，不在聊天**：把聊天请求的鉴权从 Bearer 换成 Cookie 组合也没用
  （实测 /v1 与 /v2 双网关、chat 与 responses 双协议都不扣）；别再往「聊天鉴权」方向猜。
- 同族变体：**同一账号在多个网关（/v1、/v2…）的权益面会各自漂移**——某模型 /v1 403、
  /v2 200 都正常，网关可用性要按需复测，别拿一次快照当永久事实
  （[[env-claims-must-be-reverified]]）。

**How to apply**：

1. **先分清「扣分通道」与「出内容通道」**：聊天/Bearer 只是出内容；找**结算/usage 上报**端点
   （关键词：deduce/deduct/consume/usage-report/billable/outbox）。
2. **从客户端拿真实报告**：查本地 SQLite/状态文件里的 outbox/账本（report_json 全量字段），
   或 grep 客户端 bundle 的迁移表名/`X-Trace-Id` 前缀定位代码。
3. **网关侧复刻**：每次成功响应（有 usage 的上游返回）后，用客户端 Cookie 上报同等报告；
   失败只记日志、绝不阻塞用户响应；用 UUIDv7 生成 ID 防重。
4. **验证只看账本余额差**：上报前记基线 → 触发一次真实调用 → 复测账本；「接口返回成功」
   不等于到账，`settled/charged_points` 才是。
5. **测试会真扣分**：验证上报会真实扣账号积分（最小报告也扣最低档 1 点），探测前先记基线。

**相邻**：能力声明默认值见 [[custom-llm-endpoint-capabilities-default-false]]；
「配置字段名不是规格」见 [[config-field-name-is-not-spec-read-consuming-code]]；
「环境/事实陈述必须命令复测」见 [[env-claims-must-be-reverified]]。
