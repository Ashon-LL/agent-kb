---
name: multi-line-log-attribution-use-baseurl-not-model
description: 多源错误日志（ZCode model.* 事件）归因必须按 context.baseURL 判线，模型名会重名张冠李戴；导出过滤 txt 会丢 baseURL，须回原始 jsonl 核对
type: pitfall
source: APIShow 吴以洋 ZCode 错误日志排查 (2026-10-08)
date: 2026-10-08
verified: 2026-10-08
topic: zcode
---

**经验**：排查 ZCode 客户端模型错误日志时，按模型名聚合统计会**张冠李戴**——不同 provider 共用同一模型名很正常（glm-5.2 同时出现在商汤官方直连和本站网关）。必须回到原始 jsonl，按每条 `context.baseURL` 判线路归属：`baseURL=https://api.apigogo.cyou/v1` 才是本站流量，`token.sensenova.cn` / 第三方 IP 网关都不是。归属字段在 `context` 内（`providerId` / `modelId` / `baseURL` / `statusCode` / `statusMessage`），顶层只有 timestamp/event/durationMs。

**Why**：本次 125 条错误里 glm-5.2 高频 429 占 80 条，若只看模型名会把深夜 glm-5.2 全线失败误判为本站故障，实则全是用户直连商汤官方 token plan（`token plan entitlement exhausted`），打向本站的只有 1 条（new-provider-2 glm-5.3-flash 46s 断连）。导出 txt 只保留部分字段会丢 baseURL，容易得出错误归因。

**How to apply**：任何"用户 ZCode 报模型错误、判断是否与我们站点有关"的排查，先 `python -c` 解析原始 jsonl，按 `context.baseURL` 聚合 request.failed 再逐条核对 statusCode/statusMessage；导出的过滤文本只当索引，不做归因依据。同一失败会以多种 event（request.failed/network.failed/retry.delay.resolved）重复出现，统计要用 request.failed 去重。