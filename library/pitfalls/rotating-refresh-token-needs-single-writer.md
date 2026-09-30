---
name: rotating-refresh-token-needs-single-writer
description: 会 rotate 的 refresh token 只能有一个刷新者——多方同时刷新时后到者持已失效的旧 RT，表现 401/session dead 甚至账号被禁；接管前先枚举"谁在定时刷 token"，并关掉多余的
type: pitfall
source: APIShow 接入 WorkBuddy 双账号（2026-09-21）：评估第三方面板接管任务时发现双刷新者竞态；实测确认当前仅网关一方刷新故无风险
date: 2026-09-21
verified: 2026-09-21
---

**经验**：**会 rotate 的 refresh token，只能有一个刷新者（token owner）**。多个进程/服务同时持有同一账号的 RT 并各自刷新时，先刷的那个会让 RT 失效，后到的拿着**已经作废的旧 RT** 去换 → 401 / `session dead` / 业务错误码（本例网关记为 `12153`）。它会**连续触发失败计数，进而把账号自动禁用**——即"什么都没做错，账号却挂了"。

**Why**：2026-09-21 评估给 WorkBuddy 账号池加第三方面板时发现这个风险。当时池里有两条独立的刷新路径：

- **网关**（Go）：保活定时 22:00 全量刷新 + **每次请求前 T-10min 按需刷新**（`handler.go` 附近）
- **管理端**（FastAPI）：每小时巡检续期（`renew.py` / `update_auth_tokens`）

两者**各自有进程内锁**（网关 `tryLockAccount`、管理端串行巡检），但**彼此之间没有跨进程锁**。保活 22:00 那次必然与请求前刷新窗口重叠 → 后到者持旧 RT → 401。同类项目文档里也把这条列为铁律（原作者明确写过"一个账号只能有一个 token owner"）。

本例**实测后确认当前无风险**：管理端那些 `asyncio.sleep` 循环是**任务日志轮询与任务领取**，不是 token 刷新；唯一刷新者是网关。**但这个结论必须靠"枚举谁真的在刷"得出，不能靠猜**。

**How to apply**：

1. **接管/新增组件前先枚举刷新者**：`grep -rnE "refresh|renew|keepalive|保活" <每个组件的服务代码>`，并**分清"定时刷新 token"与"定时做别的"**——本例管理端的 `while True + asyncio.sleep` 看起来像刷新，实为任务轮询。别按文件名/循环形状猜。
2. **一个账号钉死一个 owner**：其余组件要么只读（不刷新），要么关掉其续期功能。二选一，**不要双开**。
3. **判断是否已出问题的取证**：日志里找 `401` / `session dead` / 业务错误码（本例 `12153`），以及**账号被自动禁用**的记录（本例 `auto_ban` / `disabled` 由连续失败触发）。这三个常同时出现，根因都是 RT 竞态。
4. **多账号同理**：owner 可以集中在一个组件里，但**同一账号**绝不能有两个刷新者。新增账号时不要在两边都挂续期。
5. **接管顺序**：先把新组件跑成只读（或任务-only、不碰 token），验证稳定后再切换 owner，最后关掉旧 owner 的刷新。切错顺序 = 直接制造竞态。
6. **凭据文件加锁不是解法**：文件锁只能防"同时写"，防不了"读到已被别人 rotate 掉的旧 RT"——**要防的是多个读者各自去刷新**，所以要在**架构上**保证单一 owner，而不是在文件层加锁。

**相邻**：凭据只对所属层有效见 [[layered-service-credentials-must-match-layer]]；凭据轮换要覆盖所有条目见 [[credential-rotation-must-cover-all-entries]]。
