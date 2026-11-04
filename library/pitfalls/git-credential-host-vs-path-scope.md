---
name: git-credential-host-vs-path-scope
description: git credential fill 只带 host 会拿到泛用凭据，可能缺仓库级权限（如 repo-release:rw）；查凭据必须带完整 path，或直接读 Windows 凭据管理器的仓库条目
type: pitfall
source: ZCode v29.13 发布（2026-11-01：host-only 查询拿到泛用 token，CNB API 报 10024 / missing repo-release:rw，误判为“只有只读 token”）
date: 2026-11-01
verified: 2026-11-01
topic: delivery, git
---

**经验**：`git credential fill` 的查询键包含 `protocol/host/path` 三段。只给 `host` 时，凭据助手会返回该主机的“泛用”凭据；它未必带仓库级权限。要拿某个仓库的 token，必须把仓库路径也带上：

```bash
printf 'protocol=https
host=cnb.cool
path=apigogo/zcodepro.git

' | git credential fill
```

Windows 上同一个仓库通常有两条独立条目（`cmdkey /list` 可见）：`git:https://cnb.cool` 与 `git:https://cnb.cool/apigogo/<repo>.git`，两者值不同。

**Why**：2026-11-01 发布 v29.13 时，只按 host 查询拿到泛用 token，CNB API 报 `10024 The token's resource does not match this request`；换 CNB CLI 的 OAuth token 又报 `Missing required scopes: repo-release:rw`。据此误判“现有 token 只有读权限”，额外去网页创建了一个临时发布令牌。事后核对：凭据管理器里的 `git:https://cnb.cool/apigogo/zcodepro.git` 条目 GET 200、POST 校验阶段 400（说明已通过 scope 检查），**本来就具备 repo-release:rw**。多做的临时令牌虽然用完已删，但属于不必要的凭据操作。

**How to apply**：任何“用现有凭据调仓库 API”的场景，先按**完整 URL（含 path）**查凭据；查不到再枚举 `cmdkey /list` 找仓库级条目；仍没有才考虑新建令牌。权限探测用“无效 body 的写请求”：返回 400 校验错误 = 有写权限；返回 403 scope 错误 = 没有。不要只凭一次 403 就断定“现有 token 只读”。
