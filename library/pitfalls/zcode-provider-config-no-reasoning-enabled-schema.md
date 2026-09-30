---
name: zcode-provider-config-no-reasoning-enabled-schema
description: ZCode provider_config.json 没有 reasoning.enabled 字段，schema 只有 optionSpecs.reasoningLevel.{values,map}；要禁用 reasoning 必须写 map 为空，否则运行时会发出 reasoning.effort 被网关拒收
type: pitfall
source: APIShow 接入 tokenrhythm 网关 neohorse-1-9b（2026-09-21）——网关报 400 unknown request field: reasoning.effort
date: 2026-09-21
verified: 2026-09-21
tags: [zcode, provider_config, reasoning_effort, schema]
---

# ZCode provider_config.json：禁用 reasoning 不能靠 reasoning.enabled，必须用 reasoningLevel.map

## 踩坑

在 provider_config.json 的 modelConfigRules.providerModelRules 里写了：

``json
{
  "modelId": "neohorse-1-9b",
  "config": {
    "reasoning": { "enabled": false }
  }
}
``

然后跑 tokenrhythm 网关的 neohorse-1-9b，继续报：

`
400 unknown request field: reasoning.effort
`

## 根因

**ZCode provider_config.json 的 schema 里根本没有 reasoning 这个字段**。

官方 schema（kingsword09/zcode-cli blob HEAD docs/PROVIDER_CONFIG.md）明确列出的 providerModelRules 下 model.config 合法字段只有：

- enabled
- properties.*（contextWindow / supportsMidConversationSystem 等）
- optionSpecs.reasoningLevel.{values, map}
- optionSpecs.maxOutputTokens.{max, map}

运行时解析器看到 reasoning 键就跳过（既不报错也不生效），继续用 catalog 默认的 reasoningLevel.map（通常是 {"reasoning_effort": reasoningLevel}）——所以不管你写没写 reasoning.enabled=false，只要没写 reasoningLevel.map，运行时照样往请求里塞 reasoning 字段。

## 正确写法

``json
{
  "modelId": "neohorse-1-9b",
  "providerId": "new-provider-4",
  "config": {
    "enabled": true,
    "optionSpecs": {
      "reasoningLevel": {
        "values": ["disabled"],
        "map": "{}"
      }
    }
  }
}
``

关键三点：

| 字段 | 值 | 含义 |
|---|---|---|
| reasoningLevel.values | ["disabled"] | UI 下拉里只给用户 disabled 选项 |
| reasoningLevel.map | "{}"（字符串！不是对象）| 运行时把整段 reasoning 映射替换成空对象 |
| 两者都要 | 缺一不可 | 只写 values 不写 map 就用 catalog 默认 map |

## reasoningLevel.map 的三种典型值（来自官方 provider.example.json）

| 场景 | map 字符串 | 运行时行为 |
|---|---|---|
| 永远不发 reasoning | "{}" | 请求体里没有任何 reasoning 字段 |
| 条件发（推荐）| 'reasoningLevel == "disabled" ? {} : {"reasoning_effort": reasoningLevel}' | disabled 时空对象，否则发 reasoning_effort |
| 直接发 | '{"reasoning_effort": reasoningLevel}' | 不管 disabled 与否都发 |

## 哪些网关需要这个保护

所有严格校验请求体字段的网关：

- tokenrhythm.studio（2026-09-21 实测拒收 reasoning.effort）
- 任何 self-hosted 网关带了 strict validator

## 额外铁律

1. **运行时会整体回写 config.json**——手改 provider_config.json 必须在 ZCode **完全关闭后**进行；运行中改随时可能被内存态回写覆盖
2. **改之前先看一眼官方 schema**：https://raw.githubusercontent.com/kingsword09/zcode-cli/HEAD/docs/PROVIDER_CONFIG.md
3. **providerConfigRules.providerRules 的 providerId 与 config.json 里的 providerId 是两套独立体系**——personal provider（new-provider-4 这种）只存在于 providerConfigRules，不会自动出现在 config.json

日期：2026-09-21
