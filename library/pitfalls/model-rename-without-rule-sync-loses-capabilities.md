---
name: model-rename-without-rule-sync-loses-capabilities
description: 给 LLM 客户端（ZCode/自定义 provider）换模型名时只改清单不改能力规则 ⇒ 该模型能力声明静默丢失（supportsToolCall 归默认 false）⇒ 工具调用退化成正文；改模型名必须清单+顺序+规则三处同步
type: pitfall
source: APIShow / ZCode provider_config 2026-10-04（Trae deepseek-v4-flash→v4.1-flash 换名漏同步）
date: 2026-10-04
verified: 2026-10-04
topic: llm
---

**经验**：给自定义 provider 的模型换名（上游只供新名、旧名 502 时）如果只改了
`personalModelIds` / `modelOrder`，**漏改规则表里那条 modelRule 的 `modelId`**，
客户端按 (providerId, modelId) 二元组精确查规则时查不到 ⇒ 能力走「未知端点默认值」
（`supportsToolCall` 默认 false）⇒ 请求体不发 `tools` ⇒ 模型把工具调用写成正文。
症状伪装成「模型不会工具调用 / 工具调用退化成文本」，实为客户端没发结构化通道。

**Why**（2026-10-04 实测）：

- 客户端对自定义端点的能力默认是保守值（见 [[custom-llm-endpoint-capabilities-default-false]]）；
  模型规则的缺失与「规则里没写该字段」等价，都是默认 false，且零报错。
- 站点头部反证是关键分水岭：同一模型、同一上游、手工带 `tools` 打一发，
  返回 `finish_reason=tool_calls` + 结构化 `tool_calls` ⇒ 故障面 100% 落在客户端规则缺失。
- 换名漏同步时，旧规则变成「死规则」（modelId 不在任何清单里），与缺失规则并存，
  视觉上「规则总数没少」，极难察觉。

**How to apply**：

1. **换模型名 = 三处同步**：`personalModelIds`、`modelOrder`、`providerModelRules[].modelId`。
   缺一处即为缺陷。**新增模型同理**（加清单 + 加规则，单模型也要完整规则）。
2. **反证先行**：先带 `tools` 直打上游确认模型/站点支持工具调用，再怀疑客户端；
   反证通过后排查客户端模型规则是否存在、`supportsToolCall` 是否为 true。
3. **修法**：把死规则「改名」成新模型名（config 形状逐字节一致），一次动作同时补缺失+清死规则；
   走备份→写 .tmp→回读断言→零回归比对（除该条外其余规则逐条序列化一致）→原子替换。
4. **验证**：客户端需重启会话才重读配置；真实请求日志（model-io）里 tools 计数 > 0 才算生效——
   但该日志默认不保留请求体（`modelIoFullRetentionEnabled=false`），查不到也别硬找。
5. **排查时先盘点同型隐患**：其它 provider 的同类模型规则也可能缺 `supportsToolCall`，
   一并列出交用户决定，不擅自改未在用的线。

**相邻**：能力声明默认值见 [[custom-llm-endpoint-capabilities-default-false]]；
「配置字段名不是规格」见 [[config-field-name-is-not-spec-read-consuming-code]]；
「环境变更陈述必须命令复测」见 [[env-claims-must-be-reverified]]。
