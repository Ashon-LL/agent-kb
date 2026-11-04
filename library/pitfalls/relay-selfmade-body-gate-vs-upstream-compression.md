---
name: relay-selfmade-body-gate-vs-upstream-compression
description: 别在 relay 里自造请求体大小闸（阈值比上游紧、返回 429 会诱发跨源重放）；先看上游新版本怎么处理——Trae2api v1.0.6+ 是「裁剪压缩 + 413」，我们升到 v1.0.9 后 520 条消息请求由 429 变 200
type: pitfall
source: APIShow / Trae relay 入口大小闸回退（2026-10-23，本次实测 520 条消息 429→200）
date: 2026-10-23
verified: 2026-10-23
topic: api-gateway
---

**经验**：当某个上游 relay 因「请求太大」出问题，**先看该上游项目的最新版本怎么处理**，
不要在本地 relay 里自造大小闸。Trae2api-cn 从 v1.0.6 起就修了 `_bounded_remote_query`
（非 system 轮次 ≤1 时跳过校验的洞），v1.0.9 的处理是**压缩**：
`TRAE_REMOTE_QUERY_MAX_CHARS=480000` / `MAX_MESSAGES=500`，从最早的（非 system）轮次裁，
单条超大消息保留头尾截断，仍装不下才回 **413 `context_length_exceeded`**；全仓没有 429 出口。

**Why**（我方 10-21 的自造闸踩了三个坑）：
- **阈值比上游紧**（400 条 / 2MB），把「上游本来能压缩后服务」的请求判死；
- **返回 429 会诱发跨源重放**：New API `RetryTimes=10` 对 429 跨渠道重试，
  于是 2.5MB 的请求被原样打到同组其他（付费/配额）源；
- **挂错位置**：闸挂在 `_read_json_body` 上，连带误伤 IDE/raw 自有预算（80 条/12 万字符）。

**实施**：`git merge v1.0.9` → 只重放我们的业务补丁（`stop_session` 三次重试）→ 重建镜像 →
`docker compose up -d --force-recreate`；旧镜像打 tag 留回滚。实测同一账号同一请求：
520 条消息 **429 → 200**，流式/非流式全 200，站点级 4/4 通过。

**顺带**：客户端报「Provider rejected the model request」时先查**是不是我们自己的闸**——
本次就是它；而上游 413 是「客户端请求确实非法」的语义，两者不要混。
