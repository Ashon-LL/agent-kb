---
name: regex-cannot-span-nested-braces
description: 用 `[^}]*` 这类字符类跨嵌套花括号会改坏结构（多出孤立 false、语法错）；批量改嵌套结构必须按行号/解析树定位并逐行替换，改完跑 py_compile / npm run build 复验；同轮 heredoc 里的反引号会被 shell 吃掉，commit message 含反引号/反斜杠要写进文件用 -F
type: pitfall
source: MH-Agent-Open（2026-10-05 一天内用「看起来能过」的手法改坏两次代码）
date: 2026-10-23
verified: 2026-10-05
topic: methodology, python
---

**教训**：正则的字符类不理解嵌套结构；`[^}]*` 会跨过任意层花括号，改出来的代码「看起来对、编译就炸」。

## 事故一：正则跨嵌套花括号

用 `(\w+): \{[^}]*?\}, editor_ai:` 批量删状态表键，`[^}]*?` 跨过嵌套层，结果：

```js
loadingModels: { executor: false, reviewer: false, false, gpt_image: false }
```

多出一个孤立 `false` ⇒ 前端构建直接语法错。

**正解**：按行号定位 + 逐行替换；改完必须 `py_compile` / `npm run build` 复验。
结构复杂时先解析（AST/JSON），不要用正则硬套。

## 事故二：heredoc 里的反引号被 shell 吃掉

`git commit -F - <<'MSG'` 的 message 里写了 `vision_*`、`HAS_VISION` 等反引号内容，
shell 执行后**提交信息里 5 处变成空白**（代码改动本身完整，只是信息残缺）。
改用 `-F <文件>` + amend 修复。

**正解**：commit message 含反引号/反斜杠/`$` 时，一律写进文件用 `-F`，不要走 heredoc 管道。

## How to apply

- 批量改代码前先判断「有没有嵌套」；有就按行/结构改，别用跨层字符类。
- 每次批量替换后立刻跑最小构建/编译；「看起来过」不算数。
- 写提交信息/脚本时，含特殊字符一律落文件再传。

关联 [[escaping-through-patch-pipelines-needs-positive-control]]、
[[guard-criteria-anchored-to-spelling-always-escape]]、[[temp-files-must-not-be-added-by-add-all]]。
