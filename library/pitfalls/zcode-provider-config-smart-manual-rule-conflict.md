---
name: zcode-provider-config-smart-manual-rule-conflict
description: provider_config 里同一 Provider/Model 同时出现在 providerModelRules（智能）与 manualProviderModelRules（手动）会被 Zod 整份拒载、UI 全空；脚本重建规则前必须先查手动清单
type: pitfall
source: APIShow apply_zcode_linqi_provider.py 重建 new-provider-30 智能规则时重复声明 sensenova-6.8-flash(-lite)（2026-10-28，日志 [provider-config] ZodError 秒级定位）
date: 2026-10-28
verified: 2026-10-28
topic: zcode
---

# provider_config：同一 Provider/Model 智能规则与手动规则互斥

## 经验

`~/.zcode/v2/provider_config.json` 的 `providerModelRules`（智能规则）与 `manualProviderModelRules`（手动规则，多为 UI 里逐模型手配）**互斥**：同一 `(providerId, modelId)` 二选一。批量脚本重建某 provider 的智能规则时，若该 provider 下有模型是手动配置的（典型：特殊 reasoning map，如 sensenova 的 `thinking` 字段映射），把它们也生成进去，Zod 校验直接报：

```
"同一 Provider/Model 不能同时声明智能和手动配置"
→ Personal Provider Config 加载失败，已保留磁盘状态并以内存空配置降级
```

症状与 [[zcode-provider-config-group-enum-standard-personal]] 同族：**整份配置拒载、所有 provider 从 UI 消失**，ZodError 的 `path: ["manualProviderModelRules", <序号>]` 指出冲突条目。

## Why

手动规则往往承载智能模板表达不了的定制（特殊 optionSpecs map）；脚本的通用模板一覆盖，schema 层先拦。且脚本 diff 常只看「长度 ±N」，插入/重建会漏看；只有终检断言能兜住。

## How to apply

写任何批量改 provider_config 的脚本时，三步硬约束：

1. **生成前查手动清单**：`manual_ids = {e["modelId"] for e in cfg["modelConfigRules"].get("manualProviderModelRules", []) if e.get("providerId")==PID}`，智能规则只给不在 manual_ids 里的模型生成（`personalModelIds`/`modelOrder` 仍可包含全部模型——曝光与规则配置是两回事）。
2. **写前终检**：断言两个列表的 (providerId, modelId) 集合交集为空，冲突即拒绝写盘。
3. **写后按 mtime 验证**：日志 `~/.zcode/v2/logs/<日期>.log` 以文件 mtime 为界，`[provider-config]` 零失败即闭环（配置 60s 热轮询，无需重启 ZCode）。

排查入口：日志搜 `[provider-config]`；修复 = 从智能规则删冲突条目（手动规则是先存在户配置，保留），等一轮轮询看日志归零。

相关：[[zcode-provider-config-group-enum-standard-personal]]、[[zcode-provider-config-no-reasoning-enabled-schema]]
