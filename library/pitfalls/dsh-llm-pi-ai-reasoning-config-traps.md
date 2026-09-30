---
name: dsh-llm-pi-ai-reasoning-config-traps
description: DSH（deepseek harness 桌面端）自定义网关走 llm-pi-ai 行的 config.providers；reasoningEfforts 缺 off 会让用户无法关闭思考、profile 级 reasoning 在混合路由上直接抛 UNSUPPORTED_REASONING_EFFORT、maxTokensField 默认已是 max_completion_tokens、路由名带连字符会让推导出的凭证引用名非法、Config.validate 是透传的且返回 issues 不抛异常
type: pitfall
source: ZCode 启用模型迁入 DSH（C:\Software\deepseek harness 0.2.0-rc.2，2026-09-30，8 路由 19 模型）
date: 2026-09-30
---

**经验**：给 DSH 配自定义网关时，六处行为跟直觉相反，且大部分零报错。写入位置是 `~/.dsh/profiles/desktop/cordis.patch.yml` 里新增一行 `- id: llm-pi-ai` / `name: "@deepseek-ai/dsh-llm-pi-ai"` / `config.providers.<路由>: ...`（`~/.dsh` 下没有 settings.yaml，profile patch 就是唯一落点；`cordis.yml` 是 `[]` 且注释写明"改 patch 不改它"）。行按 `id` 寻址、后写覆盖前写，**补丁替换整行 config 而不是合并**，覆盖时要重述全部字段。

**Why**：全部从本机装的 `app.asar` 解包源码实证（`@deepseek-ai/dsh-llm-pi-ai/lib/index.js` 与 `@earendil-works/pi-ai/dist/api/openai-completions.js`），不是猜的：

- ⭐ **`reasoningEfforts` 缺 `off` = 用户关不掉思考**。`resolveModelReasoning` 把未声明的等级钉成 `null`，而 `getSupportedThinkingLevels` 里 `mapped === null → return false`（排除出可选列表）。所以不写 `off`，UI 就没有"关闭"这一档；此时派发"无等级"走 deepseek 分支的 `thinkingLevelMap?.off !== null` 判定为 `null !== null` 为假 → 什么都不发 → 网关用默认（通常是开启思考）。**每个推理模型都必须显式写 `off:`**。
- ⭐ **`off: null`（YAML 里 `off:` 空值）是源码注释明确允许的唯一例外**："A declared `off` with no value is the one exception: it stays absent from the map, which pi-ai reads as 'supported, send nothing'"。此时 `thinkingLevelMap.off` 是 `undefined`，`undefined !== null` 为真 → deepseek 分支正常发 `thinking:{type:"disabled"}`。即：off 既进可选列表，又能真正关掉思考。非 `off` 的等级给 `null` 会直接 `invalid()` 报错。
- ⭐ **`maxTokensField` 不要随手设 `max_tokens`**。pi-ai 默认就是 `max_completion_tokens`，而 ZCode 对 `openai-completions` 的权威默认模板也是 `{'max_completion_tokens': maxOutputTokens}`（见 `ZCode\resources\config\provider\zcode-builtin.json` 的 `modelApiRules`）。照搬 ZCode 就**全部省略该字段**；`anthropic-messages` 是原生 `max_tokens` 且其 compat 门控**不提供** `maxTokensField`，写了会被 `assertOfferedCompatFields` 拒。
- ⭐ **路由名不能带连字符**。DSH 模型页按 `<ROUTE>_API_KEY` 推导凭证引用名，而 `REF_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/` 不含连字符 ⇒ 路由名 `stepfun-2` 推导出的 `STEPFUN-2_API_KEY` 非法。用 `stepfun2` 这类连写。`KEY_SEGMENT_PATTERN = /^[a-z][a-z0-9-]*$/` 允许连字符，两个规则看起来都满足，冲突只在运行时暴露。
- ⭐ **`"openai"` 不是 pi-ai 的 thinkingFormat 分支**。`openai-completions.js` 的 if/else 链里只有 `zai / qwen / qwen-chat-template / chat-template / baseten / deepseek / openrouter / ant-ling / together / string-thinking`，之后落到默认的 `params.reasoning_effort = ...`。所以 `thinkingFormat: "openai"` 与不写等价。DeepSeek 兼容网关必须用 `deepseek`，它发 `thinking:{type:enabled|disabled}` + 选级时附 `reasoning_effort`，正好是 ZCode 默认 openai-chat-completions 模板的两个主字段。
- **profile 级 `reasoning` 在混合路由上会抛错**。`resolveReasoningLevel` 对不在该模型可选列表里的等级直接抛 `UNSUPPORTED_REASONING_EFFORT`，而一个路由下多个模型的等级集合不同 ⇒ **一律不写 profile 级 `reasoning`**，只在模型级写 `reasoningEfforts`。`rejectRemovedFields` 还禁止 profile 级 `provider`、`maxRetries`、`maxRetryDelayMs`。
- ⚠️ **`Config['~standard'].validate` 是透传的且不抛异常**。返回 `{issues: [...]}`，必须查 `issues.length`；未知字段（实测 `reasoningEffortz`）和非法 `apiKeyEnv` 名都放行。⇒ 只能靠它抓"字段类型/枚举错"，字段名拼写和引用命名要自己按正则复查。它同时把 `providers` 从输出里抹掉（`.volatile()`），说明**补丁文件才是持久来源**，不是 validate 的返回值。
- **anthropic-messages 复现 ZCode 的 adaptive 写法用 `forceAdaptiveThinking: true`**：pi-ai 的 anthropic 分支在该开关下发 `thinking:{type:"adaptive"}` + `output_config:{effort}`，与 ZCode `zcode-builtin.json` 给 `anthropic-messages` 的默认模板字节级一致。这是 anthropic compat 门控里唯一跟思考有关的开关。

