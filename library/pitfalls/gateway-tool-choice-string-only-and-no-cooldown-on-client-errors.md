---
name: gateway-tool-choice-string-only-and-no-cooldown-on-client-errors
description: OpenAI 兼容网关/上游的三条硬教训——tool_choice 形态可能只收字符串（对象形态=param invalid）；客户端参数错误绝不能当账号故障冷却（一次请求打停整池 10 分钟）；隔离触发参数用绕开账号池的上游直发矩阵
type: pitfall
source: APIShow / HITZY2002 codearts2api 网关 tool_choice 根因修复（2026-10-06 端到端实证 + 上游 PR#6/Issue#7）
date: 2026-10-06
verified: 2026-10-06
topic: methodology
---

# 网关侧 tool_choice 形态 + 参数错误处理（2026-10-06，CodeArts2api 实测）

## 教训一：上游对 tool_choice 可能只收字符串形态

OpenAI 客户端常见对象形态 `{"type":"function","function":{"name":"get_weather"}}`，但
部分上游（实测 CodeArts InferHub /api/v2/chat/completions）**只接受字符串
`auto`/`required`/`none`**，对象形态直接返回通用参数错误：

    InferHub.001001005.400 The request param is invalid, Please check it

- `tools` 数组本身可透传、`max_tokens` 可透传，唯独 `tool_choice` 对象被拒。
- 网关若把 function 模式翻译成对象形态原样发出 → 每次带工具调用都失败。
- **修法**：网关侧收敛——function 模式映射为 `"required"`（保留「必须调用工具」语义，
  单工具场景等价于强制），永不发对象。

## 教训二：客户端参数错误绝不能冷却账号池

错误链：参数错误 → `embeddedSSEError` 不识别 → 默认映射 502 → `handleUpstreamError`
对 `Status>=500` 一律 CoolErr 冷却 10min → 请求循环轮转所有账号 → **整池 503 十分钟**。

- 一次客户端形状错误（换账号结果相同）不该惩罚任何账号；应直接回 400 结束轮转。
- 检查清单：识别客户端错误族（param invalid / request param is invalid / 具体错误码）
  归 400；handler 层短路（不调 handleUpstreamError、不 NoteError、不轮转）。
- 同类既往：并发/TPM 类瞬时错误归 429 不冷却（TM.00001041）；模型级错误归 400 不冷却
  （not registered / benefit not found）。

## 教训三：隔离触发参数用「绕开账号池的上游直发矩阵」

要定位「哪个参数触发上游报错」，别用网关 API 逐变体试——**每个坏请求都会冷却整池**。
做法：一次性容器（如 `golang:1.24-alpine` 挂载网关源码 + auths）直接调上游鉴权函数，
按「基线 → 单加一个参数 → 组合」矩阵发请求，完全不碰账号池状态、无冷却风险。

## 附带：SSE 探针解析坑

OpenAI 流式 chunk 的 content/tool_calls 嵌在 `choices[0].delta` 里，不是顶层 `delta`。
取顶层会把正常的多轮续跑误判成「第二轮无正文输出」——先在帧级 dump 一次再写校验。

**相关**：[[newapi-model-limits-column-is-csv-not-json]]（同类「上游只认一种形态，写错形态全挂」）、
[[redacted-get-full-put-wipes-secrets]]（同类「客户端侧误操作打停全站」）

## 追加实测（2026-10-06，CodeArts InferHub，同一错误码的两个新触发点）

同一 `InferHub.001001005 The request param is invalid` 还有两个与 tool_choice 无关的触发点，且都可能被误判为「模型/账号问题」：

1. **max_tokens 超上限 → 001001005**：上游硬上限 **65536**（65536/65535 HTTP200；65537、80000、96000、128000、131072、384000 全 400）。客户端框架若在 `optionSpecs.maxOutputTokens.max` 配了超限值，agent 模式会原样拉满发送 → 每次必 400。**边界必须二分实测**（128000 这种「合理猜测值」也是拒的）。
2. **空 arguments `""` → `InferHub.invalid_argument.400`**（另一个错误码）：网关把空字符串归一成 `{}` 后直接 HTTP200——**修复坏参数比报错更好**。
3. 两类错误都曾走 502 → 冷却整池 10min。客户端参数类错误码必须**集中登记到一个谓词**（tool_choice/invalid_argument/param invalid…），新错误码出现时先问「这是不是又是客户端形状」。

**排查套路修正**：全链路小请求通 + 真实请求形状挂 ⇒ 差异字段即根因（用 model-io/日志抓真实 body 逐字段二分），不要在「模型不兼容/历史内容非法」等假设上空转。
