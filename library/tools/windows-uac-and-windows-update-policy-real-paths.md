---
name: windows-uac-and-windows-update-policy-real-paths
description: UAC 的 EnableLUA 真实注册表位置是 HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System（Policies\Microsoft\Windows\System 下同名路径为空，读错会误判 UAC 开着）；NoAutoUpdate 若要查在 WindowsUpdate\Automatic Updates 子键；2026-10-08 子代理在这两处都报错，主-agent 抽查才纠正
type: tool
source: 2026-10-08 default 会话全机体检（子代理结论抽查，UAC 与更新策略两处纠错）
date: 2026-10-08
verified: 2026-10-08
topic: windows, registry, security
---

查 Windows 安全/更新策略的注册表值时，**路径有两套同名近似物，读错位置会得出相反结论**：

| 目标值 | 真实位置 | 陷阱 |
|---|---|---|
| `EnableLUA` / `ConsentPromptBehaviorAdmin` / `PromptOnSecureDesktop`（UAC） | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` | `HKLM\SOFTWARE\Policies\Microsoft\Windows\System` 下同名的值**不存在**，`Get-ItemProperty` 返回空——看到空值若直接下结论"UAC 开着"就反了（实测本机 EnableLUA=0，即 UAC 全关） |
| `NoAutoUpdate`（禁用自动更新） | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\Automatic Updates`（经典位置） | 直接在 `...\WindowsUpdate` 根下查同名值可能为空；而 `...\WindowsUpdate\ExcludeWUDriversInQualityUpdate=1` 确实存在于根下——同键不同值，**不能因一个值在就断定另一个也在** |

**Why**：2026-10-08 一次全机体检里，子代理（和我第一次自查）都在 UAC 上读错路径，差点把"UAC 已关"报成"UAC 未配置/正常"；另一路子代理报"更新被 `NoAutoUpdate=1` 策略屏蔽"，实际该值并不存在——若照单全收，方案就会给出错误的根因和错误的修复动作（去删一个不存在的策略值）。

**How to apply**：
- 读策略前先 `Get-ItemProperty` 目标键并**同时打印实际存在的值名**（`$k.GetValueNames()`），空输出要区分"键不存在"和"值不存在"。
- Windows Update 搜索返回 0 项≠系统最新：先查策略（`...\WindowsUpdate` 与 `...\Automatic Updates` 两处）、再看最近成功安装的 KB 日期（`Get-HotFix | Sort InstalledOn`），KB 长期不动才是真信号。
- 子代理/子探针转述的**安全策略值**一律自己抽查一次再写进报告——见 [[subagent-absence-and-security-claims-need-selfcheck]]。

关联 [[windows-home-cleanup-safe-vs-traps]]、[[subagent-absence-and-security-claims-need-selfcheck]]。