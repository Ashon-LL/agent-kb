---
name: zcode-provider-config-group-enum-standard-personal
description: ZCode provider_config 的 config.group 是内部枚举只收 "standard-personal"，写成站点/网关分组名会 Zod 拒载整份配置（所有 provider 从 UI 消失）；站点分组隔离由令牌的 group 决定，与此字段无关
type: pitfall
source: APIShow 接入 Loomy/小浣熊供给线时误填 New API 组名（2026-10-07，同会话已二犯 provider_config schema）
date: 2026-10-07
verified: 2026-10-07
topic: zcode
---

# ZCode provider_config 的 `config.group` 只收 `"standard-personal"`

## 经验

`~/.zcode/v2/provider_config.json` 里 `providerConfigRules.providerRules[].config.group` 是 **ZCode 内部的 provider 分类枚举，唯一合法值 `"standard-personal"`**。它**不是**站点/New API 分组的透传口——用户在站点属于哪个组、能见哪些模型，**完全由所用令牌（token）的 group 决定**，与这个字段零关系。给新 provider 写 `"group": "loomy"` 这类"顾名思义"的值，Zod 校验**整份拒载**，ZCode 降级内存空配置，**所有供应商与模型从 UI 消失**。

排障与修复：
- 日志 `~/.zcode/v2/logs/<日期>.log` 搜 `[provider-config]`，ZodError 的 `path: ["providerRules", <序号>, "config", "group"]` 直接指出坏条目。
- 改回 `"standard-personal"` 即愈；配置**热加载（60s 轮询）**，不必重启——以 `provider_config.json` 的 mtime 为界数日志，之后零失败即闭环。

## Why

`providerRules[].config` 里的每个字段都是 **ZCode 自己的 schema**，不是站点语义的透传；枚举字段自创值不会"被忽略"，而是让整份配置被拒。本条与 reasoningLevel 必填（见互链）是同一失败模式的两个字段实例，症状相同（UI 全空），只有 ZodError 的 path 不同。

## How to apply

往 provider_config 写任何字段前，**先看存量条目都用了什么值**（枚举字段照抄既有取值），再按 [[zcode-provider-config-no-reasoning-enabled-schema]] 的规程做备份+原子替换+回读断言；写完用 mtime 分界确认 `[provider-config]` 日志零失败。平台侧事实见 [[zcode-platform-verified-facts]]。

相关：[[zcode-provider-config-no-reasoning-enabled-schema]]

关联 [[kb-accident-three-layer-lessons]]、[[zcode-workflow-cwd-drift-and-amend-same-name]]。
