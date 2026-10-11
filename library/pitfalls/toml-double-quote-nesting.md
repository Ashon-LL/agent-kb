---
name: toml-double-quote-nesting
description: TOML 双引号字符串内嵌未转义的双引号会提前闭合，tomllib 报 Expected newline or end of document 且行号指向语句起点
type: pitfall
source: apishow（2026-10-05 credentials.toml 新增 [astrbot.dashboard] 段）
date: 2026-10-05
verified: 2026-10-05
topic: python
---

**经验**：TOML 双引号字符串里内嵌双引号，必须转义或直接改写措辞：

```toml
# 坏：内层双引号提前闭合，后面的内容变成语法外 token
jwt_note = "换得，scopes=["*"] 含 system"

# 好：改写措辞
jwt_note = "换得，scopes 为全量星号（含 system）"
```

实测报错：`tomllib.TOMLDecodeError: Expected newline or end of document after a statement (at line 456, column 49)`。行号 456 是**语句起始行**而非出错位置，容易让人在整条语句里满世界找问题。

**Why:** TOML 是强规范格式，双引号内层双引号就是提前闭合字符串，剩余部分成为解析器无法归位的语法外内容。解析器按「整条语句失败」定位，所以报的是语句起点——报错离真实病灶有一段距离。

**How to apply:** 描述性文字含双引号时，优先改写措辞（自然语言转述，如 scopes=["*"] 写成「scopes 为全量星号」）；其次用单引号字面串 `'...'`（注意单引号串不处理转义，内部也不能有单引号）。改完立刻 `python -c "import tomllib,pathlib;tomllib.loads(pathlib.Path('x.toml').read_text(encoding='utf-8'))"` 当场验，别攒到最后。

同类引号归属问题：[[powershell-herestring-grammar-and-runtime-divergence]]、[[powershell-start-process-argumentlist-strips-quotes]]、[[windows-scripting-terminal-gotchas]]。

关联 [[fail-open-except-swallows-caller-type-errors]]、[[ssh-heredoc-delimiter-must-be-quoted]]。
