---
name: bash-backticks-in-python-string-executed
description: 用 Bash 工具跑 python -c "..." 追加含反引号的 Markdown 时，反引号被 shell 先做命令替换，内容静默损坏（路径变成命令输出/报错）；含反引号的落盘一律走 Write/Edit 工具或 quoted heredoc
type: pitfall
source: 10years-humanity EP05 决策记录追加
date: 2026-11-08
verified: 2026-11-08
topic: toolchain
---

## 经验

在 Bash 工具里用 `python -c "s=open(...).read(); s+='''...`path`...'''; open(...,'w').write(s)"`
追加 Markdown 决策记录时，字符串里的反引号（Markdown 行内代码）会被 **bash 先做命令替换**：
`data/ep05_data.json` 被当成命令执行（报 syntax error），路径在落盘内容里变成空串或报错文本。
Python 本身没报错、追加"成功"，损坏是静默的——tail 检查才发现路径丢了。

## Why

双引号包裹的 `python -c` 参数仍经过 shell 展开：反引号/$()/变量在传给 Python 之前就被替换。
三引号 Python 字符串挡不住 shell 这一层。

## How to apply

- 含反引号/`$`/Markdown 的文件内容落盘或追加：**用 Write/Edit 工具**，不经 shell。
- 必须用 shell 时：quoted heredoc（`python -I - <<'EOF' ... EOF`）或先把内容写临时文件再读。
- 追加后立刻 tail 验证关键 token（路径/数字）还在，别信"写入成功"。
