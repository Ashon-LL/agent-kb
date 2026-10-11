---
name: batch-account-onboarding-one-per-login
description: 批量纳号（OAuth device-flow/扫码/登录取 token 类）：多个待授权 state 并发时，同一浏览器登录态会把它们全部授权给同一个账号——必须一号一登（换号/无痕）并在捕获后按账号标识核对
type: workflow
source: APIShow 戌线纳号 2026-10-10（WorkBuddy 面板 OAuth 两 state 串号实测）
date: 2026-10-10
verified: 2026-10-10
topic: api-gateway
---

**经验**：给 N 个账号批量纳号时，**不要**一次性生成 N 条登录链接让用户「一口气全登完」——设备授权/OAuth 流程（device-flow、面板 start/poll 等）只认「浏览器当前登录的是谁」，**同一浏览器登录态会把多条待授权 state 全部授权成同一个账号**。正确姿势：**一号一登**（每号之间先退出登录或开无痕窗口），且**每条捕获后按返回体的账号标识（昵称/手机号/uid）逐一核对**，确认「这条 state 落的是预期那个号」再进行下一号。

**Why**：串号是**静默**的——poll 全部返回 `done:true`、账号也确实入池了，只是入池的是同一个号 N 次；不做核对就会以为「N 个号都纳好了」，直到用量或台账对不上才发现（报告里多出来的号全是同一人）。多 state 并发本身是允许的（服务端常是 map），风险不在并发，而在**人工那一步的同会话**。

**How to apply**：任何「程序生成链接 → 人工在浏览器完成 → 程序轮询捕获」的纳号/授权场景。核对优先用返回体的 nickname/uid；返回体无账号标识时，宁可按「一号一登 + 人工确认」串行做。相关 [[batch-account-onboarding-timeout-verify-before-retry]]。
