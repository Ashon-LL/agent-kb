---
name: powershell7-zip-install-github-blocked
description: PowerShell 7.7 起官方不再发 MSI（release 资产只有 zip/msixbundle），winget 直连 github.com 报 InternetOpenUrl failed 0x80072efd；改从 TUNA github-release 镜像取 PowerShell-7.7.0-win-x64.zip，核对 hashes.sha256 后解压到 C:\Program Files\PowerShell\7、Unblock-File、机器 PATH 前置即可；卸载 MSIX 包会连带杀掉正在运行的 pwsh 进程（命令中断是预期），WindowsApps 的 pwsh 别名随之消失
type: tool
source: 2026-11-23 本机（Win 26H2 26300.9711，OpenCode 2.3.2）shell 偶发「拒绝访问 os error 5」排查
date: 2026-11-23
verified: 2026-11-23
topic: powershell, windows, toolchain
---

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

**How to apply**：遇到「装了 pwsh 但宿主间歇报拒绝访问 / os error 5」「winget 装 PowerShell 报 0x80072efd」「想给 pwsh 一个稳定绝对路径」时按上面做。代价：ZIP 安装不进「应用和功能」、不自动更新，升级时重复下载解压覆盖（先退掉所有 pwsh 进程）。相关：[[winget-powershell7-msix-userscope]]、[[windows-scripting-terminal-gotchas]]。
