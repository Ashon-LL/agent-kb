---
name: zcode-provider-config-enums-and-rules
description: config.group 只收 standard-personal；智能规则与手动规则同时声明会被 Zod 整份拒载
type: pitfall
source: 合并自 zcode-provider-config-group-enum-standard-personal, zcode-provider-config-smart-manual-rule-conflict；APIShow 接入 Loomy/小浣熊供给线时误填 New API 组名（2026-10-07，同会话已二犯 provider_config schema）; APIShow apply_zcode_linqi_provider.py 重建 new-provider-30 智能规则时重复声明 sensenova-6.8-flash(-lite)（2026-10-28，日志 [provider-config] ZodError 秒级定位）
date: 2026-10-07
verified: 2026-10-28
topic: zcode
---
**经验**：config.group 只收 standard-personal；智能规则与手动规则同时声明会被 Zod 整份拒载

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## ZCode provider_config 的 `config.group` 只收 `"standard-personal"`

### 经验

`~/.zcode/v2/provider_config.json` 里 `providerConfigRules.providerRules[].config.group` 是 **ZCode 内部的 provider 分类枚举，唯一合法值 `"standard-personal"`**。它**不是**站点/New API 分组的透传口——用户在站点属于哪个组、能见哪些模型，**完全由所用令牌（token）的 group 决定**，与这个字段零关系。给新 provider 写 `"group": "loomy"` 这类"顾名思义"的值，Zod 校验**整份拒载**，ZCode 降级内存空配置，**所有供应商与模型从 UI 消失**。

排障与修复：
- 日志 `~/.zcode/v2/logs/<日期>.log` 搜 `[provider-config]`，ZodError 的 `path: ["providerRules", <序号>, "config", "group"]` 直接指出坏条目。
- 改回 `"standard-personal"` 即愈；配置**热加载（60s 轮询）**，不必重启——以 `provider_config.json` 的 mtime 为界数日志，之后零失败即闭环。

### Why

`providerRules[].config` 里的每个字段都是 **ZCode 自己的 schema**，不是站点语义的透传；枚举字段自创值不会"被忽略"，而是让整份配置被拒。本条与 reasoningLevel 必填（见互链）是同一失败模式的两个字段实例，症状相同（UI 全空），只有 ZodError 的 path 不同。

### How to apply

往 provider_config 写任何字段前，**先看存量条目都用了什么值**（枚举字段照抄既有取值），再按 [[zcode-provider-config-no-reasoning-enabled-schema]] 的规程做备份+原子替换+回读断言；写完用 mtime 分界确认 `[provider-config]` 日志零失败。平台侧事实见 [[zcode-platform-verified-facts]]。

相关：[[zcode-provider-config-no-reasoning-enabled-schema]]

关联 [[same-concept-multiple-implementations-pick-semantics]]、[[zcode-workflow-cwd-drift-and-amend-same-name]]。

## provider_config：同一 Provider/Model 智能规则与手动规则互斥

### 经验

`~/.zcode/v2/provider_config.json` 的 `providerModelRules`（智能规则）与 `manualProviderModelRules`（手动规则，多为 UI 里逐模型手配）**互斥**：同一 `(providerId, modelId)` 二选一。批量脚本重建某 provider 的智能规则时，若该 provider 下有模型是手动配置的（典型：特殊 reasoning map，如 sensenova 的 `thinking` 字段映射），把它们也生成进去，Zod 校验直接报：

```
"同一 Provider/Model 不能同时声明智能和手动配置"
→ Personal Provider Config 加载失败，已保留磁盘状态并以内存空配置降级
```

症状与 [[zcode-provider-config-enums-and-rules]] 同族：**整份配置拒载、所有 provider 从 UI 消失**，ZodError 的 `path: ["manualProviderModelRules", <序号>]` 指出冲突条目。

### Why

手动规则往往承载智能模板表达不了的定制（特殊 optionSpecs map）；脚本的通用模板一覆盖，schema 层先拦。且脚本 diff 常只看「长度 ±N」，插入/重建会漏看；只有终检断言能兜住。

### How to apply

写任何批量改 provider_config 的脚本时，三步硬约束：

1. **生成前查手动清单**：`manual_ids = {e["modelId"] for e in cfg["modelConfigRules"].get("manualProviderModelRules", []) if e.get("providerId")==PID}`，智能规则只给不在 manual_ids 里的模型生成（`personalModelIds`/`modelOrder` 仍可包含全部模型——曝光与规则配置是两回事）。
2. **写前终检**：断言两个列表的 (providerId, modelId) 集合交集为空，冲突即拒绝写盘。
3. **写后按 mtime 验证**：日志 `~/.zcode/v2/logs/<日期>.log` 以文件 mtime 为界，`[provider-config]` 零失败即闭环（配置 60s 热轮询，无需重启 ZCode）。

排查入口：日志搜 `[provider-config]`；修复 = 从智能规则删冲突条目（手动规则是先存在户配置，保留），等一轮轮询看日志归零。

相关：[[zcode-provider-config-enums-and-rules]]、[[zcode-provider-config-no-reasoning-enabled-schema]]
