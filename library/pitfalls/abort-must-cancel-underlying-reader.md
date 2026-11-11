---
name: abort-must-cancel-underlying-reader
description: abort/释放锁必须 cancel 底层 reader；只 releaseLock 不关流 → 超时形同虚设、上游继续生成并白扣额度，用户点「停止」无效
type: pitfall
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：客户端断开 / 超时 / 取消时，必须 **cancel 底层 reader**（或关闭 body、取消 context），
而不是只释放并发锁。releaseLock() 只归还并发额度，**不会**停掉已经在上游跑的请求。

**Why**：2026-10-26 参考工程审计：一版实现只在取消路径释放了锁，上游连接仍在跑 ⇒
用户点「停止」后模型照样生成，额度照扣；超时也不再生效（游标仍在等一个永不关心的响应）。

**How to apply**：把「取消」实现为 cancel(ctx) + body.Close() 两件事，锁释放在 defer；
验收时真的点一次「停止」，然后查上游侧是否还有该会话的后续请求/扣费记录。

相关：[[sse-stream-three-traps]]
