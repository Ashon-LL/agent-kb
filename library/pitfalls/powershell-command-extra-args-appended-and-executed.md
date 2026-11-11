---
name: powershell-command-extra-args-appended-and-executed
description: powershell -Command 之后的额外参数会被追加到命令串末尾；若该参数是文件路径，会被当成命令执行并触发文件关联（默认程序弹出打开该文件）；传路径/动态内容一律嵌进脚本字面量
type: pitfall
source: zcodepro v29.19 孤儿清理事故（2026-11-08）
date: 2026-11-08
verified: 2026-11-08
topic: toolchain
---

## 经验

用 `execFile('powershell.exe', ['-NoProfile', '-Command', ps, SOME_PATH])` 想「把路径作为 `$args[0]` 传给脚本」时，**PowerShell 并不会把它当参数**，而是把 `SOME_PATH` **追加到命令串末尾**，变成脚本最后一条裸命令。若该路径指向一个带文件关联的文件，PowerShell 会执行它 → 触发关联 → 默认程序弹出打开该文件。

实例（zcodepro v29.19 `reapOrphans`）：把维护日志路径 `~/.zcode/v2/zsm-maintenance.log` 作为第 4 个参数传进去，结果每次维护（orphanOn 打开后每 30 分钟一次）弹出 Notepad-- 打开该日志；同时 `$args[0]` 恒为空，脚本里 `Add-Content -Path $args[0]` 的日志永远写不进去。用户以为「exec 清理有输出」，实际是孤儿清理的命令行拼坏了。

## Why

`powershell -Command <string> [extra args...]` 的语义是「把剩余参数**追加到命令串**再执行」，不是「传给脚本的 `$args`」。`-File` 的行为又不同（剩余参数传给脚本），两者不能凭直觉混用。实测：`powershell -NoProfile -Command 'C:\path\x.log'` 与 `powershell -NoProfile -Command 'Write-Output hi' 'C:\path\x.log'` 都会让默认程序打开该文件。

## How to apply

- 需要把路径/动态内容传给 PowerShell：**作为字面量嵌进脚本内部**（单引号包裹，`'` 转义成 `''`），`-Command` 只跟脚本本身，不传额外参数。
- 别再依赖「额外参数会进 `$args`」；要传参就用 `-File` 或把值写进脚本。
- 症状识别：某个后台任务「老是弹出默认程序打开某个文件」= 有人把文件路径拼进了 shell 命令串。用进程创建监听（WMI `__InstanceCreationEvent`）抓目标进程的**父进程命令行**，比猜快。
- Windows 进程枚举仍只能走 PowerShell/CIM：本机 `wmic` 已不存在，`tasklist` 无 PPID；别为「避开 PowerShell」去换更脆的工具。
