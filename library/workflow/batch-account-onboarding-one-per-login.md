---
name: batch-account-onboarding-one-per-login
description: 批量纳号/多账号同时登录（OAuth device-flow/扫码/登录取 token 类）：同一浏览器 profile 下的多窗口/多标签页共享登录态会把多条 state 授权给同一账号——必须一号一登，且每个账号用独立浏览器环境（独立 profile/独立 user-data-dir/无痕），ego 中创建 TaskSpace 时指定不同 profileId；捕获后按账号标识核对
type: workflow
source: APIShow 戌线纳号 2026-10-10（WorkBuddy 面板 OAuth 两 state 串号实测）；APIShow CodeArts 多账号重登 2026-11-05（两个 ego TaskSpace 未指定 profileId → 两次回调都落在同一账号 5837）
date: 2026-10-10
verified: 2026-11-05
topic: api-gateway, browser
---

<!-- hook-reviewed 2026-11-16：已核对 INDEX 钩子覆盖本条 2026-11-05 新增的浏览器环境隔离内容 -->

**经验**：给 N 个账号批量纳号时，**不要**一次性生成 N 条登录链接让用户「一口气全登完」——设备授权/OAuth 流程（device-flow、面板 start/poll 等）只认「浏览器当前登录的是谁」，**同一浏览器登录态会把多条待授权 state 全部授权成同一个账号**。正确姿势：**一号一登**（每号之间先退出登录或换独立浏览器环境），且**每条捕获后按返回体的账号标识（昵称/手机号/uid）逐一核对**，确认「这条 state 落的是预期那个号」再进行下一号。

**Why**：串号是**静默**的——poll 全部返回 `done:true`、账号也确实入池了，只是入池的是同一个号 N 次；不做核对就会以为「N 个号都纳好了」，直到用量或台账对不上才发现（报告里多出来的号全是同一人）。多 state 并发本身是允许的（服务端常是 map），风险不在并发，而在**人工那一步的同会话**。

**浏览器环境隔离（2026-11-05 补充）**：多账号同时登录，每个号必须在一个**独立的浏览器环境**里——同一 profile（user-data-dir）下的多窗口/多标签页共享 cookie/localStorage，第二个窗口会直接复用第一个窗口的登录态，表现为「两个号都登录成功了，但服务端只收到同一个账号」。

- **ego**：`await profiles()` 列出可用 profile；创建空间时 `await taskSpace(name, { profileId: "Profile 1" })`，**每个账号用一个不同 profileId**。只开两个 TaskSpace、不传 profileId ≠ 隔离（它们共享默认 profile，2026-11-05 实测两次回调都落在同一账号 5837）。
- **Edge/Chrome**：每个账号用独立的浏览器配置文件（Edge 配置文件 / Chrome Profile），或独立 `--user-data-dir=<dir>` 启动；无痕/InPrivate 只隔离主 profile，多个无痕窗口之间可能共享同一无痕会话，不能替代独立 profile。
- **验证**：登录完成后核对服务端收到的账号 UID/手机号（或回调日志里的 user_id），两个账号的标识不同才算隔离成功；发现相同立即停止，换独立环境重来。

**How to apply**：任何「程序生成链接 → 人工在浏览器完成 → 程序轮询捕获」的纳号/授权场景，以及任何需要同时登录多个账号的运维操作。核对优先用返回体的 nickname/uid；返回体无账号标识时，宁可按「一号一登 + 人工确认」串行做。相关 [[batch-account-onboarding-timeout-verify-before-retry]]、[[rotating-refresh-token-needs-single-writer]]。
