---
name: cnb-token-usage-audit
description: CNB 组织 token 用量统计正解=逐构建 get-build-ai-audit 累加（charge 体系的 credit 是额度计费≠token 量，免费期 0 credit 但 token 照记）；charge_type_token 是平台 bug 勿纠缠；截止时刻记得时区；验收=逐位对齐+大运行逐条累加
type: tool
source: default 2026-10-05 apigogo 组织用量统计（27.57 亿 tokens）
date: 2026-10-05
verified: 2026-10-05
topic: cnb, methodology
---

**经验**:统计 CNB 组织「token 总用量」唯一可靠口径 = **构建级 AI 账本逐 pipeline 累加**：

1. `cnb repositories get-group-sub-repos --slug <org> --descendant all` 列全部仓库（secret 库平台本身不支持令牌访问，用量不可达，如实标注）。
2. `cnb build get-build-logs --repo <org/repo> --createTime YYYY-MM-DD --endTime YYYY-MM-DD --page-size 100` 圈窗口，**精确到时刻的 cutoff 必须客户端按 `createTime` 过滤**（这两个参数是日期粒度）。⚠️ **时区**：用户说"17:00"默认北京时间（UTC-8），NPC 侧显示也是 CST——按 UTC 截止会把 5 个运行（数百万 token）错收进来，判据=对比期初公开仓数字是否与历史口径逐位一致。
3. 对每个 build 的每个 pipeline 调 `cnb build get-build-ai-audit --repo <r> --sn <sn> --pipelineId <pid> -v`，取 `data.content.total.total_tokens`。**404 "Ai audit information not found" = 该 pipeline 无 AI 用量**，是绝大多数 push 构建的正常态，不是错误。6 线程并发 1767 个 pipeline 约 3 分钟。
4. **验收两步**：① 与另一独立来源（如历史 NPC 跑出的公开仓数字）**逐位一致**；② 对 top 大运行用 `cnb build get-build-ai-request` 翻页逐条累加（每页 100 条，`data.content` 是列表），token 数与请求数都应等于账本汇总。

⛔ **三个坑（都实测过）**：
- **`charge` 体系的 credit ≠ token 量**。credit_in_milli 是额度计费；免费期里单次运行的 `milli_credit=0` 但 `total_tokens` 照记（本例 credit 2,259.84 vs token 27.57 亿，差 6 个数量级）。别拿 `cnb charge get-volume/get-repos-volume --type charge_type_credit` 当 token 用量上报——用户会当场纠正。
- **`charge_type_token` 是平台 bug**：CLI `--help` 与 swagger.json enum 都列了它，服务端一律 `400 errcode:3 The parameter type is invalid`。别在这里反复试参数，直接走 ai-audit。
- **Python 调 cnb 必须 `cnb.cmd`**（裸名 FileNotFoundError），见 [[cnb-cli-needs-cmd-suffix-when-spawned-from-python]]；CLI 的 `-v` 输出是干净 JSON，比默认 YAML-ish 好解析。

**口径边界**：`get-build-logs` **不要按事件过滤**——AI IDE（云原生开发/工作区）里的 CodeBuddy 会话在平台上就是以 **`event: vscode`** 的构建入账的，ai-audit 同样覆盖它（2026-10-05 实测：apigogo 全量 27.57 亿中 6.55 亿来自 vscode 会话，17 个有账本 / 21 个 404）。vscode 构建 404 = 该会话未产生 AI 请求（开了没用），不是漏记。真正够不到的只有：secret 库（平台本身不支持令牌访问）。构建初始化即失败的 `-error` 占位管道无账本，若失败前已调模型则这部分丢失——报告里作为已知缺口写明。

**Why**：口径错一次就是 6 个数量级的错误数；charge_type_token 的假入口会烧掉大量无效尝试；截止时刻差 8 小时会错收/漏收整天运行；⚠️ 只按 npc 事件过滤会漏掉整个 AI IDE 通道（占总量近 1/4）。

**How to apply**：任何"统计 CNB AI token 消耗"的需求都走上面的四步；组织全量含私有库需要 Owner 账号令牌（NPC 令牌读不了私有仓，可见性是硬边界）。结果示例口径：`{仓库, tokens, 请求数, 运行数}` + 按月 + 按模型（deepseek-v4.1-flash/space-bunny 等）拆分，输入/输出/思维链/缓存读分列。
