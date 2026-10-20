---
name: scope-whitelist-hardcoded-switch-auth-path
description: 403 Insufficient scope 可能是平台硬编码的 scope 白名单而非 key 配错，加 scope 或多建 key 无效，应改走会话/JWT 认证路径
type: pitfall
source: apishow（2026-10-05 AstrBot v4.28.2 cron 端点 403）
date: 2026-10-05
verified: 2026-10-05
topic: security
---

**经验**：「权限不足」先分清它是配置问题还是**代码里的白名单**。AstrBot v4.28.x `dashboard/api/auth.py::require_scope()` 的 API key 分支：

```python
if scope not in ALL_OPEN_API_SCOPES:
    raise 403 "Insufficient API key scope"
```

cron 端点要 `system` scope，而 `system` 不在 `ALL_OPEN_API_SCOPES` ⇒ **任何 API key 永远拿不到 system**，多建 key、改 key 的 scope 都撞同一面墙（白名单制，不可勾选）。真解法是**换认证路径**：`POST /api/v1/auth/login` 换 dashboard JWT，JWT 分支直接返回 `scopes=["*"]`（含 system），cron / personas / providers / conversations 全通。

定谳手段是对照实验：同一端点 `GET /api/v1/cron/jobs`，旧 API key → `Insufficient API key scope`，JWT → `status: ok` 返回 22 条。同一端点、同一动作、只换 token 类型 ⇒ 根因是这条认证路径的 scope 上限，与 key 配置无关。

**Why:** 白名单制的 403 与「key 少了某个 scope」报错文案完全一样，直觉反应是去补 scope，而白名单里没有的 scope 补不上 ⇒ 会白建一堆 key 反复撞墙。三个识别信号：报错点名某个具体 scope；该 scope 在管理 UI 上不可勾选；文档的 scope 枚举表里没有它。

**How to apply:** 遇 403 insufficient scope 按顺序：① 在源码里找该 scope 常量的**定义处与校验处**，确认它是否在允许列表内；② 对同一端点用另一种凭证做 A/B，区分「凭证类型」与「凭证内容」；③ 确认是白名单就去找平台自己的**会话式认证**（login → JWT/cookie，通常是全权），而不是继续申请 key。别把 API key 当成唯一的机器凭证形态。

⚠ JWT 有 TTL（本例 7 天），落凭据库时同时记 `jwt_expires_at` 与重登方法，别只存 token。凭据真值只进 `.local_secrets/`，正文只记取值位置：[[credentials-never-in-memory-or-logs]]。

相关：[[redacted-get-full-put-wipes-secrets]]、[[layered-service-credentials-must-match-layer]]、[[env-claims-must-be-reverified]]。

关联 [[quota-exhausted-vs-banned-distinguish]]。
