---
name: github-pr-form-is-a-details-disclosure
description: GitHub compare 页的「Create pull request」是 details 折叠开关不是导航，PR 表单是同级的 Details-content--hidden；填 pull_request[title]/[body] 走原生 value setter + requestSubmit，别等 URL 跳转
type: pitfall
source: ps-heredoc-todie（mokuyoaxis/PowerShell-Reliability-Framework PR #1，2026-09-21 实测）
date: 2026-09-21
verified: 2026-09-21
---

**经验**：GitHub compare 页那个大号 `btn-primary` 的「Create pull request」按钮**不是导航**。它的属性是 `type=button` + `class="js-details-target"` + `aria-expanded=false`——是一个 `<details>` 折叠开关。所以任何「点它然后等 URL 变化 / 等 `/pulls/N`」的自动化**永远等不到**，表象像网络挂了或按钮无响应，实际是语义读错了。

- 真正要提交的表单是 `form#new_pull_request`，它是那个按钮所在 `<div>` 的**同级兄弟**，class 里带 `Details-content--hidden`（被折叠隐藏）。所以别在按钮祖先链里找 `<details>`——按钮根本不在表单里，`toggle.closest("form")` 是 null。
- 真正的提交控件在表单内部：`button[type="submit"].hx_create-pr-button`（与 `js-sync-select-menu-button` 是同一个按钮）。**`type=submit` 才是判据**；按 `btn-primary` 或按文本「Create pull request」会命中两个同名按钮（还有一个零尺寸隐藏副本）。
- 填字段的可靠姿势：直接选 `input[name="pull_request[title]"]` 和**隐藏**的 `textarea[name="pull_request[body]"]`（新编辑器的可见区是 CodeMirror/富文本，隐藏 textarea 才是提交载荷），用原生 setter 写值再派发冒泡 `input` 事件：
  ```js
  const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
  set.call(ta, text); ta.dispatchEvent(new Event("input", { bubbles: true }));
  ```
  然后 `form.requestSubmit(submitBtn)` 提交。`requestSubmit` 不要求表单可见，所以**连展开 details 都可以跳过**（把 `Details-content--hidden` 换成 `Details-content--shown` 更稳，但非必需）。
- ⛔ **别用坐标点击**：页面会重排，两次读取之间按钮位置会变，坐标点下去常落在 `<li>` 上。整个「填标题 + 填正文 + 提交」用一个 `page.evaluate` 一次做完最稳；正文从磁盘 `fs.readFileSync` 读进来直接当参数传，别手工转录。
- ⚠️ **pin 和 POST 必须挨在一起**（[[github-china-network-workarounds]]）：实测一次 POST 打到刚好翻死的 pinned IP，返回 `chrome-error://chromewebdata/`、页面 body 长度 0，**服务端没建 PR**（`GET /pulls` 仍是 0）。所以失败后先用 API 确认「到底建没建」，再重探 IP（真 TLS 握手、SNI=github.com）、重 pin、重提交。
- ⚠️ `gh api` 返回 `404 Not Found` 也可能是你**把 owner 拼错了**，不一定是网络或权限——先核对 URL 里的 owner 段。
- **fork PR 的 CI 不会自动跑**：upstream Actions 会记录 run（每个 commit 一条）但 `conclusion: "action_required"`，等 maintainer 批准才执行——不是失败，别当红灯报。

**How to apply**：GitHub 上任何「点主按钮 → 等跳转」的 UI 自动化，先读按钮的 `type` 和 class；`type=button` + `js-details-target` = 折叠开关，改走 `form.requestSubmit()`。提交类 POST 前后各查一次服务端状态。相关：[[github-china-network-workarounds]]、[[windows-scripting-terminal-gotchas]]。
