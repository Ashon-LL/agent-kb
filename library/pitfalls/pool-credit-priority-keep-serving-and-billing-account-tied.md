---
name: pool-credit-priority-keep-serving-and-billing-account-tied
description: 账号池做 credit-priority 选号（像 Trae 按余额高者优先）时，「服务账号」与「计费/结算账号」必须全程同一——转发鉴权、usage 上报、401 刷新写回都要用同一个选中账号；验证用「余额差落谁家」而非日志；没有每账号余额信号的源（STS/OAuth 号）退化为健康轮询，别硬造优先级
type: pitfall
source: APIShow / Astron relay 双号池 + qoder pick() 改造（2026-10-05 端到端实证）
date: 2026-10-05
verified: 2026-10-05
topic: api-gateway
---

**经验**：把多账号源改成「credit-priority」（剩余额度高者优先，同 Trae）时，最容易漏的不是
**选号逻辑**本身，而是**选中账号的贯穿**：一次请求从「出内容」到「扣分」往往经过多个独立
函数（转发 Bearer / usage 上报 Cookie / 401 重试刷新），各自重读配置就会选到不同账号——
必须让**同一个选中账号贯穿「转发→计费上报→401 刷新」**，刷新后的新凭证还要**写回该账号
所属的存储**（池条目或单凭据文件二选一，别写串）。验证只看**余额差落谁家**：服务了请求的
账号被扣分、没服务的账号分毫不动，才算闭环。

**Why**（2026-10-05 实测，Astron relay 双号池改造全程证据链）：

- 改造前 relay 三个函数（current_bearer_token / report_usage / refresh_model_bearer_token）
  各自 `load_cred()` 读单凭据文件——池化后若各自独立选号：A 号服务、B 号计费上报，
  用户软件积分就扣在没出力的号上（违反「消耗必须落软件积分账」的用户核心诉求）。
- 落地方案：请求入口选一次 `pick_cred(model)`，显式把 cred 往下传（`forward(cred=…)` →
  `report_usage(cred=…)` → 401 时 `refresh_model_bearer_token(cred)`）；刷新后
  `_persist_pool_account(account_id, {token})` 按账号归属写回池条目，池外才落单凭据文件。
- 实证闭环：`spark-x2.5` 非流式+流式两发 200；选中号（余额最高）星火 24986→24984（Δ-2），
  未选中号 **Δ0**，billing 日志 `state=settled rated=1 charged=1`——「谁服务谁记账」成立。
- 选号口径：**按模型的扣分币种**选（spark/deepseek 系看星火余额、其余看通用余额），
  别用一个笼统「积分」排序；快照缺失回退轮询、单号回退单凭据。
- 边界：没有「每账号余额信号」的源（如华为 CodeArts STS——只有账号级 OAuth、无 quota 概念）
  **没法做 credit-priority**，退化为 first-healthy 轮询是正确的，不是偷懒；硬造优先级
  只会带来「排序依据不存在」的假账。

**How to apply**：

1. 池化选号前先列全「一次请求穿过函数的读凭据点」，统一改为入口选一次 + 参数贯穿。
2. 币种相关的选择信号从**配额快照**拿（由池定时任务落盘，别让网关每请求打上游）。
3. 凭证写回按账号归属分桶（池条目 / 单凭据文件），刷新不能写串账号。
4. 验收只认余额差：请求→选中号 Δ<0、其余 Δ=0、billing 状态 settled。
5. 无余额信号 → 明确报「退化健康轮询」并说明原因，不硬造排序。

**相邻**：「扣分走独立结算上报」见 [[desktop-app-points-reverse-proxy-via-usage-report]]；
「到账只认余额差」同 [[multi-account-claim-per-person-dedup-hides-second-account]]；
「环境/事实陈述必须命令复测」见 [[env-claims-must-be-reverified]]。
