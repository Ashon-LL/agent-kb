---
name: powershell-bool-eq-string-casts-string-to-bool
description: PowerShell bool -eq string 时先把 string 转 bool（非空=True），导致 $true -eq "toml" 返回 True
type: pitfall
source: agent-kb hooks 多平台部署（2026-09-20）
date: 2026-09-20
verified: 2026-09-20
---

**教训**：PowerShell 里 -eq 两侧类型不同会触发隐式转换，方向是把右边转成左边。所以 $true -eq "toml" 会先把 "toml" 转成布尔（非空串 → $true），再比较 $true -eq True → **True**！这让 if/else 分支全部走错，把 JSON 当 TOML 追加了进去。

**解法**：布尔和字符串比较时显式转类型：
`powershell
# ✅ 正确
if ([string]$t.MergeConfig -eq "toml") { ... }
# 或
if ($t.MergeConfig -is [string] -and $t.MergeConfig -eq "toml") { ... }

# ❌ 错：$true -eq "toml" 也会进 TOML 分支
if ($t.MergeConfig -eq "toml") { ... }
`

**How to apply**：PowerShell 脚本里用 -eq 区分字符串值和布尔值时，先显式转类型再比。相关：[[cnb-npc-dispatch-essentials]]。
