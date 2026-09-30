---
name: cli-over-browser-automation
description: 平台任务优先用 CLI/OpenAPI 而非浏览器自动化，先读平台文档；浏览器只留给无 API 的扫码/token 环节
type: workflow
source: ailika（2026-09-13 用户指示）
date: 2026-09-14
verified: 2026-09-13
---

**经验**：要操作某平台前先确认它有无 CLI 或 OpenAPI（如 `gh` 对 GitHub、`cnb` 对 CNB），读一遍平台文档（很多文档站提供 llms.txt 可批量抓）后用命令读写。浏览器自动化只留给确实没有 API 的环节：扫码登录、一次性建 token、仅 UI 的核验。

**Why**：命令更快、可脚本化、比点 UI 可靠；用户把命令行控制视为"和 git push 一样自然"的默认预期，还要求"先好好学平台"而不是点界面瞎试。
