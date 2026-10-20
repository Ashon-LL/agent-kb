---
name: browser-extension-migration-mechanism-first
description: 跨浏览器迁移扩展前必须先确认目标浏览器的安装机制（ego-lite 实测只认自家安装、会删外部塞入的扩展文件与注册项）；同一扩展在 Chrome 商店与 Edge 商店是两个不同 ID，按 ID 做差集必误判；UI 快照/页面计数不能当证据，落盘的 Extensions 目录 + Secure Preferences 才是
type: tool
source: 2026-10-20 本机 ego-lite 扩展迁移四连败复盘（用户全程手动安装成功）
date: 2026-10-20
verified: 2026-10-20
topic: browser
---

**经验**：
1. **先问"目标浏览器怎么装扩展"，再动手迁**。ego-lite（Citro Labs，`C:\Program Files\Citro Labs\ego lite`，profile 在 `%LOCALAPPDATA%\Citro Labs\ego lite\User Data\`，默认 profile 名是 `Profile 1` 不是 `Default`）实测：**只认自己安装流程产生的扩展**。往 `Extensions/` 拷文件 + 手写 `Secure Preferences` 注册项，下次启动会被它删掉（连官方 `ego-browser import --browser edge` 导入的扩展也一起清）。`--load-extension="<dir>"` 启动参数能加载个别扩展但不持久、且多数被安全策略拦。⇒ 迁移前先确认机制，5 分钟就能给出"ego 不支持从 Edge 直接迁扩展，需在它的商店重装"这个诚实答案，而不是连试四条路。
2. **同一扩展在 Chrome 商店和 Edge 商店是两个不同 ID**。例：AIX 智能下载器 Edge 版 `pljfekbkmmbkdfhddpebdlmfngigcohc`、Chrome 版 `ibdfeimkglcmdejppabkaidpippniiob`；WorkBuddy Edge 版 `ndbfelmlimfjklodckmbalfioaehegpc`、Chrome 版 `ajnnogdfpilbhkeggdjlcokgglijmdde`。**按 ID 集合做差集判断"缺哪些扩展"必误判**，必须按名字（manifest.name）比对。
3. **UI 快照/页面计数不能当证据**。`chrome://extensions/` 的 accessibility 快照是异步渲染的：4 秒快照只有 1041 字符、只列出 2 个，而落盘事实是 10 个已装（3 启用 7 禁用）。判定装没装、启没用，看 `Extensions/<id>/<ver>_0/` 目录是否存在 + `Secure Preferences` 的 `extensions.settings.<id>.path/disable_reasons/from_webstore`，别看页面。
4. **`disable_reasons=[1]` = 用户手动禁用**，不是迁移失败。看到它先问用户，别当成 bug 去"修"。
5. **连续失败两次就该停下问，而不是换第三条路**。本例四条路（手拷文件/官方 import/load-extension/商店安装）全部零效果，却每条都汇报了"有进展"——把试错当成了交付。

**Why**：把"试过"当成"推进"，会把用户的事做成自己的实验场，还覆盖用户数据（本例中手动改过 ego 的 Secure Preferences 与 Local State 默认 profile）。判定类问题（装没装/缺哪些）拿不到可靠证据时，正确答案是"我不知道，需要 X"而不是再猜一次。

**How to apply**：任何"把 A 浏览器的 X 迁到 B 浏览器"的任务：① 先确认 B 的安装机制与数据真源（落盘文件，不是 UI）；② 按名字而不是 ID 比对；③ 用落盘状态给结论；④ 两次失败就停下来把机制讲给用户、让用户决定装还是弃。相关：[[tencent-browser-skill-setup]]、[[browser-extension-forensics-profile-leveldb]]。
