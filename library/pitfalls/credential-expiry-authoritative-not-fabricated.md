---
name: credential-expiry-authoritative-not-fabricated
description: 过期时刻必须取权威载体（上游 exp/expires_in），不得编造（如 now+7d）；修坏数据放在「每次 parse」层，存量才能免重登自愈
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: security
---

**经验**：凭据的过期时刻**只认上游下发的权威字段**（JWT exp / expires_in / 明确的时间字段）。
上游没给就返回 undefined（= 不知道），由「不知道 ⇒ 放行续期」处理——**宁可多刷一次，不可编造**。
同时，修正损坏凭据的逻辑要放在**每次 parse 的入口**，而不是登录入口。

**Why**：2026-10-26 参考工程审计：某实现给不返回过期时间的端点硬写 now + 7d，
而这份值同时是唯一的续期判据 ⇒ 定时续期「永远跳过」、积分自愈也「也不自愈」、UI 还显示「自动续期」，
**两条链同时卡死且日志零字**。另例：存量坏凭据若只在登录入口修，用户不重登就永远不好。

**How to apply**：parse 层对缺失字段返回 undefined 并记一条「未知」日志；
所有「修数据」的变更都问一句「存量用户不重登能不能自动恢复」，把修正放在 parse/加载路径上。

相关：[[jwt-expiry-read-exp-no-verify]]、[[credential-write-never-cross-account]]
