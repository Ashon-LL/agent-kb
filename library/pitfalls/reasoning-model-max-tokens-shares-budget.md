---
name: reasoning-model-max-tokens-shares-budget
description: 思考型模型的 reasoning 与正文共用同一 max_tokens 预算，预算被思考吃满时 response 的 message 里根本没有 content 键；读正文必须 .get 而不是下标
type: pitfall
source: APIShow 每日汇报脚本 daily_zhiqing_report.py（2026-09-18 03:10 生产降级实锤，sensenova-6.8-flash-lite 三档实测）
date: 2026-09-18
---

**经验**：调 OpenAI 兼容的思考型模型（`reasoning_effort` / `thinking` / 流式 reasoning 内容那类）时，**reasoning token 和正文 token 共用同一个 `max_tokens` 预算**，不是"思考额外送"。所以预算定得过紧时，思考会把整份预算吃满，`finish_reason=length`，返回的 `message` 里**只有 `reasoning`/`reasoning_content` 键，`content` 键整个不存在**。此时 `message["content"]` 直接抛 `KeyError`，不是 `None`。

**第二个坑**：思考长度是随机的，同一份预算**有时成有时败**——`reasoning_effort=low` 也可能偶发吃满。所以"我这边测着是好的"不构成证据，必须看失败率。

**Why**：09-18 每日汇报脚本 `llm_digest` 配 `max_tokens=1200` + `reasoning_effort=low`，生产跑了一次就报 `LLM 失败，降级为原文摘要: 'content'`——`KeyError`，日报发了但发的是聊天原文节选而不是摘要。三档实测把机制钉死（同一请求体，`max_tokens=1200`）：`reasoning_effort=low` → content 45 字 + reasoning 115（正常）；`reasoning_effort` 缺省 → content 44 字（正常）；**`reasoning_effort=medium` → `finish_reason=length`、`message` 键只有 `['role','reasoning']`、`completion_tokens=1200` 全部是 `reasoning_tokens`**——正文一行都没有。500 字中文正文约 700 tokens，1200 的预算只留 500 给思考，随机一点就爆了。

**How to apply**：①给思考型模型设 `max_tokens` 时按 **"预期思考量 + 正文"** 合计留（正文字数 × 1.4~1.6 估算中文 token，再乘 2~4 倍给思考余量）；②**读正文永远用 `msg.get("content") or ""`**，不要 `msg["content"]`——缺键、`null`、空串三种形态都得兜住；③拿到空正文时**去掉/降级 `reasoning_effort` 重试一次**再判定失败，而不是直接降级业务；④验证要看失败率（连跑 5+ 次），别用单次成功当证据。修复实测：预算 1200→4000 + 缺键容忍 + 一次重试后，真实 51 轮窗口 **5/5 成功**。同类相邻教训见 [[config-field-name-is-not-spec-read-consuming-code]]（改了配置旋钮却不生效）。
