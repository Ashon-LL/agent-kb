---
name: windows-home-cleanup-safe-vs-traps
description: Windows 用户目录清理口径——更新器安装包/缓存可删，但 %APPDATA%\npm 是全局 CLI 入口不是缓存（删了废掉 cnb/pnpm 等命令）；孤儿 MSI 记录要单独清
type: tool
source: 2026-10-06 default 会话清理 C:\Users\MECHREVO（释放 70.5 GB）
date: 2026-10-06
verified: 2026-10-06
topic: windows
---

**经验**：清 Windows 用户目录前，先把「缓存」和「CLI 入口」分开——两者长得像，删错直接废掉命令行。

## 可安全删（本次实测）

| 类别 | 典型路径 | 说明 |
|---|---|---|
| **更新器安装包残留** | `%LOCALAPPDATA%\<app>-updater\installer.exe`、`pending\` | Electron 更新器装完不删，是最大一类纯垃圾。按 `*updater*` 名扫一遍 |
| 包管理器缓存 | `%LOCALAPPDATA%\uv\cache`、`pip\cache`、`npm-cache`、`~\.cache\huggingface` | 删后按需重下 |
| 构建/运行时缓存 | `.cache\acode-runtimes`、`ms-playwright`、`node-gyp` | 可重下 |
| 解包暂存 | `Arduino15\staging`、`Arduino15\tmp` | **不是**已装包（`packages\` 才是） |
| 应用缓存 | `PCAppStore\storecache`、`Everything\Everything.backup.db`、`CrashDumps` | 索引/备份可重建 |
| Temp | `%LOCALAPPDATA%\Temp`（清内容保目录） | |

## ⛔ 陷阱：看着像缓存、其实是入口

**`%APPDATA%\npm`（即 `~/AppData/Roaming/npm`）不是缓存。** 里面是**全局 npm CLI 的 shim 脚本 + node_modules**：`cnb`、`pnpm`、`agent-browser`、`wrangler`、`mcp-server-sequential-thinking` 等全在这里。删了这些命令直接失效。
判据：目录里有 `*.cmd` / `*.ps1` / 无扩展名的同名脚本三件套，就是 shim 不是缓存。

同理 **`%LOCALAPPDATA%\Microsoft\WinGet\Packages\`** 放的是 winget 装的工具**本体**（ffmpeg/pandoc/uv/mutool），不是下载缓存，删了工具就没了。

## 孤儿 MSI 注册记录

「已装列表里有、但文件早没了」的条目（本次 Python 3.11.9）：`python311.dll`、`Python311\` 目录全盘搜不到、`py -0p` 不列、PATH 无引用 ⇒ 文件已被删，只剩注册表空壳。
- 直接跑缓存里的卸载器多半报 **1603**（MSI fatal，日志里 `LaunchConditions. Return value 3`）。
- 逐组件 `msiexec /x {GUID} /qn /norestart` 能清掉一部分，剩下的报 **1709**（"package not available"，包缓存失效）。
- 残留的空壳记录可直接 `Remove-Item` 掉对应 `Uninstall\<GUID>` 键（清前先确认文件真没了、`py -0p`/PATH 都不引用）。

## 设备管理器里的"神秘显卡/神秘设备"：远程软件卸载残留

第三方远程控制/投屏软件（连连控 AskLink、ToDesk、向日葵、Parsec 等）会装 **IDD 虚拟显示器 + 虚拟手柄**驱动（ROOT 枚举、名字怪如 `AskLinkIddDriver Device`）；App 卸载后驱动常留原地，设备管理器里凭空多一块"显卡"。取证四步（全程只读）：① `Get-PnpDevice` 拿 InstanceId → ② `DriverStore\FileRepository\<inf>_amd64_*` 目录里 .dll/.sys 的 `VersionInfo.CompanyName` + `pnputil /enum-drivers` 的提供程序名（实名厂商，WHQL 签名看 `Get-AuthenticodeSignature`）→ ③ DriverStore 目录的 CreationTime 即安装时刻，`HKLM\SOFTWARE\<vendor>` 键里有安装包文件名与时间线 → ④ 宿主是否还在：卸载表/Program Files/MuiCache/进程扫品牌名。确认 App 已走后清理用 `pnputil /delete-driver oemNN.inf /uninstall /force`（连带删服务+设备），再删厂商键；内核虚拟手柄驱动 Start=System 每次开机加载，残留不是零成本。

**Why**：把 `%APPDATA%\npm` 当缓存删掉，会让本机所有 npm 全局命令消失，而它们恰是各种 MCP/CLI 工具的入口——症状是"明明装了却 command not found"，排查成本远高于收益。反过来，`*updater*` 目录白占几百 MB~GB 且永远不再用，是最该优先清的。

**How to apply**：
- 扫描先按体积排序，再**逐个确认"这目录里是什么"**（`installer.exe` = 可删；`*.cmd`+node_modules = 入口，留）。
- 判断"某软件是否已卸载"别只看注册表：查 `C:\Software`、`C:\Program Files` 里有没有活的 exe，没写注册表的绿色版常被误判成残留。
- 删前记 `Get-PSDrive C` 的 Free 基线，删后核对释放量（本次 471.57→542.07 GB）。
- 体积小但确认无引用的散落文件（根目录的 `*.bak`、临时脚本）单独一批删，别和目录清理混。
- 删完空间没回来先别怀疑卸载失败：跑 `vssadmin list shadows`。卷影副本会把快照时点已存在文件的磁盘块钉住，文件删除后空间仍不归还，直到该副本被删/过期（实测 2026-10-07 05:59 的 ClientAccessible 副本钉住了 coreutils 删掉的 1.4 GB；同机器上 pagefile.sys 会随内存压力自动增减，测量释放量前先排除它）。
- 删注册表键时 pwsh `Remove-Item -Recurse -Force` 可能对 ACL 完全正常的键报 `SecurityException: Requested registry access is not allowed`（实测 AskLink 残留键，重试无效）；换 `reg.exe delete "<key>" /f` 直接成功。另：Git Bash 里 reg.exe 的 `/f` 会被 MSYS 改写成路径报"无效语法"，须加 `MSYS_NO_PATHCONV=1` 或在 pwsh 内调用。

关联 [[esp32-arduino-cli-flash-workflow]]、[[windows-update-resume-and-no-auto-reboot-playbook]]。