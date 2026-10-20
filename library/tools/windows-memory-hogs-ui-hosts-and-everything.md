---
name: windows-memory-hogs-ui-hosts-and-everything
description: Windows 11 三个常被误判的内存大户：TextInputHost（输入体验）久跑涨到 500MB+ 可安全重启并以 ~250MB 重生；SearchHost（搜索 UI）~150MB 正常；Everything ≈100-130 字节/条目，排除列表可用 -add-exclude-folders 无头配置（ini 键 exclude_folders 逗号分隔）
type: tool
source: 2026-10-18 本机实测（蛟龙15 Win11，31GB 内存）
date: 2026-10-18
verified: 2026-10-18
topic: windows
---

**经验**：
1. **TextInputHost.exe（Windows 输入体验）**：本机基线约 245–270MB（仅装微软拼音，无第三方输入法），连续运行约 2 天后涨到 **562MB**（缓慢增长，不是中招）；`Stop-Process -Name TextInputHost -Force` 安全，Windows 数秒内自动拉起新进程、回落到约 250MB。它只托管输入法候选窗/表情/剪贴板历史/触摸键盘，不参与索引。
2. **SearchHost.exe（Windows 搜索界面）**：本机 **154MB** 属正常（WinUI/XAML + 网页建议），不是索引器（本机 SearchIndexer 未运行）。想降耗：设置→隐私和安全性→搜索权限→关掉"搜索要点/网页建议"；或改用第三方启动器。**补充（2026-10-18 补）**：即使任务栏搜索框已隐藏（`SearchboxTaskbarMode=0`）、网页搜索/建议已关（`BingSearchEnabled=0`、`DisableSearchBoxSuggestions=1`）、WSearch 服务已停用，SearchHost 仍由外壳常驻；实测**杀掉后 3 秒内被自动拉回**（新 PID ~139MB，33 秒后仍在，20 秒采样 CPU=0s、WS 波动 0.1MB）⇒ 这是预加载设计，kill 无效、没有"空闲卸载"开关。它的 142MB WS 里约一半是共享代码页（private 约 78MB）。真要归零只能移除/禁用 Search 应用（Win+S/Win 键入搜索失效，可用 Everything 代替文件搜索），不推荐。唯一温和可调项是"搜索要点"；但本机 `HKCU\Software\Microsoft\Windows\CurrentVersion\SearchSettings` 受安全软件保护（写值/建测试值均被拒），正确做法是组策略 `HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search\AllowSearchHighlights=0`（Microsoft Policy CSP 有条目，实测可写）；关闭后 SearchHost 内存 **149.2→144.1MB，无实质变化**——它是内容特性，不是内存开关。
3. **Everything 内存 ≈ 100–130 字节/条目**：条目数可用 `fsutil fsinfo ntfsinfo C:` 的 "Mft 有效数据长度" ÷ "每 FileRecord 分段字节数(1024)" 估算（本机 2.30GB → 约 236 万条，含目录）；索引常驻内存是设计，判断是否异常看**峰值是否≈当前**（本机峰值 310MB、当前 235MB 属稳定）。
4. **Everything 无头配置排除**：`"C:\Program Files\Everything\Everything.exe" -add-exclude-folders "C:\Windows\WinSxS;C:\ProgramData\Microsoft;..."`（分号分隔路径，经 IPC 作用于运行中实例）；退出后 ini（`%APPDATA%\Everything\Everything.ini`）里 `exclude_folders=` 存成**逗号分隔**；重启后索引剔除这些条目。本机实测 **235.7MB → 117.8MB**。另有 `-exclude-folders`（覆盖式设置）、`-create-file-list-exclude-folders`（建文件列表时排除）。
5. **避免误判**：任务管理器里的"提交/虚拟内存峰值"不是实占（本机 Everything 虚拟峰值 4.8GB、实占 100–200MB）；判定内存大户取 Working Set + 启动时间 + CPU 累计，并间隔复测看趋势。
6. **TextInputHost 没有官方"内存上限"设置**（2026-10-18 补，gh `memstechtips/Winhance#374` + Tavily 调研）：社区只有两条路——①**彻底禁用**：把 SystemApps 里的 `TextInputHost.exe` 改名 `.old`、`IsInputAppPreloadEnabled=0`；代价=触摸键盘/手写/表情面板（Win+.）/Xbox 键盘失效，多个实测反馈**中文输入法不受影响**；Windows 更新可能还原文件；本机没有 `TabletInputService` 服务、无触摸/手写设备，Winhance 里的服务步骤不适用。②**守护任务**：定时检查，工作集超阈值就杀掉，Windows 数秒内以 ~290MB 重生（本机已落地：`C:\Software\WinMemGuard\TextInputHost-Guard.ps1` + 计划任务 `TextInputHost-MemGuard`，SYSTEM、每 30 分钟、阈值 350MB、日志 guard.log）。**两个计划任务坑**：以 SYSTEM 运行的任务**解析不到 PATH 里的 powershell.exe**（0x80070002），action 必须写全路径 `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`；`schtasks /create` 默认"电池供电不启动"，笔记本必须再用 `Set-ScheduledTask` 把 `DisallowStartIfOnBatteries/StopIfGoingOnBatteries` 置 false（每次重建任务后都要重设）。

**Why**：这三个进程都常被当成"异常占用/中毒"；知道基线、趋势和安全重启方式，才不会误杀或做无效优化。

**How to apply**：用户抱怨某进程占用高 → 先取 Working Set/私有内存/启动时间/CPU → 对照本条基线；TextInputHost 直接重启；Everything 用排除列表（缓存/系统组件优先：pnpm store、npm/uv 缓存、WinSxS、ProgramData\Microsoft、Temp、RecycleBin 等），别关索引本身。相关：[[windows-home-cleanup-safe-vs-traps]]、[[windows-wsl2-memory-accounting]]。

关联 [[no-new-artifacts-in-c-root]]、[[nvidia-driver-update-denied-by-service-key-lock]]、[[windows-hardware-reserved-memory-attribution]]、[[rustup-update-fails-when-stale-msvc-std-component-missing]]。
