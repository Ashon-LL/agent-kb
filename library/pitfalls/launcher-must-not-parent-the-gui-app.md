---
name: launcher-must-not-parent-the-gui-app
description: 更新脚本/安装器启动 GUI 应用别用 Start-Process 直接起——应用会成为脚本子进程，既继承脚本窗口的控制台句柄（应用日志被打印进脚本窗口），又落在脚本进程树里（默认终端是 Windows Terminal 时，关标签会连带杀整棵进程树 ⇒ 关脚本窗口＝关应用）
type: pitfall
source: zcodepro（ZCode 一键更新脚本 update-zcode.ps1）
date: 2026-10-29
verified: 2026-10-29
topic: windows, toolchain, safety
---

**症状**（用户口径）：跑完更新脚本，**应用日志被打印进脚本那个窗口**；而且**关掉脚本窗口，应用也跟着退了**。
更隐蔽的变体：脚本跑完那个窗口会**自己关闭**，于是"应用刚被脚本启动、一秒后又被脚本窗口的关闭带走"，看起来像应用自己闪退。

**根因**是一行启动代码：

```powershell
Start-Process -FilePath $exePath      # ❌
```

它把应用起成**脚本的子进程**，两个后果都从这一处来：

1. 子进程继承脚本窗口的控制台句柄 ⇒ 应用的 stdio 输出落进脚本窗口（"日志跑进脚本里"）；
2. 子进程落在脚本的进程树里 ⇒ 本机默认终端若是 **Windows Terminal**，关标签会**连带杀掉整棵进程树**，于是关窗口＝关应用。

⚠️ 注意：应用是 **GUI 子系统**（`PE Subsystem=2`）**也不能幸免** —— "GUI 程序不附着控制台"只说明它不 attach 控制台，但句柄继承与进程树归属是两码事。别用 PE 子系统当挡箭牌。

**修法：把启动交给一个在你自己进程树之外的常驻进程代办**

```powershell
Start-Process -FilePath 'explorer.exe' -ArgumentList "`"$exePath`"" -ErrorAction Stop | Out-Null
```

新进程的父进程是 explorer，不继承本窗口的控制台句柄，也不在本进程树里。

**别用 DETACHED_PROCESS 代替**（本机会引发黑窗风暴，见
[[detached-process-causes-console-window-storm]]）；也不要指望 `CreateNoWindow` ——
它和 `DETACHED_PROCESS` 同时给会被忽略，而且它不解决"仍在本进程树里"这一半。

**怎么验证（别靠肉眼）**：

1. 启动后查真实父进程：`(Get-CimInstance Win32_Process -Filter "ProcessId=<child>").ParentProcessId` → 再查那个 pid 的名字，应当是 `explorer`；
2. 更直接的端到端判据：**让脚本窗口关掉，看应用是否还在**。等价的可判定信号是「那段时间起的 cmd/powershell/conhost 进程一个都不剩，而应用还在跑」；
3. ⛔ **自测用 `-NoStart`/只写临时目录的用例全部盖不到启动路径** —— 这个坑就是这么溜过一整套自测的。凡改启动方式，必须单独加一条"装完关窗口，应用要活着"的用例。

**顺带一条同源加固**：覆盖大文件（几百 MB 的 asar/zip）别"先备份再直接覆盖目标"——中途关窗口/断电会留下写了一半的目标文件。改成
「先写同目录临时文件 → 校验 → `[System.IO.File]::Replace` 原子替换」，目标要么是旧的、要么是新的。

关联 [[updater-kill-must-anchor-to-live-install]]、[[detached-process-causes-console-window-storm]]、[[file-change-not-code-running]]。
