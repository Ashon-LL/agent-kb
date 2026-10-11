---
name: custom-llm-endpoint-capabilities-default-false
description: 自建/中转的 LLM 端点被产品按「未知兼容端点」处理时，工具调用等能力默认全关且零报错——症状是「模型把工具调用写成正文/工具不可用/产物没落盘」；修法是显式声明能力（openclaw: compat 挂 model 条目），改完必须请求体捕获自证
type: pitfall
source: MH-Agent-Open / openclaw 2026.9.4 自定义 provider（CUMCM A 题实弹，2026-09-30）
date: 2026-09-30
verified: 2026-09-30
topic: llm
---

**经验**：当 LLM 客户端**无法从 baseUrl 认出模型身份**（自建网关、中转站、自定义 provider id）时，
它会按「未知兼容端点」处理，而这类端点的**能力默认值是 false**——不是「未知就放行」。
最贵的一条是 `supportsTools=false` ⇒ **请求体里根本不发 `tools` 数组** ⇒ 模型无从返回结构化
`tool_calls`，于是把「我要调用哪个工具」当正文写出来。症状层层伪装：日志里 `Assistant reply
looks like a tool call, but no structured tool invocation was emitted`、回合没有工具、脚本没落盘、
「编译结果未知」——**全程零配置错误、零警告**。

**Why**（2026-09-30 实测，一整轮真实任务的失败面 100% 在这里）：

- 官方 schema 原文：openclaw 对未知兼容端点，`supportsTools` / `supportsJsonSchemaResponseFormat`
  **Default: false**。而本仓 provider id 是自定义的 `mh-upstream`、baseUrl 指向中转域名 ⇒ 命中该默认。
- ⭐ **必须做反证再动手**：直连**同一上游、同一模型**，手工带上 `tools` 数组发一次 ⇒ 稳定返回
  `tool_calls`（thinking 开 / 关 / 不传三态全正常，reasoning_tokens 205/0/202）。反证一出，
  故障面就 100% 落在客户端的能力声明，上游无需背锅。**没有这条反证，你只能猜**。
- ⛔ **声明位置也会被拒**：openclaw 的 `compat` 挂在 provider 层会被 loader 拒
  （`Unrecognized key: "compat"`），**必须挂在 model 条目上**（`models.providers.*.models[].compat`）。
- ⛔ **能力声明之间会互相废掉**：开 `supportsJsonSchemaResponseFormat`（对应上游
  `response_format: {"type":"json_object"}`）后，同请求体重放**模型不再返回 `tool_calls`** ⇒
  等于把关掉工具调用换了个名字。⇒ 结构化输出默认不勾选，只用于纯生成场景。
  同族约束：不少上游要求 prompt 里必须出现 `json` 关键词，否则 400；且官方明确不建议
  与思考模式同开。

**How to apply**：

1. **先分清「端点认不出」与「端点真不支持」**：读客户端对该字段的 **Default 值**（不是看有没有这个
   字段）。默认 false 的字段，**不显式声明 = 关闭**，与「留空用默认」在语义上完全相反。
2. **能力声明要成组给**，不能只给显眼的那一个：工具调用、多模态输入模态、思考/推理开关、
   思考档位集合、结构化输出、API 协议适配器（openai-completions / anthropic-messages）——
   每一项都对应「不声明就退回目录默认」，而目录默认对未知端点一律是保守值。
3. ⛔ **别把「不表态」和「声明为不支持」写成同一件事**：UI 上「不勾选」应映射为**不写该键**
   （保持现值），只有用户显式表达「不支持」才写 `false`。写成 `{feature:false}` 会把「没勾」
   变成「声明不具备」，语义不同。
4. **改完必须自证「真的改到了」**，且要在**真实生成物**上验，不要看代码或日志：
   - 打开客户端**实际写出的配置文件**（不是内存对象），断言 `compat.supportsTools is true`；
   - 再让真实步骤跑一轮，确认产物落盘。
   - ⚠️ 这一步还防另一类事故：客户端**有多个副本**（dev 仓库 / 安装区 / 用户跑的实例），
     你改的那份不等于在跑的那份。同一案例里安装区的旧代码重写了配置文件、把新声明抹回 `null`，
     且**无任何报错**。
5. **配套教训：JSON 结构化输出不是「更强的工具调用」**，它是另一条互斥路径，同时开会废掉工具。

**相邻**：字段名/注释不是规格见 [[config-field-name-is-not-spec-read-consuming-code]]；
日志文案同样不是规格见 [[log-text-is-not-spec-read-emitting-code]]；
自定义 provider 的配置生成逻辑见（该条目已不在库中，链接暂缺）。

关联 [[disguised-client-gate-needs-placeholder-tools-merged-not-replaced]]、[[empty-config-is-not-missing-feature]]。
