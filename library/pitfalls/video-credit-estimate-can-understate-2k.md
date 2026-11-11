---
name: video-credit-estimate-can-understate-2k
description: APIShow MiniMax H3 的 credit_estimate 可能明显低于实际扣费；2K/10秒预估142.9、实际230.86（+87.96，约+61.6%），且实际超过200阈值也未再次拦截，不能把估算当最终价格
type: pitfall
source: 2026-11-08 APIShow MiniMax H3 月光玫瑰 2K 10 秒视频
date: 2026-11-08
verified: 2026-11-08
topic: llm, mcp
---

**经验**：`credit_estimate` 只是草稿阶段的估算，**不是最终扣费上限**。同一个 `minimax-video-h3` 任务，2K 的实际 `credit_actual` 可能比估算高出一大截；展示估算时必须说明「以实际结算为准」，不要向用户承诺「最多扣这么多」。

**Why**：2026-11-08 的 2K、16:9、10 秒任务：

- `draft_id=vd_1d14facd10d4eb0b608c58b281892111`
- `task_id=vt_6e377b6702da831b096047234134ff84`
- `credit_estimate=142.9`
- `credit_actual=230.86`
- 差额 `87.96`，约 `+61.6%`
- 实际扣费超过站点 200 阈值，但服务端没有再次返回 `confirmation_required`，任务直接 `completed`。

同一天 5 秒 2K 草稿估算为 71.45（未提交，随后取消），可见估算随时长上升，但 10 秒的实际值仍远高于线性外推。后续同一提示词/参数又生成了两次 10 秒 2K 任务（`vt_fa02355258e8f0715a3946ca477927c2`、`vt_77b987d1afdcc672c3694bea4c26224d`），`credit_actual` 都是 230.86、估算都是 142.9，三次一致，说明这不是单次抖动。不能把这里的比例当成所有模型/分辨率的固定公式；这是该端点、该模型、2K 档的三次一致实测。

**How to apply**：
1. 展示草稿时同时给出「估算」和「实际以结算为准」，不要用「最多 142.9」这类承诺。
2. 2K/高分辨率任务按估算留出至少 50% 的额度余量；若账户余额接近估算值，先确认余额再提交。
3. 实际超过 `ConfirmAboveCredit` 阈值但估算低于阈值时，服务端可能不会二次拦截；不要依赖「实际超阈会被拦」来保护余额。
4. 任务完成后必须读取 `credit_actual` 并与估算并列记录；不要只记估算。
5. 想控制成本时优先 768P，或在正式提交前用小分辨率/短时长做一次价格对照；但不要把单次对照写成永久定价规律。

> ⏰ 时效状态（2026-11-08 记录，**已实测一次 2K 10 秒任务**）：本机 `apishow-video` → MiniMax H3，估算 142.9、实际 230.86，实际超出 200 阈值但未二次拦截。
> ⚠️ 用前必须实测：用 `apishow_prepare_video` 看 `credit_estimate`，提交完成后用 `apishow_watch_video(task_id)` 读 `credit_actual`，两者并列核对。

关联 [[video-terminal-failure-needs-upstream-error-before-retry]]、[[negative-prompt-is-also-moderated]]、[[no-assertion-without-measurement]]。
