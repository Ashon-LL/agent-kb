---
name: powershell7-install-msix-and-zip
description: PowerShell 7.7 前 MSIX/winget 与 7.7 后无 MSI 的 ZIP 兜底；含 PATH、Unblock-File、卸载 MSIX 的进程中断
type: tool
source: 合并自 powershell7-zip-install-github-blocked, winget-powershell7-msix-userscope；2026-11-23 本机（Win 26H2 26300.9711，OpenCode 2.3.2）shell 偶发「拒绝访问 os error 5」排查; default 会话（2026-11-04 本机 Windows 11 26H2 实测，winget v1.29.380）
date: 2026-11-04
verified: 2026-11-23
topic: powershell, windows, toolchain
---
**经验**：PowerShell 7.7 前 MSIX/winget 与 7.7 后无 MSI 的 ZIP 兜底；含 PATH、Unblock-File、卸载 MSIX 的进程中断

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## powershell7-zip-install-github-blocked

**经验**：PowerShell 7.7 在 Windows 上**已经没有 MSI**，`winget install --id Microsoft.PowerShell` 会去 github.com 下 `.msixbundle`；国内直连 github 常报 `InternetOpenUrl() failed 0x80072efd`。可靠装法是官方 ZIP + 国内镜像：

1. 先确认资产形态：TUNA 目录里 7.7.0 只有 `PowerShell-7.7.0-win-x64.zip` / `...arm64.zip` / `PowerShell-7.7.0.msixbundle`，**没有 .msi**（7.6 及以前才有）。
2. 镜像地址（目录名含空格，必须 `%20`）：
   `https://mirrors.tuna.tsinghua.edu.cn/github-release/PowerShell/PowerShell/v7.7.0%20Release%20of%20PowerShell/`
   同目录的 `hashes.sha256` 可校验；`LatestRelease/` 指向最新版。
3. 下载后先比对：`(Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()` 必须等于 hashes.sha256 里 `*PowerShell-7.7.0-win-x64.zip` 那行（本次实测 `7c74e03b20a75b59715847439d046a6214b1863ee79b187872980f139bb4a05f`）。
4. **解压前删掉同名 junction**：若 `C:\Program Files\PowerShell\7` 是指向 `C:\Program Files\WindowsApps\Microsoft.PowerShell_*\` 的 Junction，必须先 `(Get-Item $dest).Delete()`（只删重解析点），否则解压/安装会写进 MSIX 包体。
5. 解压用 `[System.IO.Compression.ZipFile]::ExtractToDirectory($zip,$dest)`（比 Expand-Archive 快），再 `Get-ChildItem $dest -Recurse -File | Unblock-File` 清 MOTW。
6. 把 `C:\Program Files\PowerShell\7` 放到**机器级 PATH 最前**；验证三件套：`where.exe pwsh`、`(Get-CimInstance Win32_Process -Filter "ProcessId=$PID").ExecutablePath`、`(Get-AuthenticodeSignature "$dest\pwsh.exe").Status`（应为 Valid / CN=Microsoft Corporation）。
7. 卸 MSIX：`Remove-AppxPackage Microsoft.PowerShell_7.6.9.0_x64__8wekyb3d8bbwe`。**如果执行卸载的进程本身就是这个包的 pwsh，它会被一起结束**——终端只显示 `Exit code: 1`，命令看似失败其实已成功；所以先把其它活干完再卸。
8. 卸载后 `%LOCALAPPDATA%\Microsoft\WindowsApps\pwsh.exe` 与 `WindowsApps\Microsoft.PowerShell_8wekyb3d8bbwe\pwsh.exe` 两个别名一起消失。宿主（如 OpenCode）若沿用启动时的 env 快照、PATH 里没有新目录，`pwsh` 会解析失败；此时把宿主配置的 shell 写成绝对路径 `C:\Program Files\PowerShell\7\pwsh.exe` 可立即生效，重启宿主后裸 `pwsh` 也能解析。

**Why**：`winget --scope machine` 在 7.7 上仍可能拿到 msixbundle（微软把 Windows 分发迁到 MSIX/ZIP），而 Store/MSIX 的 `WindowsApps\pwsh.exe` 是 AppExecLink 转发器，被 HIPS/安全软件拦截时就是 `拒绝访问 (os error 5)`；ZIP 装到 Program Files 后是普通 exe，没有别名层，路径稳定且可写进配置。

**How to apply**：遇到「装了 pwsh 但宿主间歇报拒绝访问 / os error 5」「winget 装 PowerShell 报 0x80072efd」「想给 pwsh 一个稳定绝对路径」时按上面做。代价：ZIP 安装不进「应用和功能」、不自动更新，升级时重复下载解压覆盖（先退掉所有 pwsh 进程）。相关：[[powershell7-install-msix-and-zip]]、[[windows-scripting-terminal-gotchas]]。

## winget-powershell7-msix-userscope

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
