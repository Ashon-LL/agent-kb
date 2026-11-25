---
name: model-window-from-upstream-catalog-not-guess
description: 模型上下文窗口必须读上游 /v1/models 的 context_length/max_output_length，不能按模型名或印象猜；改客户端 provider 配置时要逐键验证 schema（ZCode 加 maxOutputTokens 会让整份 provider_config 被 ZodError 拒载并降级为空配置）
type: pitfall
source: APIShow 商汤源 2026-10-30：误判窗口 200K（实为 1,048,576）；ZCode provider 加 maxOutputTokens 触发 ZodError；2026-11-08 补 modelConfigRules 落点
date: 2026-10-30
verified: 2026-11-08
topic: llm
---

<!-- hook-reviewed 2026-11-16：已核对 INDEX 钩子覆盖本条 2026-11-08 新增的 modelConfigRules 落点内容 -->

# 模型窗口读上游目录，不靠猜；provider 配置逐键验 schema

## 症状

- 按「模型名像 200K」给商汤模型配窗口，实际上游 `/v1/models` 写的是
  `context_length: 1048576`（GLM-5.2/Kimi-K3/deepseek-v4.x 均为 1M，仅 sensenova-6.8-flash-lite 为 262144）。
- 给 ZCode 的 `provider_config.json` 加了一个 `maxOutputTokens`，整份配置被
  `ZodError: unrecognized_keys` 拒绝加载，运行时降级为**空 provider 配置**（供应商列表消失）。

## 根因

1. 窗口是**上游目录字段**，与模型名、宣传口径无关；不同源的同一模型名窗口也可能不同。
2. 客户端配置有严格 schema：多一个未知键就整份拒载，而不是忽略该键。
3. ZCode 的加载失败只在日志打 warn（成功静默），所以「看起来没事」并不代表配置生效。

## 怎么做

- 取窗口：`GET {upstream}/v1/models` → `context_length` / `max_output_length`，按返回值配置。
- 改 provider 配置：先备份；一次只加/改一个键；改完看 60 秒内的日志有没有
  `ZodError` / `加载失败`；失败立即回退。
- ZCode（2026-10 实测）：`properties` 不接受 `maxOutputTokens`；只改 `contextWindow` 等已存在键。
- 若已触发降级：删掉非法键并确认文件干净；ZCode 成功重载是静默的，必要时重启客户端。

## ZCode 模型元数据落点（2026-11-08 补）

`~/.zcode/v2/provider_config.json` → `config.modelConfigRules.{providerModelRules, manualProviderModelRules}[]`，按 `(providerId, modelId)` 二元组索引；每条含：

- `config.properties.contextWindow`：上下文设定值（如 1000000）。
- `config.optionSpecs.maxOutputTokens.max`：**最大输出上限**（滑块的最大值），不是「已配置值」；`properties.maxOutputTokens` 不存在/不被接受。
- 同一 `(providerId, modelId)` 可能在两个 section 各有一条；`manualProviderModelRules` 是手动加的，`providerModelRules` 随 provider 模板带出，取值时两处都要查。

要给用户导出模型设置时，直接读这里；查不到就**标注未知**，不要填默认值。

## 相关

[[trae-remote-query-500kb-bytes-silent-close]]、[[research-upstream-before-fixing]]、[[model-rename-without-rule-sync-loses-capabilities]]、[[user-input-contract]]
