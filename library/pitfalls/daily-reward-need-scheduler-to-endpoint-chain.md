---
name: daily-reward-need-scheduler-to-endpoint-chain
description: 逆向「每日奖励到账」要追「调度器→回调→实际 HTTP 调用」三级链；「桌面端启动自动调 X」不等于 X 是发放源（推广活动幂等 claim vs 账号服务 init-app，连日 Δ0 才发现）
type: pitfall
source: APIShow / 讯飞 Astron Studio 每日积分链路定谳（2026-10-06 asar 逆向 + 余额差实测到账）
date: 2026-10-06
verified: 2026-10-06
topic: reverse-engineering
---

**经验**：找「每日自动到账的奖励」触发点时，逆向必须追到**三级链**：

    createXxxScheduler(轮询常量/退避表) → options.initialize 回调 → gateway 方法体里的实际 HTTP 端点

只看到「桌面端启动时自动调了 X 端点」就断定 X 是发放源，会连日 Δ0 而不自知。

**实证（AStudio 每日积分）**：
- 真链路：`createAstronDailyInitAppScheduler`（每 5 分钟轮询）→ `initializeAstronTenantApp` → gateway 的 `initializeTenantApp` → **`POST tenant-app/v2/init-app`**（Cookie 鉴权、无请求体、返回 `{banned:false}`）。服务端在这次调用里按天发放（实测两号各 Δ+100 通用 / Δ+5000 星火）。
- 假链路：`POST client-download-reward/claim` —— 属**推广活动服务**（bundle 报错文案「推广活动服务返回了无效的领取结果」），对奖励横幅只是**幂等回执**，恒 `flag:true` 而 Δ0。脚本连日调它、台账连日 Δ0，根因就在这。
- 判别法：看该端点所在代码块的**错误文案归属哪个服务**；同一 bundle 里「账户/会员/积分」与「推广活动」是两套服务命名空间。

**配套纪律**：
1. **奖励类脚本必须记 `delta`（余额差）字段**，不能只记「已领取 / 200 / flag:true」——缺 delta 就没人发现连日空转。
2. 发放由**服务端按天判定**（响应恒 `count:null`、重复调用幂等），客户端不需也管不了时点；每天调一次即可。
3. 参数类可从 `membership/plan-config` 读口径自证（`dailyLoginEnabled` / `dailyLoginValidDays` / 各套餐 `dailyLoginPoints`）。

**相关**：[[gateway-tool-choice-string-only-and-no-cooldown-on-client-errors]]（同属「上游只认一种形态/参数，写错就全挂」类）、
[[redacted-get-full-put-wipes-secrets]]（返回成功≠生效，必须读回实证）
