---
name: browser-extension-forensics-profile-leveldb
description: 排查 Edge/Chrome 扩展问题（"油猴脚本不生效"）的取证路径——读 profile 的 Secure Preferences 判权限/启用状态，LevelDB 被浏览器锁定要用 FileShare.ReadWrite 共享读，location=4 是解包加载（profile 里无文件副本、源目录删了就失效但注册项还在且不能手改）；油猴类脚本还可能依赖本机 RPC 端口（PanLinker 例：localhost:16800 无监听＝核心功能不可用）
type: tool
source: 2026-10-08 default 会话排查 Edge 篡改猴(Tampermonkey 5.5.0 / iikmkjmpaadaobahmlepeloendndfphd) 脚本失效 + 卸载 Browser Relay
date: 2026-10-08
verified: 2026-10-08
topic: browser, methodology
---

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

关联 [[subagent-absence-and-security-claims-need-selfcheck]]、[[powershell-substring-match-bulk-delete-hazard]]。