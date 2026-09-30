---
name: llm-context-window-is-input-plus-output
description: 【作用域=AstrBot tdp 网关 + qwen3.8-27b，跨项目未验证】该上游按「输入 token + 请求的 max_tokens ≤ 模型硬窗口」校验，两者相加超限必拒；配 max_tokens 前必须知道硬窗口并把输入闸门和输出上限拆开算，验收探针要用接近真实生产的输入体积（小 prompt 会掩盖超窗）
type: pitfall
source: APIShow AstrBot v4.28.2 tdp 网关（qwen3.8-27b，2026-09-29 生产 400 报错定谳 + models.dev 官方规格交叉验证）
date: 2026-09-29
verified: 2026-09-29
---

**作用域（先读这条）**：本条只定谳于 **AstrBot 的 tdp 网关 + qwen3.8-27b 这一个组合**（2026-09-29 生产 400 打脸 + models.dev 官方规格交叉验证）。OpenAI 兼容上游**是否都做同样的 `input + max_tokens ≤ window` 校验，未验证**——别的网关可能 clamp 而不是拒、可能只校验 `max_completion_tokens`、也可能压根不校验。⛔ **当成"通用 OpenAI 规范"套到别的项目前必须实测一次**；正文里的数字和字段名都是 AstrBot/tdp 语境。
- ⚠️ **已发生的误用（2026-09-30）**：迁移 DSH 桌面端配置时，我看到阶跃星辰2 的 `step-5-preview` 是 `maxTokens 1000000 == contextWindow 1000000`，直接套用本条预判"任何有输入都会在校验阶段 400"，并把 maxTokens 主动压到 65536。用户指出这是 AstrBot 的经验、不是 DSH 的——**StepFun 是否这么做从未实测**，我下的是未被验证的推论。教训见 [[kb-entry-source-scope-is-the-boundary]]。

**经验**：AstrBot 的 tdp 网关（qwen3.8-27b）按 **`实际输入 token + 请求的 max_tokens ≤ 模型硬窗口`** 校验请求。所以「把 max_tokens 顶到模型上下文大小」这种直觉是错的——输入必然占一部分，两者相加会超窗被拒。报错文案形如：

```
This model's maximum context length is 262144 tokens. However, you requested 250000 output
tokens and your prompt contains at least 12145 input tokens, for a total of at least 262145
tokens. Please reduce the length of the input prompt or the number of requested output tokens.
(parameter=input_tokens, value=12145)
```

注意它报的是**请求的 max_tokens**，不是模型实际生成量。也就是说哪怕最终只生成 50 个 token，只要 `输入 + max_tokens > 窗口` 就先拒为 400。

**两个维度必须分开**：官方模型元数据（models.dev）把规格列成 `limit = {context: 上下文窗口, output: 最大输出}` 两个数。但很多应用框架的旋钮语义和这个不一致——例如 AstrBot 的 `max_context_tokens` 实际是**输入闸门**（压缩判定按 `count_tokens(输入消息列表) vs max_context_tokens`），不是总量。旋钮名字像「上下文」就以为是窗口，是典型坑。

**Why**：AstrBot 里 tdp（qwen3.8-27b）配 `max_context_tokens=250000` + `max_tokens=250000`，合计 500000；模型硬窗口 262144。结果只要真实会话输入超过 12144 token 就必 400——而 bot 带记忆+工具 schema 的常规会话已经 12145 token，等于**几乎每次都炸**。修法：`max_context_tokens=180000`（输入闸门，压缩在 153000 触发）+ `max_tokens=65536`，合计 245536，留 16608（6.3%）给分词误差。

**第二个坑（更阴险）**：我用 `1+1 等于几` 这种十来个 token 的小 prompt 做验收探针，250000+10 < 262144 直接放行，于是**误判「上游接受 max_tokens=250000」并上线**，被生产 400 打脸。**小 prompt 会系统性掩盖 input+output 超窗**——因为超窗与否取决于输入体积。验收必须用接近真实生产的输入体积（本项目用 12559 字符 ≈ 1.5 万 token 复现失败量级，3/3 通过才算数）。同类相邻教训见 [[config-field-name-is-not-spec-read-consuming-code]]（配置旋钮语义与字面名不符）。

**How to apply**：①配 `max_tokens` 前先查清模型硬窗口，且**查官方来源**（模型厂官方文档 / models.dev 这类官方元数据聚合），别信第三方 UI 提示或网关 `/models` 返回（很多网关全填 `None`）；②框架旋钮按**消费该字段的源码**判定语义，区分「输入闸门」与「总量」；③按 `输入闸门 + max_tokens ≤ 硬窗口` 反解切分，留 5~10% 余量给分词误差；④「自动填充 / 留 0 让框架推断」要先确认框架的元数据源真拉到了——框架可能静默退回一个小得多的 fallback（本次 AstrBot 容器内 `LLM_METADATAS` 实测为空，`max_context_tokens=0` 会退回 fallback 128000 而非真实 262144，导致过度压缩）；⑤**验收探针的输入体积要贴近真实生产**，别用最小 prompt；⑥思考型模型的 `max_tokens` 还要额外考虑 reasoning 与正文共预算，见 [[reasoning-model-max-tokens-shares-budget]]——两个约束叠加时输出上限往往比直觉小得多。
