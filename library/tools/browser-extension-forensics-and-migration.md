---
name: browser-extension-forensics-and-migration
description: Edge/Chrome 扩展的 Secure Preferences/LevelDB 取证与跨浏览器迁移机制；含 location=4、扩展 ID 差异、安装器删除外部扩展
type: tool
source: 合并自 browser-extension-forensics-profile-leveldb, browser-extension-migration-mechanism-first；2026-10-08 default 会话排查 Edge 篡改猴(Tampermonkey 5.5.0 / iikmkjmpaadaobahmlepeloendndfphd) 脚本失效 + 卸载 Browser Relay; 2026-10-20 本机 ego-lite 扩展迁移四连败复盘（用户全程手动安装成功）
date: 2026-10-08
verified: 2026-10-20
topic: browser, reverse-engineering
---
**经验**：Edge/Chrome 扩展的 Secure Preferences/LevelDB 取证与跨浏览器迁移机制；含 location=4、扩展 ID 差异、安装器删除外部扩展

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## browser-extension-forensics-profile-leveldb

**判"扩展为什么不工作"的取证顺序**（全只读，不改浏览器配置）：

1. **读 `Edge\User Data\<Profile>\Secure Preferences` 与 `Preferences` 的 `extensions.settings[<id>]`**：`location`（1=正常安装 / **4=解包加载** / 10=内置组件）、`disable_reasons`（**0/空=启用，1=kReload 待重启浏览器才生效**）、`granted_permissions.api` 与 `active_permissions.api`（**两者都含 `userScripts` 才说明"允许用户脚本"已开**）、`withholding_permissions`（非空=站点权限被扣）、`user_scripts_worlds`（脚本 world 的 CSP）。
2. **名字解析**：manifest 常是 `__MSG_appName__`，须读 `_locales\zh_CN\messages.json`（或 en）替换。⚠️ 路径别把扩展 ID 拼两遍——`...\Extensions\<id>\<ver>\manifest.json`，拼错会导致"全部扩展名未知"的假象。
3. **策略别误判**：`ExtensionManifestV2Availability=2` 只封 **Manifest V2**，MV3 扩展不受影响；`BackgroundModeEnabled=0` 同理无关。Enhanced Security 看 Preferences 里 `is_under_advanced_protection:false`。
4. **看脚本本体与依赖**：`Local Extension Settings\<id>\000003.log` 是 LevelDB，**浏览器运行时被锁**——用 `File.Open(path, Open, Read, ReadWrite)` 共享读，`File.ReadAllBytes` 会抛"being used by another process"。里面能读到 `@name/@match/@require/@grant`、**已缓存的 @require 资源（base64）**、脚本的 `enabled:true` 开关、以及 GM 存储里的自定义配置。

**油猴类脚本的隐藏依赖**：有些脚本（如 PanLinker/网盘直链下载助手）核心功能走**本机 JSON-RPC 服务**——存储里可见 `setting_rpc_domain=http://localhost`、`setting_rpc_port=16800`、`setting_rpc_path=/jsonrpc`。扩展与权限全都正常、CDN 也 200，但**该端口无监听 ⇒ 功能必然不可用**（缺的是辅助服务，不是脚本）。判完扩展层正常就要往"脚本依赖的本机服务/过期 token"转，勿反复怀疑权限。

**Why**：2026-10-08 实测——篡改猴扩展层完全健康（MV3、userScripts 已授予且生效、`<all_urls>` 无扣减、脚本 enabled、依赖已缓存、CDN 可达），真因是脚本依赖的 localhost:16800 服务不存在；不查脚本配置就会在"权限/网络"上白转。

**How to apply**：
- 顺带安全提示：这类存储里常躺明文账号 token（本次见到某网盘 access_token 明文）——**诊断输出里不要复述该值**，并提醒用户刷新/吊销。
- **卸载解包扩展**：源目录删掉即失效，但 Secure Preferences 里的注册项 HMAC 受保护、不能手改（改了会被 Edge 重置），须用户在 `edge://extensions` 点"删除"；彻底一点可加策略 `ExtensionSettings` 阻断。

关联 [[web-automation-call-page-functions-not-dom-clicks]]、[[browser-only-success-check-credential-first]]。 [[browser-extension-forensics-and-migration]]、[[zcode-iab-web-automation-capability-boundary]]。

## browser-extension-migration-mechanism-first

**经验**：
1. **先问"目标浏览器怎么装扩展"，再动手迁**。ego-lite（Citro Labs，`C:\Program Files\Citro Labs\ego lite`，profile 在 `%LOCALAPPDATA%\Citro Labs\ego lite\User Data\`，默认 profile 名是 `Profile 1` 不是 `Default`）实测：**只认自己安装流程产生的扩展**。往 `Extensions/` 拷文件 + 手写 `Secure Preferences` 注册项，下次启动会被它删掉（连官方 `ego-browser import --browser edge` 导入的扩展也一起清）。`--load-extension="<dir>"` 启动参数能加载个别扩展但不持久、且多数被安全策略拦。⇒ 迁移前先确认机制，5 分钟就能给出"ego 不支持从 Edge 直接迁扩展，需在它的商店重装"这个诚实答案，而不是连试四条路。
2. **同一扩展在 Chrome 商店和 Edge 商店是两个不同 ID**。例：AIX 智能下载器 Edge 版 `pljfekbkmmbkdfhddpebdlmfngigcohc`、Chrome 版 `ibdfeimkglcmdejppabkaidpippniiob`；WorkBuddy Edge 版 `ndbfelmlimfjklodckmbalfioaehegpc`、Chrome 版 `ajnnogdfpilbhkeggdjlcokgglijmdde`。**按 ID 集合做差集判断"缺哪些扩展"必误判**，必须按名字（manifest.name）比对。
3. **UI 快照/页面计数不能当证据**。`chrome://extensions/` 的 accessibility 快照是异步渲染的：4 秒快照只有 1041 字符、只列出 2 个，而落盘事实是 10 个已装（3 启用 7 禁用）。判定装没装、启没用，看 `Extensions/<id>/<ver>_0/` 目录是否存在 + `Secure Preferences` 的 `extensions.settings.<id>.path/disable_reasons/from_webstore`，别看页面。
4. **`disable_reasons=[1]` = 用户手动禁用**，不是迁移失败。看到它先问用户，别当成 bug 去"修"。
5. **连续失败两次就该停下问，而不是换第三条路**。本例四条路（手拷文件/官方 import/load-extension/商店安装）全部零效果，却每条都汇报了"有进展"——把试错当成了交付。

**Why**：把"试过"当成"推进"，会把用户的事做成自己的实验场，还覆盖用户数据（本例中手动改过 ego 的 Secure Preferences 与 Local State 默认 profile）。判定类问题（装没装/缺哪些）拿不到可靠证据时，正确答案是"我不知道，需要 X"而不是再猜一次。

**How to apply**：任何"把 A 浏览器的 X 迁到 B 浏览器"的任务：① 先确认 B 的安装机制与数据真源（落盘文件，不是 UI）；② 按名字而不是 ID 比对；③ 用落盘状态给结论；④ 两次失败就停下来把机制讲给用户、让用户决定装还是弃。相关：[[tencent-browser-skill-setup]]、[[browser-extension-forensics-and-migration]]。

关联 [[zcode-iab-web-automation-capability-boundary]]。
