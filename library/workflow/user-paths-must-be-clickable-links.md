---
name: user-paths-must-be-clickable-links
description: 给用户的一切本机路径（交付物、脚本、日志、配置）一律写成可点击 Markdown 链接 `[显示名](绝对路径)`，不要给纯文本路径串；纯文本要用户手打或自己翻目录
type: workflow
source: ZCode 改造项目（2026-10-18 用户明确要求「以后给我可点击打开的路径」）
date: 2026-10-23
verified: 2026-10-18
topic: delivery
---

**经验**：回复里出现的本机路径，一律用 Markdown 链接，不用纯文本。

## 对比

| ❌ 不要 | ✅ 要 |
|---|---|
| `Downloads\Project\zcode改造\zcodepro-patch-src.zip` | `[zcodepro-patch-src.zip](C:\Users\MECHREVO\Downloads\Project\zcode改造\zcodepro-patch-src.zip)` |
| `ZCode-3.15.2new-memfix6\INSTALL-replace-app.asar.bat` | `[INSTALL-replace-app.asar.bat](C:\Users\MECHREVO\Downloads\Project\zcode改造\ZCode-3.15.2new-memfix6\INSTALL-replace-app.asar.bat)` |
| `%USERPROFILE%\.zcode\v2\crash\heap\renderer-memory.log` | `[renderer-memory.log](C:\Users\MECHREVO\.zcode\v2\crash\heap\renderer-memory.log)` |

## How to apply

- 交付物、脚本、日志、配置文件、目录——只要给路径就用链接。
- 显示名用文件名或简短中文，路径用绝对路径（不要 `...` 省略）。
- Windows 反斜杠可直接放在链接目标里；含空格用尖括号或百分号编码，视渲染器而定，优先测一次。

关联 [[deliver-user-tuned-artifact]]、[[report-what-you-did-not-what-you-meant-to-do]]、
[[user-large-files-hardlink-not-copy]]。
