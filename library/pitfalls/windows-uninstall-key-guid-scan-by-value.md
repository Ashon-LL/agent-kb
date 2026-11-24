---
name: windows-uninstall-key-guid-scan-by-value
description: Windows 卸载注册表项的键名可能是 GUID 或 is1.xxx（非产品名），按键名搜会漏，必须按 DisplayName 值扫 HKCU/HKLM/WOW6432Node 三处 Uninstall；Electron 应用残留散落 6+ 处，侦察要同时搜产品全称、缩写前缀、组织名，删完复扫一轮
type: pitfall
source: 本机彻底卸载 DSH（DeepSeek Harness 0.2.2-rc.3，2026-11-20）：卸载项键名是 GUID，按键名搜 0 命中；首轮按 *deepseek* 扫描漏掉 3 个 AppData 目录（共 211 MB）
date: 2026-11-20
verified: 2026-11-20
topic: windows
---

**经验**：

1. ⭐ **卸载注册表项的键名不等于产品名**。DSH 的键名是 GUID `1bf39983-50d0-5fe0-9ef4-cece76f67c5e`（HKCU\...\Uninstall 下），NSIS 系常用 `is1.<产品名>` 惯例。`Where-Object { $_.PSChildName -match "deepseek|harness" }` 0 命中，但按 `DisplayName` 值扫就找到了。删卸载项必须按值扫三处（HKCU / HKLM / WOW6432Node）并打印完整键路径后再删；"已删"校验要检查真实键路径，不要检查产品名路径（DSH 的键名不是产品名，检查产品名路径会误报"已删"）。
2. **Electron 应用残留地图（DSH 实测 7 处）**：
   1. 安装目录（`C:\Software\DeepSeek Harness`，1.1 GB，含官方卸载器）
   2. 自定义数据目录（`~/.dsh`，824 MB，含凭证与 profile）
   3. `AppData\Local\<APP名>` + `AppData\Local\<功能子目录>`（`DSH` 空目录 + `dsh-dafeiyu` 207 MB 带版本子目录）
   4. `AppData\Local\@<org>-desktop-updater`（electron-updater 缓存，299 MB）
   5. `AppData\Roaming\@<org>`（user-data-dir，内含产品名子目录 `dsh-desktop`）
   6. `AppData\Roaming\<功能>-electron-helper`（内嵌小应用的 Electron profile，4.4 MB）
   7. 开始菜单快捷方式
   首轮按 `*deepseek*`/`*ds-harness*` 只扫出 5 处；补扫 `*dsh*` 才抓到 3 个 AppData 目录。
3. **短前缀扫描要人工核对误报**：`*dsh*` 会误中 "headshot"（图片目录 `AI Headshot`），扫完逐条确认归属再删。

**Why**

按键名搜卸载项是直觉做法，但安装器（尤其 NSIS/electron-builder）常把键名设为 GUID 或 is1.xxx；"删了没"的校验若指向产品名路径，在键名不是产品名时恒为真，形成假阳性闭环。多目录残留同理：Electron 应用把数据按功能拆到多个 AppData 位置，产品名全称搜不全。

**How to apply**

1. 卸载类任务先全量侦察：安装目录、`~/.<app>`、AppData\Local+Roaming（产品名+缩写前缀+`@org` 三组模式）、注册表三处 Uninstall（按值扫）、开始菜单/桌面快捷方式、进程/服务/计划任务/PATH。
2. 删除前给用户清单（区分"应用残留"与"用户数据"，用户数据让用户拍板），确认后一次删净。
3. 删完用同样多组模式复扫一轮 + 按值复扫注册表，0 残留再报完成。

相关 [[windows-home-cleanup-safe-vs-traps]]、[[electron-builder-nsis-silent-install-fallback]]。
