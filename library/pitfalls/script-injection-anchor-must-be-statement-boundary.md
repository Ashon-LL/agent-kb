---
name: script-injection-anchor-must-be-statement-boundary
description: 往 PowerShell/Bash 脚本里插代码，锚点必须落在语句边界（整条 if/elseif 链之前或之后）；-Check 类预检跑不到的位置等于没验证
type: pitfall
topic: toolchain
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：给别人的脚本（PowerShell / Bash / .bat）做注入式修改时，**锚点必须是语句边界**——不能插在 `if` 与 `elseif`/`else` 之间、不能插在函数签名与函数体之间、不能插在 `try` 与 `catch` 之间。并且 `-Check`/`--dry-run` 只覆盖预检路径，**不能当作「整脚本可运行」的证明**。

**Why**：ZCode 交付脚本的升级流程里，我给 `update-zcode.ps1` 插了一个清理函数，锚点选在 `if ($__isLive -or $ForceKill) { Close-ZCode }` 这一行**之后**——而它后面紧跟 `elseif (Get-Process ZCode …) { … }`。函数定义把 `if`/`elseif` 劈开，PowerShell 把孤立的 `elseif` 当命令，报 `无法将"elseif"项识别为 cmdlet` 并在**替换 asar 之前**中止。`-Check` 之所以没发现：它在预检分支就 `exit 0`，根本执行不到被劈断的位置；构建期也只有中文/CRLF/BOM 格式校验，没有 PowerShell 语法解析。

**How to apply**：① 插函数定义选「整条 if/elseif 链之前」或「独立语句之间」，插调用选「关应用/快照/替换」这种明确的语句边界；② 插入后**实际解析一遍**（`[System.Management.Automation.PSParser]::Tokenize()` 或直接跑一次真实路径的干跑），不要只依赖 `-Check`；③ 让注入后用到的每处调用都 `| Out-Null`，避免函数返回布尔值被打到控制台；④ 失败运行日志要留：本例日志显示「快照已做、缓存已移、asar 未动」，据此可立刻判定无半升级。

关联 [[bundle-injection-strict-scope-startup-smoke]]、[[minified-alias-must-resolve-at-build-time]]、[[flaky-test-needs-margin-and-full-failure-log]]。
