---
name: opencode-model-capabilities-config
description: opencode 配置里模型能力键位：capabilities.input/output 管多模态、capabilities.reasoning{supported,toggle,effort[],budget{min,max}} 管思考等级；models.dev/api.json 默认 UA 被 403，须伪装 Mozilla；同一模型多源数据打架时按 canonical_model_id 聚合多数票再落盘
type: tool
source: 本机 OpenCode 2.x 2026-11-23 实配 67 个模型；schema 取自 https://opencode.ai/config.json
date: 2026-11-23
verified: 2026-11-23
topic: llm, windows
---

# OpenCode 模型能力字段与 models.dev 取数

## 配置键位（`~/.config/opencode/opencode.jsonc`）

- `providers.<providerID>.models.<modelKey>` 对应 schema 的 `Config.ModelEncoded`，`additionalProperties: false`。
  合法键：`modelID`、`type`、`family`、`name`、`releaseDate`、`compatibility`、`package`、
  `settings`、`headers`、`body`、`capabilities`、`variants`、`cost`、`disabled`、`limit`。
  旧版常见的模型级 `attachment` / `modalities` 不在这份 schema 的键表里（现存配置仍带着，未见拒载）。
- `limit`：`{context, input, output}`，都是整数 token 数。
- `capabilities`：`tools`(bool)、`freeform`(数组)、`input`/`output`(模态字符串数组)、
  `temperature`(bool)、`reasoning`(对象)。
- `capabilities.reasoning` 两种形状：
  - `{"supported": false}`（只允许这一个键）
  - `{"supported": true, "toggle": true, "effort": ["low","high","max"], "budget": {"min":0,"max":81920}}`
    ——`toggle`=能否开关思考，`effort`=可选档位，`budget`=思考预算 token 范围，三者都可省。
- 模型显示名与上游真实 id 不同时用 `modelID`；密钥仍走 `settings.apiKey = "{file:secrets/<f>.key}"`。

## models.dev 取数

- `https://models.dev/api.json` 约 6.9MB，顶层是 `provider -> models` 字典；模型记录含
  `modalities.input/output`、`reasoning`(bool)、`reasoning_options`（`toggle` / `effort.values` /
  `budget_tokens`）、`canonical_model_id`。
- ⚠ 用 Python `urllib` 默认 UA 直接 GET 会 **403 Forbidden**；换成
  `curl -A "Mozilla/5.0 ..."` 即 200。别因为 403 就断定站点不可用。
- 同一模型在几十个渠道各有一条记录，模态/档位经常不一致（如 `qwen3.8-27b` 有人只写 text，
  多数写 text+image）。做法：按 `canonical_model_id` 分组，对 `modalities` 与
  `reasoning_options` 各取**众数**，`reasoning` 取“任一为真”，再翻译成上面的键位。
- models.dev 未收录的冷门模型（`spark-x`、`sensenova-6.8-flash`、`neohorse-1-9b` 等）回到官方文档核对：
  讯飞 Spark-X2 只有文本 + `thinking` 三态；商汤 6.8 Flash 原生多模态（文/图/视频）；
  NeoHorse-1-9B 是 Qwen3.5-9B 纯文本微调（无视觉权重）但保留思考解析器。
- 只写配置、不调用供应商接口即可完成元数据补齐；补前后对比时把 `limit` 排除在改动之外，
  单独断言“非 capabilities 字段零改动”。

## 供应商 /models 自带的元数据（有就优先用）

同一套 OpenAI 兼容网关，不同分组/密钥暴露的字段差别很大（2026-11-23 实测）：

- `api.apigogo.cyou/v1` 的「临期优先」分组：每条带 `context_length`、`max_output_tokens`、
  `max_tokens`、`input_modalities`、`supports_image/video/tool_call`、`reasoning`、
  `reasoning_levels`、`reasoning_default_effort`，甚至每个渠道的 `sources[]`。
- 同一域名的另一把密钥（opencode 免费组）只返回 `id/object/created/owned_by`；
  `api.apigoto.com` 同样只有 id。
- `zcode-tokenrhythm` 有 `context_length`/`max_output_tokens`，但没有模态与思考字段。

所以拉取模型按「供应商元数据 > models.dev > 表单默认值」的优先级合并：
接口没给的字段保持 None（不要伪造），只有全新模型且三处都没有时才落默认值；
已有模型只覆盖接口确实返回的字段，避免把手工调过的窗口冲掉。

字段别名：上下文看 `context_length`/`context_window`/`limit.context`；
输出看 `max_output_tokens`/`max_completion_tokens`/`limit.output`；
模态看 `input_modalities`/`architecture.input_modalities`，再用 `supports_image|video|audio`
推导出 image/video/audio；思考档位看 `reasoning_levels` 或
`reasoning_options[type=effort].values`。

## 相关

[[model-window-from-upstream-catalog-not-guess]]（ZCode 的窗口/配置严格 schema 是另一套，别混用）、
[[llm-context-window-is-input-plus-output]]