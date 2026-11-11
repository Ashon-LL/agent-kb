---
name: winget-powershell7-msix-userscope
description: winget install Microsoft.PowerShell 默认装 MSIX 用户级包——pwsh 落在 WindowsApps 别名(符号链接到 C:\Program Files\WindowsApps\Microsoft.PowerShell_*\pwsh.exe)，不在 C:\Program Files\PowerShell\7；验证用 pwsh --version + Get-AppxPackage，别找 Program Files\PowerShell\7；powershell 仍是 5.1、pwsh 才是 7（并排不替换）；Windows Terminal 的 PS7 默认 profile GUID={574e775e-4f2a-5b96-ac1e-a2962a402336}、source=Windows.Terminal.PowershellCore
type: tool
source: default 会话（2026-11-04 本机 Windows 11 26H2 实测，winget v1.29.380）
date: 2026-11-04
verified: 2026-11-04
topic: powershell, windows, toolchain
---

**经验**：在本机用 `winget install --id Microsoft.PowerShell -e --silent` 装 PowerShell 7：

1. **装的是 MSIX 用户级包，不是机器级 MSI**：实体在 `C:\Program Files\WindowsApps\Microsoft.PowerShell_<ver>_x64__8wekyb3d8bbwe\pwsh.exe`，`C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\pwsh.exe` 是指向它的**符号链接**（非 0 字节商店占位）。`C:\Program Files\PowerShell\7\` **不存在**——别按 MSI 路径去找而误判"没装上"。
2. **验证可用性**：`pwsh --version`（PATH 已有 WindowsApps 别名）+ `Get-AppxPackage Microsoft.PowerShell | Select Version,InstallLocation`。当前会话 PATH 可能未刷新，重开终端即有；必要时直接用 WindowsApps 全路径。
3. **并排不替换**：`powershell` 命令仍是 Windows PowerShell 5.1，`pwsh` 才是 7。装 7 不会改变任何软件原本对 `powershell` 的调用。
4. **Windows Terminal 默认**：PS7 的 profile GUID 恒为 `{574e775e-4f2a-5b96-ac1e-a2962a402336}`、`source: Windows.Terminal.PowershellCore`（动态探测 pwsh）。本机 settings.json 的 `defaultProfile` 早已指向它 ⇒ 装好 pwsh 后开 Terminal 默认即 7，无需再改。要改默认就改 `defaultProfile`。
5. **附带收益**：pwsh 7 默认 UTF-8 输出，消除 5.1 在 Git Bash 里的中文乱码（5.1 按 GBK/UTF-16 输出被按 UTF-8 读成 `鏄惁`）；并支持 `&&`/`||`、三元、`-Parallel` 等 5.1 没有的语法。

> ⏰ 时效状态（2026-11-04 记录，**未复核**）：本次装到版本 7.6.9.0；winget 默认走 MSIX 用户级。
> ⚠️ 用前必须实测：`pwsh --version`；`Get-AppxPackage Microsoft.PowerShell | Select Version,InstallLocation`；若要机器级 MSI 改装 `winget install --id Microsoft.PowerShell --scope machine` 或官网 MSI。

**Why**：按 MSI 习惯去 `Program Files\PowerShell\7` 找会扑空、误以为安装失败而反复重装；以为装 7 会"接管"系统默认而担心副作用——实际并排共存，`powershell` 不变。

**How to apply**：给 agent 软件补 pwsh 7 时按上面验证；用户问"会不会成默认"答"不会，powershell 仍 5.1、pwsh 才是 7；Terminal 默认看 defaultProfile"。相关：[[powershell-tool-stdout-empty-write-files-instead]]、[[codex-hook-command-must-be-valid-in-powershell]]、[[windows-scripting-terminal-gotchas]]。

关联 [[powershell-tool-stdout-empty-write-files-instead]]、[[codex-hook-command-must-be-valid-in-powershell]]、[[zcode-platform-verified-facts]]。