---
name: cnb-issue-attachment-download
description: CNB issue 附件下载坑：Web 路由 vs API 凭证错配（Bearer→400）、curl 200 可能是假 SPA、评论链接被 undefined/ 污染、API 取回一律 404
type: tool
source: mh-agent-open 第八单（2026-09-17）实测；附件随构建停止回收取不回
date: 2026-09-17
verified: 2026-09-17
topic: cnb, browser
---

**经验**（NPC 上传 `cnb issues upload-file --file <path>`，需 `CNB_ISSUE_IID=<n>` 否则报缺 issue number；返回 `asset_link` 是**根相对** `/-/files/issues/<内部ID>/<slug>/<uuid>/<名>`，无仓库前缀）：

- **Web 路由 ≠ API 凭证通道**：`asset_link` 给浏览器用、靠**登录 Cookie**；CLI 的 `~/.cnb/token`（Bearer）是 **OpenAPI 凭证**，同 host 不同路由前缀。拿 Bearer 打 `/-/files/...` → **400 `{"errcode":3,"errmsg":"Invalid argument"}`**（请求形态不被这条路由接受，不是没登录——403 才是权限）。
- **⚠ curl `-sL` 的 200 会骗人**：`https://cnb.cool/-/files/issues/...`（无仓库段）返 200，但 body 是一页 "Page not found · CNB" 的 SPA HTML（~123KB），**不是文件**。判存亡必须看 body，不能信状态码。
- **API 下载两条都 404**：`cnb issues get-files --file-path <...>` 与 `get-issue-files --repo <r> --file-path <...>`（scope `repo-issue:r`）。穷举 7 种路径写法（含/不含仓库段、含/不含 `undefined/`、各级截断）→ **全 404 `errcode:5 Resource not found`**。
- **⚠ 评论里存的附件链接被污染**：API 返回的 `asset_link` 干净，但 issue 评论 markdown href 实测多了字面量 `undefined/` + 仓库段（`undefined/apigogo/mh-agent-open/-/files/...`）——点开即坏，别信它。
- **结论**：附件绑定那次构建上下文，手动停止构建 + 容器回收后对象大概率已清，按现有链接取不回。**可靠取回方式 = 让 NPC 直接 push 代码**（如 `auto/openclaw-sse-usage-compat`），不靠 issue 附件绕路。

**How to apply**：要 NPC 的中间产物，优先在派单任务书里要求「直接推分支/建 PR」；附件只作兜底，且下载前先 `head -c 200` 验 body 是不是 HTML。

关联 [[verification-script-ua-can-fake-a-config-failure]]。
