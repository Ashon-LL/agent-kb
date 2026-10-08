---
name: empty-config-is-not-missing-feature
description: 判断「某能力是否启用」必须读实现+实测产出，不能凭 env/配置为空下结论（空值可能正是正解）；配置缺失与「功能不存在」是两件事
type: pitfall
source: APIShow / trae 设备隔离误判（2026-10-06 读实现+容器内实测证伪）
date: 2026-10-06
verified: 2026-10-06
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

**相关**：[[daily-reward-need-scheduler-to-endpoint-chain]]（同样「先读实现再下结论」）、
[[quantity-and-config-claim-three-errors]]（「把程序默认值当谁设的」的镜像：**把空配置当未实现**）
