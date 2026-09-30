---
name: powershell-tool-stdout-empty-write-files-instead
description: PS 工具执行成功但 stdout 回传恒为空（`Stdout: (empty)`，命令没跑没输出）；判据是「跑没跑」看 $LASTEXITCODE 和产出文件、不看 stdout；解法=让 PS 写文件再用 Bash 读
type: pitfall
source: WorkBuddy PS 工具调用（ZCode 侧 Bash 调 PowerShell，2026-09-18 实测；正文标注环境 Windows 10.0.26200 / PS 5.1.26100.8115）
date: 2026-09-18
verified: 2026-09-18
---

## WorkBuddy PS 工具：执行正常，但 stdout 回传恒为空（改用「写文件 + Bash 读」）

> 2026-09-18 实测。环境：Windows 10.0.26200，PS **5.1.26100.8115**（Desktop 版）。
> 宿主固定为 `System32\WindowsPowerShell\v1.0\powershell.EXE -NoProfile -NonInteractive -Command <命令>`。

## ⛔ 先认清「本机有两个 PS，工具只用其中一个」

实测本机**同时存在两套**：

| 命令 | 路径 | 版本 |
|---|---|---|
| `powershell` | `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe` | **5.1**.26100.5074（Desktop） |
| `pwsh` | `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\pwsh.exe`（**0 字节** = App Execution Alias） | **7**.6.5 |

- **PS 工具用的是 5.1**（transcript 的「主机应用程序」行可见完整路径，`PSEdition=Desktop`）。
- ⛔ 两个版本的**行为不可互相推断**：本次实测同一段缺陷代码，
  在 5.1 抛 `无法处理命令…强制参数丢失: EventName`，在 7.6.5 则走**另一条路径**
  （被 `catch` 接住，但 `$PSVersionTable` 读回**空值**）。
- ⇒ 只要涉及 PS 版本相关的判断，**必须分别实测两个版本**，不能只测一个就下结论。
- 从 PS 工具里驱动 pwsh：`& pwsh -NoProfile -File <脚本>` **可用**；
  但被驱动的 pwsh 里 `$PSVersionTable` 可能读到空 ⇒ **不要靠它判断版本，靠 `pwsh --version`**。

## 现象（最反直觉的一点）

工具返回 `Stdout: (empty)` 时，**脚本往往真的跑了、也真的输出了**。
`Stdout: (empty)` **只说明回传通道丢了**，**不能**据此判定「没跑 / 没输出 / 命令不存在」。

⇒ 这是「查不到 ≠ 不存在」家族的又一例，**但这次是回传层而非查询层**。

## 取证手法（可复算）

用 `Start-Transcript` 把真实输出落盘，再读回对照：

```powershell
Start-Transcript -Path C:\tmp\ps_transcript.txt -Force | Out-Null
Write-Output "TEST-A"
Write-Host "TEST-B"
"TEST-C: bare string"
42
Stop-Transcript | Out-Null
```

实测结果：**四种输出形式在 transcript 里全部出现**，而工具回传的 `Stdout` 仍为空。
transcript 同时会打印宿主的完整命令行 —— **想知道工具怎么包装你的命令，这是最快的入口**。

## ✅ 可靠通道

| 通道 | 是否可靠 | 备注 |
|---|---|---|
| **写文件（.NET API）** | ✅ 可靠 | 唯一推荐的取结果方式 |
| **`Exit Code`** | ✅ 可靠 | `exit 7` → 工具如实报 `Exit Code: 7` |
| `Stdout` | ⛔ 恒空 | 别指望；也别据此做判断 |
| `Stderr` | ⛔ 恒空 | 同上（报错信息也拿不到） |

## 写文件的三个硬约束（都踩过）

1. **用 .NET API，不用管道/重定向**
   ```powershell
   [System.IO.File]::WriteAllLines($path, $lines,
       (New-Object System.Text.UTF8Encoding($false)))   # $false = 不写 BOM
   ```
2. **`> file` 是截断语义** —— 多行分次追加会互相覆盖；`>>` 也仍是 PS 的原生重定向，
   编码不受你控制。
3. ⛔ **`Out-File -Append -Encoding utf8` 在 PS 5.1 里实为 UTF-16LE** ——
   稍后用 UTF-8 读会得到乱码（实测 `v24.19.0` 读成 `㉶⸶⸹`）。
   **别信 `-Encoding utf8` 的字面**，它在这版里不等于「UTF-8 无 BOM」。

## 子进程：拿 stdout / stderr / exit code

```powershell
$p = Start-Process -FilePath "node.exe" -ArgumentList @('C:\tmp\probe.mjs') `
     -NoNewWindow -Wait -PassThru `
     -RedirectStandardOutput "C:\tmp\out.txt" -RedirectStandardError "C:\tmp\err.txt"
$p.ExitCode        # 实测准（子进程 exit 3 → 报 3）
```

- **两个流必须指向不同文件**（同文件会相互覆盖）。
- ⛔ **`-ArgumentList` 里的内层双引号会被剥掉**：
  `@('-e', 'console.log("x")')` 到 node 手上变成 `console.log(x)` ⇒ `ReferenceError`。
  ⇒ **带引号的代码一律写成独立脚本文件**（`.mjs`/`.ps1`）再传路径，别塞进 `-e`。

## ⛔ 两条通道各自封死

- `Start-Process cmd.exe` 被拒：`Starting cmd.exe from PowerShell bypasses PowerShell command validation`
- 从 Bash 里调 powershell/pwsh 被拒：`Invoking PowerShell from Bash bypasses PowerShell security checks; use the PowerShell tool instead`

⇒ **不存在「换个入口把 stdout 捞出来」的取巧路径**。唯一正解就是「PS 写文件 → Bash 读」。

## 推论：脚本形态上的要求

需要在本机跑、且要拿回结果的脚本，**必须自带「把全部证据写文件」的设计**——
不能依赖调用方看 stdout。反面样板：只在控制台 `Write-Host` 结果的脚本，
在这种环境下等于**跑完什么也看不到**。

## ⛔ PSSA 1.25 在 5.1 下装不上——「命令没跑」再次伪装成「0 条结果」

`PSScriptAnalyzer` 1.25 只随 pwsh 7 分发；在 Windows PowerShell 5.1 下
`Invoke-ScriptAnalyzer` 直接 `CommandNotFoundException`。⛔ 若外面套了 `@( ... )`
收集结果，命令不存在会被**静默当成空数组** → "0 findings" 假绿，把「没跑」当成
「跑了且干净」。

- 5.1 lane 钉 PSSA ≤1.21（1.25 装不进 Desktop）；7.x 用 1.25。
- 判「分析器真跑了」看版本行/规则计数输出，别只看 findings 条数。

## 关联

- `log-text-is-not-spec-read-emitting-code.md` —— 同属「别把观察到的表象当结论」。
- `file-change-not-code-running.md` —— 同属「如何确认一件事真的发生了」。
- `cnb-cli-needs-cmd-suffix-when-spawned-from-python.md` —— 同属「Windows 上的调用姿势坑」。
