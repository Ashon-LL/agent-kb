---
name: prefer-narrow-native-switch-over-broad-global-or-plugin
description: 第三方应用要关掉某个对象的行为时，先读源码找最小作用域的原生开关；别写插件，也别动全局开关
type: workflow
source: apishow（2026-10-05 AstrBot 单会话静默 10 小时）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
---

**经验**：诉求「让对象 A 不再做 X」而 A 只是众多同类中的一个时，按这个顺序找机制，找到第一档就停：

1. **源码里找逐会话/逐用户/逐对象的状态机**（搜 `is_*_enabled`、`*_service_config`、stage 与插件注册表、配置默认值）。AstrBot 有原生 `PATCH /api/v1/sessions/service` → `session_enabled`，状态落 `preferences` 表 `scope='umo'`：即生效、重启不丢、不必停机。
2. **改人格 prompt / 软约束**——⛔ 那是模型自觉，不是 enforcement。此前一次「静默」靠 prompt，grep 人格提示词找不到任何静默条款，完全不可靠。
3. **全局开关**——⛔ 过度杀伤。本例全局 `id_whitelist` 是 allow-list，用它实现单会话静默会把另一个真人用户一起静默。
4. **自写插件**——代价最高，要自己处理持久化与生效时机，且要装进应用的扩展点路径。

验证要点：用**应用自己的 enforcement 类**跑真实数据做 A/B，而不是「发消息看有没有回」。本例直接调 `SessionStatusCheckStage` + `ConversationManager(真实 DB)` + 最小 FakeEvent：目标对象 `is_session_enabled=False → pipeline_stopped=True`，两个对照组对象 `True → False`。

**Why:** 全局开关会误伤无关对象，prompt 软约束随时失效，自写插件维护成本高且扩展点路径一改就废——全是可避免的。原生最小作用域机制通常已经存在（只是没写进文档），代价只是一次源码阅读。

**How to apply:** 按 ①→④ 顺序找，停在第一档；每个「关掉」都要留回滚（备份原配置 + 定时恢复脚本 + 失败时保留排查入口）。连续踩墙 2 次以上就回到只读盘点，别继续盲试。

相关：[[survey-before-acting-on-own-project]]、[[verify-with-real-pipeline-and-readonly-probes]]、[[custom-llm-endpoint-capabilities-default-false]]。