**How to apply**：

1. 配自定义网关先解包 `app.asar` 读 `dsh-llm-pi-ai/lib/index.js`，抄 `PROTOCOLS`、`MODALITIES`、`THINKING_LEVELS`、`SUPPORTED_THINKING_FORMATS`、`COMPAT_GATES` 这几个常量——它们才是规格（见 [[config-field-name-is-not-spec-read-consuming-code]]）。
2. 只发 3 种协议：`openai-completions` / `openai-responses` / `anthropic-messages`；`MODALITIES` 只有 `text` 和 `image`，**视频/PDF 能力必须丢弃**，否则会声明一个 pi-ai 不认识的模态。
3. 每个推理模型写 `off: null` + 只声明 ZCode/网关真实支持的等级；等级名一律映射到自身（`high: high`）。ZCode 的 `disabled`→`off`、`enabled`→`low`（DSH 无"开启但不指定强度"的等价档）。
4. `reasoningEfforts: false` 表示非推理模型（UI 不显示思考开关）；省略该字段则回落到 pi-ai 内置目录的能力，别依赖它。
5. 写完必须双验：① 用 DSH 自己的 `dsh-llm-pi-ai` `Config['~standard'].validate` 查 `issues`；② 凭证文件用 `@deepseek-ai/dsh-credentials-local` 的 `parseCredentialsDocument` 验（返回的 `refs`/`records` 是 **Map**，`Object.keys()` 拿到空数组，要用 `.size` 和 `for of` 读）。两者都过才算数。
6. 路由 id 避开内置目录 46 个 id，也别碰 `deepseek-official` / `deepseek-account`（已由别的适配器注册，复用会导致插件加载失败）。
7. 改完备份两份文件再动手；DSH 有配置文件监视器，凭证文件热加载，但 profile 是在启动时合成的 ⇒ **重启 DSH 生效**。
8. ⛔ **别把别的项目的预算教训直接套过来**：`maxTokens` 顶到窗口大小会不会 400，取决于**该上游**是否校验 `input + max_tokens ≤ window`。[[llm-context-window-is-input-plus-output]] 只定谳于 AstrBot 的 tdp 网关 + qwen3.8-27b，**DSH 各网关未验证**——实测过再动。同理思考型模型的 `max_tokens` 与 reasoning 共预算（见 [[reasoning-model-max-tokens-shares-budget]]）也要本地实测。用户已设的值被改动后，先确认是不是有意为之（2026-09-30 我把用户有意设的 65536→1000000 反推成"踩坑"去劝阻，方向反了）。

**相邻**：字段名不是规格见 [[config-field-name-is-not-spec-read-consuming-code]]；ZCode 侧的 reasoning schema 事实见 [[zcode-provider-config-no-reasoning-enabled-schema]]。
