---
name: upstream-queue-blind-wait-backfires
description: 上游「排队」类错误不是时间窗——盲打等待补丁会把快速失败变成超长挂起；先查同类 2api 项目（queue-poll/串行化/不惩罚账号）再发明机制；警惕网关自产文案（如 usage exceeds frequency limit）被当成上游证据
type: pitfall
source: APIShow / qoder 网关 qwen3.8-flash 10605 等待补丁两次试错回退（2026-10-05 实测）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
---

# 上游「排队」类错误：先查社区成熟实现，别自己发明等待机制

## 症状
网关收到上游排队/频控错误（如 Qoder 10605 isQueued）后，请求被快速失败（429+Retry-After），
怀疑是「冷却窗口没等够」，于是打「等待续上」「模型级串行闸」补丁——结果请求被挂起
185 秒仍返回同样的错误，把快速失败变成了超长挂起，对客户端更糟。

## 根因
1. **排队≠时间窗**：排队是上游并发准入控制（同一账号/模型并发超窗口即被拒），
   不是「静默 N 秒就恢复」的冷却。盲等基于错误假设。
2. **社区早有成熟答案**：同类项目（qoder2api 生态 14 个仓库）对 10605 的实现是——
   官方排队状态端点轮询（`queue/status?requestSetId=...`，SSE 保活、就绪后**同账号**重试）、
   或**串行化并发**（`QODER_MAX_CONCURRENCY=1` 默认）、且**明确排队不惩罚账号**（换号丢 prompt 缓存）。
   自己发明等待机制 = 重造轮子 + 未经考验。
3. **警惕「错误文案是自家的」**：网关合成的文案（如 `usage exceeds frequency limit`）
   是「全号冷却耗尽」的自家信号，不是上游原文；拿它当上游证据会推导出错误结论。

## 怎么避免
- 对上游「排队/限流」类错误，**先 gh 搜同源项目/同类 2api 项目**看社区怎么处理，再动手。
- 验证假设用「静默不同时长→单发」曲线，而不是一次等待就下结论。
- 变更前备份；变更后如无正面效果，立即回退并如实报告。

## 相关
[[upstream-queue-error-must-be-429-not-hard-403]]、[[file-change-not-code-running]]
