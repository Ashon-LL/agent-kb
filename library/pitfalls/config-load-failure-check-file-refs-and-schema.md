---
name: config-load-failure-check-file-refs-and-schema
description: 应用报 "Invalid configuration; using defaults" 类整份配置加载失败时，先查所有"指向文件"的配置键是否存在、且内容符合该 build 的 schema——文件存在≠合法
type: pitfall
source: default 会话 2026-10-13（Codex 桌面版 + 第三方 Codex++ 注入配置）
date: 2026-10-13
verified: 2026-10-13
topic: verification
---

**经验**：日志出现 `Invalid configuration; using defaults` / `failed to resolve feature override precedence` / `failed to parse <X>_json path … as JSON` 这类**整份配置**加载失败时，按这条链查，比猜"哪个开关没开"快得多：

1. 列出配置里所有**指向文件**的键（`model_instructions_file`、`model_catalog_json`、各类 `*_file`、marketplace `source`、`notify[0]`…），逐个 `Test-Path`。
2. **文件存在 ≠ 合法**。实测两例：①键指向的文件根本不存在（第三方工具**先写引用、文件后落盘**，属竞态，隔两分钟自愈）；②文件存在且是合法 JSON，但**缺该 build 的必填字段** → 同样整份配置失败。
3. 判定"必填"要以**实测报错 + 上游源码**为准，别只看 main 分支：同一条目在一个 build 里必填、在 main 里却是 `Option` + `#[serde(default)]`（用户猜"我用的是 beta 版"方向正确）。

**Why**：症状极具误导性——表现为"设置页改不了 / 沙盒装不上 / 某功能灰掉"，看起来像权限或功能开关问题；实际是**配置解析在更底层就失败了**，下游全是连带故障。只盯表象修会在错误层反复打转（本次前两层都"修好"了，真因在第三层）。

**How to apply**：先抓一行**明确报错文本**（搜 `failed to parse` / `Invalid configuration`），再按上面三步定位；验收标准是"同一日志不再出现该行"，不是"UI 看起来恢复了"。另外第三方工具会**整份重写**配置文件：手加的段落（如 `[hooks]`）可能被冲掉，改完要复查，并确认它自己的 profile/模板是否已收进你的改动。相关：[[quantity-and-config-claim-three-errors]]、[[negative-feasibility-claims-need-a-probe]]

关联 [[injected-ui-feature-failure-check-credential-plumbing-first]]、[[run-level-failure-text-is-not-sub-operation-failure]]、[[multi-line-log-attribution-use-baseurl-not-model]]、[[model-capability-verdict-needs-official-docs-not-probes]]、[[no-assertion-without-measurement]]。
