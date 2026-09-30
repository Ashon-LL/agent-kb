---
name: research-upstream-before-fixing
description: 上游异常先上网查现状再动手，免费源本质脆弱；以 DB/API 实测为准不信口头切换
type: workflow
source: apishow + mh-agent-open（2026-08-26 用户指令，zen/OpenRouter 两案验证）
date: 2026-09-14
---

**经验**：上游模型/免费渠道出异常（503/401/挂起）时，处置前先 WebSearch 该上游现状 + GitHub issues + 官方文档/目录，确认是"上游死了"还是"临时抖动"再决定摘除或保留。免费/逆向类上游本质脆弱：无 SLA、随时改名、下架、门禁化，查证能避免瞎修。

同族纪律：用户口头说"已切换/已改配置"但 DB/API 实测未变时，以实测为准——放开动作前先 `GET 状态端点` 确认真的状态。
