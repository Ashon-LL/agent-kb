---
name: cnb-npc-dispatch-channel-config-and-time-caps
description: CNB NPC 派单：@地址必须带完整仓库路径、CLI 评论可触发、配置源在 NPC 仓 .cnb.yml、timeout 不等于会话上限
type: pitfall
source: mh-agent-open
date: 2026-10-21
verified: 2026-10-21
topic: cnb
---

# CNB NPC 派单：通道、配置源与时长上限（2026-10-21 实测）

**1. @ 地址必须带完整仓库路径**
`@<NPC 所属仓>(<角色名>)`，例：`@apigogo/x(中书令)`。
裸 `@中书令` **不产生事件**：2026-10-21 实测——bx 镜像仓发裸 `@中书令` 评论（201 成功），
60~70 秒后 build 列表零新增；同日在 `apigogo/mh-agent-open` 发 `@apigogo/x(中书令)` + `--work-mode`，
**2 秒**建出 `issue.comment@npc` 流水线（sn `cnb-ehi-1k5e2vrpf`）。

**2. CLI 评论可以触发，不需要网页首棒**
`cnb issues post-issue-comment --repo X --number N --body-file f.md --work-mode` → 201 → 建流水线。
此前"CLI 拉不起"的结论来自 NPC **在自己仓用 NPC 身份自评**的场景，不能外推为"CLI 不可用"。
（网页评论也有效，勾「替我上班」等价。）

**3. CLI 不能触发评论事件**
`cnb build start-build --event` 的帮助原文：事件名**须为 `api_trigger` 或以它开头**。
⇒ 想走 `issue.comment@npc` 只能发评论；想用 `start-build` 就只能走 `api_trigger*` 事件段。

**4. 配置源按事件分割**
- `issue.comment@npc` / `pull_request.comment@npc`：事件段由 **NPC 所属仓**的 `.cnb.yml` 定义
  （本仓 = `apigogo/x` 的 `.npc` 锚点）⇒ 改**机型 cpus / maxTurns / timeout** 要改 fork，改目标仓无效。
- `api_trigger_npc`：由**目标仓自身** `.cnb.yml` 定义（mh 仓：`cpus: 4` / `timeout: 4h` / `maxTurns: 1000`）。
- 目标仓缺该事件定义时，平台按【系统默认】+【NPC 仓】合并，NPC 仓已定义者覆盖默认。

**5. 4 核实测（2026-10-21）**
评论路径 `.npc` 原引用 `.runner`（cpus 2）→ 新增 `.runner-dispatch`（cpus 4）并让 `.npc` 引用它；
新流水线 labels 实测 `cpus: 4 / memory: 8`。**只动 `.npc` 锚点**，心跳/巡检仍走 `.runner`（2 核），互不覆盖。
回退 = `.npc` 的 runner 改回 `*runner`（一行）。

**6. `timeout` ≠ 会话总时长（最容易错的一条）**
官方 `npc:go` 语义：`timeout` 管**单次工具执行 / 无输出窗口**（未声明=10 分钟 / 2 小时），
**不是**会话或流水线总时长。mh 仓 2026-09-18 两例实证在 **2h01m 被 SIGKILL**，
且**声明 `timeout: 6h` 照样在 2h 被杀**（`cnb-eke` 实跑 121.12 min → error）。
⇒ 「改 timeout 就能跑更久」是错的。

**7. ⛔ 取证陷阱：配置文件注释会被日志回显**
`strings runner.bin | grep -o 'CNB_PIPELINE_MAX_RUN_TIME=[0-9]*'` 会命中**我们 .cnb.yml 注释里写的示例值**，
不是真实 env。真实 env 在日志里是 `CNB_PIPELINE_MAX_RUN_TIME=<masked>`。
⇒ 判平台注入值必须看**独立证据**（被杀时刻与阈值吻合 / 多构建对照），不能只 grep 字面量。

**8. 评论路径是否同受 2h 上限：未验证（据实标注）**
变量在评论路径日志里也在（值掩码）；历史上评论构建最长 18m39s（`cnb-esv-1k592klfg`），
**没有 >2h 的评论样本**。⇒ 只能说"很可能同样"，不能说"已验证"。

**9. 长任务的正确姿势 = 增量推送，不是换通道**
不管是 api_trigger 还是评论，撞上限时**已推的留下、未推的全丢**。
所以任务书必须写明：禁裸 `wait`、单条命令分段、每完成一项立即 commit+push。

**用户口径（2026-10-21）**：`6h` 是配置量级参考，**不是任务截止线**
（原话「我没有说 <6h，没有说整个必须在 6h 内完成」）。

关联 [[dispatch-requires-three-way-equality-and-artifact-hygiene]]、
[[check-inflight-work-before-dispatch]]、[[no-assertion-without-measurement]]。
