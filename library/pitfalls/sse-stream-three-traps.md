---
name: sse-stream-three-traps
description: SSE 流式链路三坑：保活用注释行（别发明空 delta 心跳）、首块预读阶段要看门狗（io.ReadFull 可无限阻塞）、读空闲预算必须低于链路最紧一环
type: pitfall
source: APIShow docs/分析/20261023_SSE流式保活业界做法.md（2026-10-23 源码级调研 vLLM/LiteLLM/new-api/one-api/llama.cpp）
date: 2026-11-10
verified: 2026-11-10
topic: api-gateway
---

**经验**：SSE 转发链路的三个高频坑——
① **保活用注释行**（`: keep-alive\n\n` / `: ping`），不要用空 delta 心跳
（`{"choices":[{"delta":{}}]}`）：空 delta 对「内容级计时」的客户端无效，且被部分网关直接丢弃；
② **首块预读阶段必须自带看门狗**：`io.ReadFull(resp.Body, 4096)` 在「上游已回 200 头但 body 不吐字节」时
可无限阻塞，看门狗要在预读**之前**就起；
③ **读空闲超时预算必须低于链路最紧的一环**（如 nginx proxy_read_timeout 300s、上游 STREAMING_TIMEOUT），
否则超时被上游/代理先触发，本层的取消逻辑永远轮不到。

**Why**：2026-10-23 源码级调研 vLLM/LiteLLM/new-api/one-api/llama.cpp：保活形态主流就是注释行；
new-api 在**发上游请求之前**就设 SSE 头并起 ping（覆盖请求准备与重试期），三家都不等 body 攒够字节。
首块预读无看门狗是 relay-go 读码发现的真实缺口（gateway.go 预读段无超时，看门狗在其后才创建）。

**How to apply**：写 SSE 转发时对照这三点自检；阈值配置统一从链路最小值推导，并给预读段单独设看门狗；
改动后用一个「200 头但不吐字节」的桩上游验证看门狗真的触发。

相关：[[abort-must-cancel-underlying-reader]]、[[error-classify-by-latency-and-layer]]
