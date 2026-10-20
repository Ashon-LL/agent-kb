---
name: empty-config-is-not-missing-feature
description: 判断「某能力是否启用」必须读实现+实测产出，不能凭 env/配置为空下结论（空值可能正是正解）；配置缺失与「功能不存在」是两件事；同一项目的多条「设备标识」路径要分开读，且先与上游源码对文件
type: pitfall
source: APIShow / trae 设备隔离误判（2026-10-06 读实现+容器内实测证伪）
date: 2026-10-06
verified: 2026-10-17
topic: methodology
---

**经验**：看到配置项为空就断言「这个能力没做/没启用」是高频误判。**空值可能是正解。**

**实证（trae 设备隔离）**：
- 我见 `TRAE_CHECKIN_DEVICE_IDS_JSON=` 为空 → 断言「两账号共用同一设备标识、隔离只是名义的」。
- 读实现发现真相：`checkin_device_id_for()` = `sha256(账号identity) % 10^16` **按账号派生** 16 位设备 id ⇒ 一账号一设备，天然隔离。容器内实测两号 device_id 确实不同。
- 更关键：**显式填上那个 env 反而是功能降级**——源码里 `rotate_checkin_device_id()` 一旦检测到已配置 id 就 `return ""`，直接**关掉撞 9074 时的换设备脱困能力**。空配置才是项目设计的正解。

**判别顺序**：
1. 先 grep 实现，看这个能力是「读配置」还是「按上下文派生」。
2. 再实测产出（如在运行容器里算一遍两账号的派生值并比对），而不是读配置文本。
3. 最后才决定要不要动配置。

**配套：撞风控先分「设备维度 vs 时段维度」**。同一账号连续换 device id 重试仍失败、退避后成功 ⇒ 指向**时段性全网限流**（例：签到整点 everyone 同时打），改配置方向应是**错峰**而非换设备。

**补充（2026-10-17 读上游源码）：同一个项目里，「设备标识」可能有多条互不相干的路径，别用一条去解释另一条。**

以 trae 为例，两条路径机制完全不同：
- **签到路径**：`checkin_device_id_for()` = 按账号 sha256 派生**稳定的** 16 位 id（即上文那条）；撞 9074 才 `rotate_checkin_device_id()` 换代，且显式配 id 反而关掉换设备脱困。
- **聊天路径**：`trae_client.py::get_current_device()` —— `machine_id`(32hex) / `device_id`(19 位) / `brand` 每次**随机生成**、**每 3–5 个请求整体换一套**，而且是**进程级共享**（不按账号区分）。
- ⛔ 这段轮换**是上游项目自带**（APIShow 部署= `autumnsentiment/Trae2api-cn`，容器内 `src/trae_client.py` 与上游 `main` 分支**逐行零差异**，`max_uses=3+rand(0,2)`），**不是我方补丁**。看到「随机 / 轮换 / 不按账号」先别断言「隔离没做」——**去上游仓库把同名文件对一遍**（`gh api repos/<owner>/<repo>/contents/<path>` 取原文，再 `diff` 容器内文件），能一眼分出"上游如此"和"我们改了"。

**判据**：两条路径受**不同**的配置/环境变量控制（`TRAE_CHECKIN_DEVICE_ID(S)` 只作用于签到），拿 A 的开关解释 B 的行为必然错。

**相关**：[[daily-reward-need-scheduler-to-endpoint-chain]]（同样「先读实现再下结论」）、
[[quantity-and-config-claim-three-errors]]（「把程序默认值当谁设的」的镜像：**把空配置当未实现**）

关联 [[disguised-client-gate-needs-placeholder-tools-merged-not-replaced]]、[[custom-llm-endpoint-capabilities-default-false]]。
