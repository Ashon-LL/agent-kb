---
name: upstream-queue-error-must-be-429-not-hard-403
description: 上游「排队中」(10605/isQueued/retryAfterSeconds) 被网关当硬 403 透传会让客户端判 auth_failed 不重试直接死——正确做法是切号试遍、全号耗尽才返回 429+Retry-After；且要确认错误是走 HTTP 层还是装在 200 建流的 SSE 信封里，改错分支等于没改
type: pitfall
source: APIShow / qoder 网关 403-10605 排队修复（2026-10-05 端到端实证）
date: 2026-10-05
verified: 2026-10-05
topic: api-gateway
---

**经验**：上游返回「服务排队/暂不可用」语义（如 `code=10605, isQueued=true,
queueType=p3, serviceAvailable=false, retryAfterSeconds=30`）时，**绝不能原样当 4xx 硬错误
透传给客户端**——客户端（ZCode/New API/各类 SDK）普遍把 403 判为凭据失效 `auth_failed`
且 `retryable=false`，直接失败不重试。正确链路：**① 先切号试遍**（队列是「账号+模型槽」
维度，换号常常有用）；**② 全号耗尽才对��返回 `429 + Retry-After`**（秒数取自上游
`retryAfterSeconds`），让客户端退避重试而不是死。

**Why**（2026-10-05 qoder 网关实测，5 处漏洞）：

- **⛔ 「错误码 403」≠「HTTP 403」**：上游是 **HTTP 200 建流、403 装在 SSE 信封里**
  （日志 `rejected via envelope`）。我第一版补丁改在 `open_upstream` 的 HTTP 403 分类
  分支——那个分支永远不命中，改完实测仍 403。**先 grep 日志确认错误从哪进来，再动手**。
- **⛔ 别假设「排队=模型级、换号无用」**（我当时的假设，用户当场质问「为什么不切号」）：
  实测日志证明切号一直在发生且**有用**——qwen 两模型两号都排队，但 glm 模型
  019f922e 排队 → 换 019fd280 **成功 200**。⇒ 队列是「账号+模型槽」维度。
- **真 bug 是「重开产生的 RateLimited 被原信封吞掉」**：重试循环里
  `except Exception: raise exc`（无条件回退原始错误）把真实结论丢掉，
  客户端拿到硬 403。共 5 处同型漏洞：聚合重试函数的重开分支、chat/responses
  非流式调用点（缺 `except RateLimited` → 被兜成 502）、chat/responses 流式内联
  reopen、流式块整体（在 open_upstream 的 try 之外，冒到最外层断连）。**grep
  `except RateLimited` 数一遍调用点，别只改一处。**
- 验证手法：① 等真实排队窗口（本次恰好撞上）；② 临时注入把任意信封改写成排队强制走
  分支，验完立即回滚并 grep 确认注入计数为 0。⛔ 注入前**必须先备份**——我第一版注入
  写成 `def _FORCE_QUEUE_VERIFY = True` 报 SyntaxError 直接把服务打挂，靠备份回滚恢复。

**How to apply**：

1. 拿到上游错误先定位载体：HTTP 状态码？还是 200 流里的信封（`statusCodeValue`）？改错分支等于没改。
2. 排队类错误先**切号试遍**（保留原有重试/轮换逻辑），不要因为「像是模型级」就跳过换号。
3. 全号耗尽时抛既有的限流异常（`RateLimited` 之类），由统一出口渲染 **429 + Retry-After**，
   并确保**每个调用点都有对应捕获**（`grep -c` 核对）。
4. 队列冷却用**模型级**（`model_cooldowns[model]`），别用账号级——否则一个模型的排队
   会把该号所有模型一起封掉。
5. 临时注入验证必须：先备份 → 改完 `py_compile` → 重启后确认进程启动时间晚于文件 mtime
   （文件更新≠代码在跑）→ 验完回滚并 grep 注入标记归零。

**相邻**：同 [[pool-credit-priority-keep-serving-and-billing-account-tied]]（切号语义）；
「文件更新≠代码在跑」见 [[file-change-not-code-running]]；「日志字面语义不是规格」见
[[log-text-is-not-spec-read-emitting-code]]；「别拿单一关键词当全量」见
[[env-claims-must-be-reverified]]。

关联 [[upstream-queue-blind-wait-backfires]]。
