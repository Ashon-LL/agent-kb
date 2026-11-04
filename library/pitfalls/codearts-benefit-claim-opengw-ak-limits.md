---
name: codearts-benefit-claim-opengw-ak-limits
description: CodeArts 福利模型领取走 opengw /api/v1/benefit/claim（AK/SK 签名、每天一次）；OAuth 流发的 AK 在 opengw 全 401、面板内置领取报 4000 —— 脚本代领走不通，要官方客户端/真实 IAM AK
type: pitfall
source: APIShow CodeArts 修复调研（2026-10-30）：Johnsheng1/codearts2api benefit.py + HITZY2002/codearts2api + magpie-community plugins/codearts 三方对照 + 本机 4 号实测
date: 2026-10-30
verified: 2026-10-30
topic: llm
---

# CodeArts 福利模型领取：机制、错误码与账号限制

## 经验

华为云 CodeArts 免费福利模型（`deepseek-v4-flash-0731` / `deepseek-v4-pro-0813` / `glm-5.3-flash`）的领取机制（三方实现一致，抓包确认）：

- Host：`https://opengw.developer.huaweicloud.com`
- `POST /api/v1/benefit/claim`（空 body）＝**每天领取一次**（北京时间，幂等）
- `GET /api/v1/benefit/claim`＝签到状态；`GET /api/v1/user/tokens/balance`＝免费额度余额
- `GET /api/v1/gateway/config`＝免费模型列表
- 鉴权：`SDK-HMAC-SHA256`（AK/SK，签名头 host/content-type/x-sdk-date）
- 错误码：`0000` 成功；`4004` 无福利/已过期；`4006` 当天名额没了
- 领取成功后 chat 自动带 `maas_type: benefit`，模型立即可用

**坑**：通过 IDE OAuth 流拿到的 `access_key_id/secret_access_key` 在 opengw 处 **401「access key not found」**（4 个号实测全 401）——这组 AK 不是可用的 IAM AK；面板内置领取（HITZY2002 codearts2api）则报 **4000 invalid channel, group not found**。

## Why

- 误以为「有 AK/SK 就能脚本代领」会卡在 401；误以为面板自动领取开着（`benefit_auto_claim=true`）就等于领了，会卡在 4000；
- 福利是**账号维度**的官方活动，领取入口在官方客户端/控制台（打开 CodeArts IDE 模型菜单即触发 claim）。

## 追加实测（2026-10-30，5837 主号新建 IAM AK）

给 `hw_008615194685837_01` 新建正式 IAM AK 后：**鉴权通过**（不再 401），但 claim/config/balance 全部返回 **200 + error_code 4000「invalid channel, group not found」**。加 `X-Domain-Id`/`X-Project-Id` 头无解（后者直接 400 APIG.0602 project not found）。⇒ 4000 是 **opengw 侧该账号没有福利 channel/group 绑定**，不是签名问题。领取入口只剩官方客户端（登录 CodeArts IDE/控制台打开模型菜单）；要先在控制台确认该账号当期是否还有这个福利活动。

## 官方客户端复核（2026-10-30）

用 5837 安装并登录**官方 CodeArts Agent**（Electron，state.vscdb 里 `huawei-cloud-authentication-hw_…-usages` 确认同身份）：其本地快照 `is_free_benefit=False`、模型目录无任何福利模型 ⇒ 与 API 4000 互相印证：**该账号当前未被发放此福利**，不是「没领取」。等官方侧重新发放（或换有福利的账号）后，Agent 模型菜单会自动出现这三个模型。


## ⭐ 关键更正（2026-10-30 同日）：glm-5.3 / kimi-k3 / deepseek-v4.1-flash 其实是可用的

官方 CodeArts Agent 实测（同一账号 5837）用 **`deepseek-v4.1-flash-1017`** 跑通任务；其内核日志显示 chat 仍打
`https://snap-access.cn-north-4.myhuaweicloud.com/api/v2/chat/completions`，但额外带一整套头：
`model-id` / `model-name`、`x-ot-function: agent-general`、`x-ot-client-type: IDE`、`x-ot-client-version: 26.10.100`、
`agent: build`、`user-msg-id`、`created-time`、`x-ot-session-id`，body 另带 `tool_stream/user_prompt/messageCount/tools`。
**缺这些头时，chat 网关对 glm-5.3/kimi-k3/ds4.1f-1017 回 `InferHub.002002009.404 model is not registered`**——不是账号没这些模型，是我们的请求形状不像 Agent。

复刻验证（同 token + Agent 头）：GLM-5.2 / **glm-5.3** 直接 200；kimi-k3 / ds4.1f-1017 报 `TM.00001041`（并发会话 3 上限，重试即可）。
按此给 relay 打补丁（`scripts/adapters/codearts/patch_codearts_agent_headers.py`）后，四个模型全部 200，站点 codearts 组实测 200。

⇒ 分层结论：**能力/大模型都在**，缺的是「以官方 Agent 的请求形状访问」；福利模型（deepseek-v4-flash-0731 等）才是真正需要领取、且本账号 4000 领不到的。

## How to apply

- 要领：用对应账号登录 **CodeArts IDE / 华为云控制台**手动领取；或给该账号建**真实 IAM AK/SK** 后用 Johnsheng1/codearts2api 的 `benefit.py`（支持 `status/claim/models`，可挂每日计划任务）；
- 领取成功后再把模型加回渠道清单（HITZY2002 的 chat 会自动带 `maas_type: benefit`，加 `Benefit: true` 的目录条目才不会被动态发现覆盖成 404）；
- 诊断顺序：401 APIG.0301＝AK 无效（换真 IAM AK）；4000 invalid channel/group＝账号无此福利组（找官方入口或放弃）；4004/4006＝活动过期/名额没了。
