---
name: survey-false-negatives-substring-and-enumeration
description: 盘点/逆向时两类搜索假阴性——子串误命中当结论 + 枚举前缀即边界
type: pitfall
topic: methodology
source: apishow
date: 2026-10-03
verified: 2026-10-03
---

**经验**：盘点/逆向类任务的结论用三句自查：① 每个否定结论后面，我能不能说出我枚举的那个集合是怎么来的？② 报"命中 N 处"时，我看过其中几条的上下文？③ 有没有结构化判据（枚举表/常量表/错误码表）可以先抽出来，而不是靠猜路径？

**Why**：连续两次得出错误否定结论——grep `signin` 命中 6 处全是 `outstanding` 的子串误匹配就断言"没有签到系统"；按 `/client-popups/*` 和 `/points/*` 穷举十几条路径全 404 就断言"没有领取接口"，真端点是 `client-download-reward/claim`（第三个命名空间）。单测夹具也不能借用线上配置条目——下线一个供给线会把与被测逻辑无关的测试打红。

**How to apply**：grep 命中只能当线索不能当证据，下结论前逐条看上下文片段。说"X 不存在"之前先问"我枚举的集合是谁定的"。有结构化判据（枚举值/错误码表）就别盲试 URL。
