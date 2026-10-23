---
name: external-tool-integration-criteria-and-gotchas
description: 接外部工具集（MCP 等）的判据是「模型自己做不到」，工具数是反向指标；附「握手超时先怀疑客户端」与「URL 名字可能是另一套 slug」两坑
type: tool
source: mh-agent-open
date: 2026-10-20
verified: 2026-10-20
topic: mcp
---

# 接外部工具集：判据是「模型自己做不到」，不是「工具数量」

**背景**（2026-10-20，接入书生·端砚 SCP「科学工具广场」）：
平台有 47 个 server、**3653 个工具**。第一直觉是"工具最多的 server 最值钱"，
实测**恰好相反**：工具数 1894 的 ToolUniverse、以及 41/99/81 的「计算工具集」，
抽样工具名是 `convert_length_mm_to_m` / `round_to_decimal_places` / `calculate_area`
——**把一行 Python 拆成几十上百个微函数**。接进来只增加「选错工具 + 多一轮往返」。
最终只接 3 个**真数据源**（学术检索 / 跨学科知识图谱 / 论文 KG），计算工具集一个都没接。

**判据（可直接复用）**：
1. 问「**这件事模型自己写三行代码能不能做**」——能，就不接；
2. 只找「**模型不拥有的东西**」：数据库、全文语料、专有索引、真实实验/仪器接口；
3. 抽样读 10 个工具名再决定：名字里全是 `convert_*` / `calculate_*` / `round_*`
   ⇒ 微函数工厂，一条都不接；
4. 工具数写进汇报时**必须同时写抽样工具名**，否则等于拿数量冒充能力。

**两个实测坑（会把"能不能挂"的结论带偏）**：

- **握手超时先怀疑客户端，不是网络**：目标网关 curl `initialize` **0.47 秒**成功，
  而某 CLI 自带的 MCP 客户端 `--connect-timeout 60` 仍 `did not complete initialize`
   ⇒ 是**客户端实现不兼容**。做法：curl 打一次 + 官方 SDK 打一次，两条都通即可判定
   问题在被测客户端；⛔ 不要因「一方连不上」就写"服务不可用"。
- **URL 里的名字可能是另一套**：显示名（中文）在 URL 里被拒（`Invalid server_name`），
  正解是 **ASCII slug**（`26 → Data_processing_and_statistical_analysis`）。
  唯一可靠来源 = **平台详情页自己生成的配置片段**；
  ⛔ 不要拿列表接口的显示名去拼 URL。

**落地纪律**：
- 外部依赖不进关键路径：缺凭据 / 缺 SDK / 连不上 / 远端报错 ⇒ 一律返回结构化失败，**不抛**；
  唯一例外是 `CancelledError` 必须原样透传（它继承 `BaseException`，吞掉会让调用方永久挂起）。
- 凭据只进运行时 DB / 子进程 env；返回值与日志都不得回显；
  换凭证时**不要只看表格里的掩码**——复制控件常是掩码旁那个没有 aria-label 的图标，
  或只在创建成功那一刻出现一次。
- SDK 依赖走**惰性导入**：缺装时降级成 `sdk_unavailable`，⛔ 不让整个服务起不来。

**关联**：[[fail-open-except-swallows-caller-type-errors]]、
[[local-sync-must-reach-user-visible-layer]]。
