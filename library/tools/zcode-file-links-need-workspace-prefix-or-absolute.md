---
name: zcode-file-links-need-workspace-prefix-or-absolute
description: ZCode 对话里的本地文件链接必须用绝对路径或带工程子目录前缀的相对路径——只写 out/xxx 会相对工作区根解析，子目录工程里必然打不开
type: tool
source: 10years-humanity EP04（用户多次反馈链接打不开，2026-11-07）
date: 2026-11-07
verified: 2026-11-07
topic: zcode
---

## 经验

ZCode 的 Markdown 文件链接按**工作区根目录**解析，不是按当前 shell cwd 或工程目录。
工作区根是 `%USERPROFILE%\Videos\Bili`，工程在 `10years-humanity/` 子目录时：

- ❌ `[x](out/preview/x.mp4)` → 解析成 `Bili/out/preview/x.mp4`（不存在）
- ✅ `[x](10years-humanity/out/preview/x.mp4)` → 正确
- ✅ `[x](%USERPROFILE%/Videos/Bili/10years-humanity/out/preview/x.mp4)` → 最稳（正斜杠）

## Why

用户在客户端点链接打不开时会以为文件不存在或路径错了，实际是解析基准不同；
子目录工程里所有相对链接都会偏一层。Windows 路径用正斜杠，反斜杠在 Markdown 里易被转义。

## How to apply

- 对话里给本地文件链接：默认绝对路径（正斜杠），或确认工作区根后带子目录前缀。
- 不确定工作区根时，先 `pwd` 看 shell cwd 与工程目录的层级差。
- 相关：[[zcode-platform-verified-facts]]。
