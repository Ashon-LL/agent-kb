---
name: jwt-expiry-read-exp-no-verify
description: JWT 过期判断只读 exp、不验签；只做「何时该续期」的判断，验签是多余成本且会因上游密钥轮换误判
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: security
---

**经验**：在「决定要不要续期」的场景里，JWT 只解码读 exp，**不做签名验证**。
验签是信任判定，续期判据只需要时间；上游自己的网关很多时候也只按 exp 判。

**Why**：2026-10-26 参考工程审计：自验签会引入密钥来源与轮换问题——上游轮换密钥后，
本地持有的旧公钥会让**本来有效的凭据被误判为无效**，触发不必要的续期/清号。

**How to apply**：把「时间判据」与「信任判据」分开：续期调度只读 exp；
需要信任判定的场景（鉴权中间件）才验签，并显式处理密钥轮换。

相关：[[credential-expiry-authoritative-not-fabricated]]
