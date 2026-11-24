---
name: opt-in-feature-must-not-flip-default-call-path
description: 给官方函数加「可选保留/增强」语义时，必须保持默认调用路径不变；若把 opt-in 写成 opt-out，官方不传参的调用会意外走新分支并撞上官方自己的守卫
type: pitfall
topic: methodology
source: zcode改造-v29.22 归档删除失败 2026-11-16（对照果冻 3.18.0.202611161123）
date: 2026-11-16
verified: 2026-11-16
---

**经验**：给官方函数加"可选能力"（保留用量、跳过某步、增强模式等）时，默认值必须让**官方现有调用方**的行为保持不变。写成 `opt-in === true` 才启用新行为；不要写成 `!== false` 默认启用——官方调用方通常不传这个新参数，会全部走新分支。

**Why**：ZCode 改造里我方给 `purgeSessions` 加"墓碑保留用量"功能，写成 `preserve = opts.preserveUsage !== false`（默认保留）。官方 `completeSessionDeletion` 调用时只传 `(sessionId)`，不传第三参 ⇒ 全部走墓碑分支执行 `UPDATE session`；但官方库有 `session_purge_update_guard` 触发器，`state='deleting'` 时禁止 UPDATE session ⇒ 必抛 `session-data.deleting` ⇒ 归档永久删除永远卡在 `incomplete`，用户看到"成功 0/失败 3、删除尚未确认完成"。果冻最新版同一功能写成 `opts.preserveUsage === true`（默认删除），默认调用路径不撞守卫。

**How to apply**：
1. 复刻/增强官方函数时，先查**所有真实调用点**传不传你的新参数；以"不传 = 官方原行为"为默认。
2. 新分支若执行与官方不同的写操作（UPDATE vs DELETE、额外表写入），必须在测试里用**真实触发器和真实调用形状**（参数个数都一致）跑一遍；只测自己传参的形态等于没测默认路径。
3. 对照上游/竞品实现默认值时，直接抽它的判据表达式（`===true` vs `!==false`），别只看"有没有这个功能"。
4. 负控要证明旧默认会失败：把判据改回去，在同一测试夹具下必须复现原异常。

关联 [[bundle-injection-strict-scope-startup-smoke]]、[[tautological-assertion-and-self-scoped-recheck]]。
