---
name: dont-open-frontline-for-edge-features
description: 改"本来没坏只是不通"的边缘功能前先问挡不挡主线——降级路径已存在且干净时是完成态不是待办
type: pitfall
topic: change-discipline
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：改一个"本来没坏、只是不通"的东西之前，先问：它挡住主线了吗？不挡就降级，别修。降级路径已经存在且干净时（写明原因、留占位、不伪造），那是完成态，不是待办。

**Why**：为截图能力开贯穿四层管线（Dockerfile→setup 脚本→守卫用例→白名单），40 分钟净零产出后全 revert。它从来没挡住主线——技能侧降级本来就很干净。修"不通"的默认代价参照物是主线，不是"我能不能修好"。

**How to apply**：给边缘功能动 Dockerfile/密钥库/全局白名单之前先自问这条管线有几层。一层（运行期幂等脚本）可以接受；四层不值。执行方抗命改判据时先复算——别把自己的推断当规格。

关联 [[guard-criteria-anchored-to-spelling-always-escape]]、[[prefer-narrow-native-switch-over-broad-global-or-plugin]]、[[minimal-change-and-no-scope-creep]]。
