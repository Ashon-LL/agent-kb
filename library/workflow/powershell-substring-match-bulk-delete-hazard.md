---
name: powershell-substring-match-bulk-delete-hazard
description: 用 -match/正则做批量"删除同名变量/文件"时子串会误伤——`$n -match "ACC"` 把 ELECTRON_FORCE_RENDERER_ACCESSIBILITY 和 GITHUB_PERSONAL_ACCESS_TOKEN 一并删掉（都含 ACC）；批量删除必须用 -eq/-ceq 精确匹配或先把命中清单打印出来人工确认
type: workflow
source: 2026-10-08 default 会话清理 ACC_PRODUCT_CONFIG_V3 时误删两个用户级环境变量（含 GitHub PAT），靠注册表导出快照 1 分钟内还原
date: 2026-10-08
verified: 2026-10-08
topic: powershell, safety
---

批量删环境变量/文件时用**子串匹配**当下就是删除条件，命中面会比预期大得多。实测：`if ($n -match "ACC") { $k.DeleteValue($n, $false) }` 想删 `ACC_PRODUCT_CONFIG_V3`，实际连带删掉 `ELECTRON_FORCE_RENDERER_ACCESSIBILITY`（含 "ACCessibility"）和 **`GITHUB_PERSONAL_ACCESS_TOKEN`**（含 "ACCess_token"）——后者是 GitHub 插件 MCP 依赖的凭据。

**Why**：子串误伤在"打印清单"阶段无害，在"直接删"阶段就是事故；且被误删的常常是**看不出关联的凭据类变量**，缺失时报错点离现场很远（GitHub 插件不加载、MCP 401），极难联想到"删环境变量时手滑"。

**How to apply**：
- 精确删：`-eq`/`-ceq`（PowerShell 字符串比较默认**不区分大小写**，`-ceq` 才区分）；文件名同理用 `-like` 配通配符而非 `-match`。
- 两段式：先 `Where-Object` 出**全名清单**并打印/落盘，人工或规则确认后再删；删完立即**逐项核对**（值的长度/存在性，不打印敏感值本身）。
- 大批量破坏性操作前先做**注册表导出/文件复制快照**（`reg export HKCU\Environment …`、复制待改文件），出错时 `reg import` 秒级还原——本次即靠动手前 2 分钟做的快照还原了两个变量。
- 循环里删注册表值时 `GetValueNames()` 的快照要先物化成数组（`@(...)`），边遍历边删会漏项或炸迭代器。

关联 [[subagent-absence-and-security-claims-need-selfcheck]]、[[windows-home-cleanup-safe-vs-traps]]、[[user-instruction-is-not-evidence-of-no-dependency]]。