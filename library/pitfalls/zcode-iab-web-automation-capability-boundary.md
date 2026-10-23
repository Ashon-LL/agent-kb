---
name: zcode-iab-web-automation-capability-boundary
description: ZCode 内嵌浏览器（IAB）web 自动化的能力边界：能做 DOM 读写/受控表单/需"用户激活"的交互用 cua 真实点击（坐标=截图栅格）/同源 iframe；⛔ 不能做文件选择器与 window.open 弹窗（真实点击也不够）
type: pitfall
source: Elsevier 新版投稿服务（submit.elsevier.com/NEUCOM）实弹投稿，2026-10-14
date: 2026-10-14
verified: 2026-10-14
topic: browser, zcode
---

**经验**：在 ZCode 侧栏内嵌浏览器（IAB）里做 web 自动化，先分清三类边界，否则会在"点了没反应"上反复空转。

**能做（稳的姿势）**：
- 读页面：`domSnapshot()`（AI/ARIA 树，能穿透同源 iframe）；复杂 SPA 读不出时用 `evaluate` 读 `innerText`/字段值。
- 受控表单（React 等）：`el.click()`，或**原生 setter + `input`+`change` 事件**（直接赋 value 会被框架清空）。
- **需要"用户激活"的交互**（combobox 展开、下拉列表）：**cua 真实点击**——坐标 = **当前截图栅格的像素**；先 `scrollIntoView` 再取 `getBoundingClientRect` 中心。
- 同源 iframe：`frameLocator("#id")` + 来自 DOM 事实的选择器。

**⛔ 不能做（平台级，别硬试）**：
1. **文件选择器**：`<input type=file>` 既不能编程赋值（DataTransfer 注入的 File 会被 SPA 忽略），也没有 `setInputFiles` 能力 ⇒ **上传必须由人在真实浏览器完成**。
2. **弹窗（`window.open`）**：被宿主拦截；**cua 真实点击也不够**；拦截 `window.open` 只能拿到参数（常见 `("", "apc", "width=...")` 空 URL + 窗口名）⇒ 开不了。⚠️ 若参数里**有完整 URL** 才可自己 `goto`。

**判据与绕法**：
- "点了没反应"先 `evaluate` 读元素的 `aria-expanded`/`value`/`checked` **验证是否真生效**（别拿"命令返回成功"当结论）。
- 页面小字提示常是钥匙（本次："check your browser settings to **allow pop-up windows**" = 明示弹窗被拦）。
- 弹窗/文件选择器类 ⇒ 请用户在自己的浏览器完成那一步；或同源 `fetch(script.src)` 搜 JS 里的目标 URL。

**实例**：Elsevier 新版投稿服务（`submit.elsevier.com/<JOURNAL>`，8 步：类型→上传→元数据→作者→funder→OA→附加信息→Review）——**上传 + OA 两步必须真浏览器**，其余（选类型/元数据/作者/机构自动补全/CRediT/附加信息/声明）IAB 可全自动。

关联 [[browser-extension-migration-mechanism-first]]、[[browser-extension-forensics-profile-leveldb]]、[[ego-browser-form-automation-dialogs-and-cache]]。
