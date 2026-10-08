---
name: ablation-must-self-verify-change-applied
description: 消融/性能实验必须自证"这次真的改到了吗"——判据是计算后取值不是调用动作
type: pitfall
topic: methodology
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：消融类实验必须自带"我这次真的改到了吗"的自检，且判据是计算后的取值（如 `getComputedStyle` 结果），不是"我调用过设置函数"（动作）。没有这道闸，实验失效与实验成功在输出上长得一样。

**Why**：连续测错三次都静默产出看起来合理的假数字——串行档位混入时间漂移、新开页面混入冷启动方差、参数没传对（Playwright evaluate 只接受一个 arg，传列表让 JS 收到整个数组，消融从未生效）。最毒的是自检打印的是同一行却没看出异常。

**How to apply**：单页面轮转（不新开页/reload）+ 每轮颠倒顺序 + 参数用单对象 `evaluate(js, {mode, pick})` + 状态硬闸（off 档 getComputedStyle 必须含 `none`、on 档必须含 `url(`，不满足直接 fail 退出）。
