---
name: powershell-herestring-grammar-and-runtime-divergence
description: PowerShell here-string 定界符的真实语法（开/闭两侧不对称、行尾空白合法、换行符无关）、bash heredoc 在 PS 里是文件重定向不是未知语法、5.1 与 7.x 写文件字节级分岔、一条 stdin 只能喂一样东西、吞变量与真空变量输出不可区分
type: pitfall
source: ps-heredoc-todie + PowerShell-Reliability-Framework
date: 2026-09-21
verified: 2026-09-21
topic: powershell, container
---

**经验**：here-string / heredoc 出错几乎都**不报错**或报错文案指向错地方，人会在错误的方向上排查很久。以下全部在 pwsh 7.6.5（Core）与 Windows PowerShell 5.1.26100.8115（Desktop）**双运行时实测**，解析期结论两者完全一致。

## here-string 定界符的语法是不对称的

- **开头 `@'` / `@"` 后面允许尾随空白**：`@' ` 后跟空格 → **0 个解析错误**。
  ⛔ 网上普遍流传的「header 必须是该行最后一个字符」是错的。
- **开头后面不能有任何内容**：`@' # comment`、`@' ; $x=1` → 各 2 个错误，
  "No characters are allowed after a here-string header but before the end of line."
- **结尾 `'@` 前面只允许空白**：前加 1 个空格 / 4 个空格 / 一个 tab → 各 1 个错误，
  "White space is not allowed before the string terminator."
  ⇒ **缩进结尾定界符是解析错误，不是风格问题**，这是最常被踩的一条。
- ⛔ **结尾 `'@` 后面可以跟任何东西**：`'@ ` 尾随空格、`'@ | Set-Content`、
  `'@ + 'tail'`、`'@; x=1`、`'@ # note`、`$x = @'` → **全部 0 个错误**。
  ⇒ 别指望「结尾后面多写了东西」这种报错，它不报。
- 行内 `@''@` → 1 个错误；未闭合 `@'` → 1 个；孤立 `'@` → 1 个
  （报错文案是 "missing the terminator: '." —— **连 `@` 都不提**，极易误判）。
- **换行符完全无关**：CRLF / 混合 EOL / 闭合行是 CRLF → **全部 0 个错误**。
- 单引号字符串跨真实换行 → **0 个错误**（合法，结果里就是字面 LF）。

## `<<` 在 PowerShell 里是文件重定向，不是未知语法

- `cmd <<EOF`、`cmd <<'EOF'` → 3 个错误，**第一个是
  "Missing file specification after redirection operator."** ⇒ 它被当成文件输入重定向解析，
  **后面的命令根本没跑到**。
- `$x = <<EOF` → 1 个错误："The '<' operator is reserved for future use."
- ⛔ 所以「把 bash heredoc 粘进 pwsh」既不是"语法不被识别"也不是"能透传给子进程"，
  而是**静默地在 token 化阶段就断了**。报「语法错」会把你引向转义方向，全是死路。

## 5.1 与 7.x 的写文件默认行为分岔（字节级）

同一份 4 行 JSON here-string 载荷：

| 写法 | pwsh 7 | 5.1 |
|---|---|---|
| `Set-Content`（无 `-Encoding`） | 41 B，无 BOM | 41 B，无 BOM |
| `Out-File`（无 `-Encoding`） | 41 B UTF-8，无 BOM | **84 B，`FF FE` BOM，UTF-16LE** |
| `Set-Content -Encoding UTF8` | 41 B，无 BOM | **44 B，`EF BB BF` BOM** |
| `-Encoding Unicode` | 84 B UTF-16LE | 84 B UTF-16LE |
| `[IO.File]::WriteAllText` + `New-Object System.Text.UTF8Encoding($false)` | **39 B，无 BOM，cr=0 lf=3** | **39 B，无 BOM，cr=0 lf=3** |

⛔⛔ **`-Encoding UTF8` 不是跨运行时的修法**：在 5.1 上它**比默认多写 3 个 BOM 字节**，
症状是「加了官方推荐参数之后两台机器的校验和还是不一致」。
唯一在两边字节一致的是 `WriteAllText` + `UTF8Encoding($false)`。

另外：**每个 cmdlet 文件出口都会产生混合换行**（body 是 LF，cmdlet 自己再补 CRLF）——
实测全部 cr=1 / lf=4。表现为「功能测试全过，只有 checksum 或 diff 里多出一行」。

## 一条 stdin 只能喂一样东西

- heredoc 作为 `python -c` 的唯一 stdin → 30 字节；改成管道 → 30 字节；
- ⛔ **heredoc 同时送脚本和载荷（走同一条 stdin）→ 0 字节，且不报错**。
  空读取是**预期结果**，不是 shell 写错了，所以最容易把根因归成"typo"。
- 正确形态：其一落临时文件 / 命名管道；小载荷走位置参数；或拆成两阶段，
  前一阶段写产物、后一阶段读。

## 吞变量与真空变量，输出一模一样

- `pwsh -Command "$MSG"` 里 `$LASTEXITCODE` 被外层 bash 吃掉 → 空；
- 把 `\` 转义成 `\$` 在本例**同样是空**（因为没有原生命令跑过，它本来就未设置），
  两次 PID 不同（7264 / 10368）；
- ⛔⛔ 两种情况**打印结果完全一致，从输出上无法区分**。
  ⇒「多打几个反斜杠」这个常见建议在这个场景下**无效且不可自证**；
  必须加一条「状态缺失就显式失败」的守卫，不能让它以空值绿过。

## heredoc 生成 .ps1 再执行

- 用**引号定界符** `<<'PSEOF'` 写 `.ps1` 再 `-File` 调 → 3 个反斜杠完整；
- 用**无引号** `<<PSEOF` → `$path` / `$bs` / `$_` 全被展开成空，
  文件**照样写出来了（exit 0）**，然后子进程抛
  `ParserError: An expression was expected after '('.`，源码被搅成
  ` = 'C:\Users\MECHREVO\Downloads'` / ` = (.ToCharArray() | Where-Object {  -eq [char]92 }).Count`。
  ⇒ **exit 0 + 文件存在 ≠ 内容对**，必须回读或先 parse。

**How to apply**：写 PowerShell 前先查定界符是否缩进、载荷是不是脚本（是就把 heredoc 定界符加引号）；
任何"生成产物"的校验看**字节和 checksum**不看 exit code；5.1 上写文件一律走 `WriteAllText`。
相关：[[windows-scripting-terminal-gotchas]]（bash 双引号吞 `$_`、/tmp 三套文件系统、
引号 heredoc 也吃反斜杠）、[[powershell-tool-stdout-empty-write-files-instead]]
（PS 5.1 的 `Out-File -Encoding utf8` 实为 UTF-16LE）、[[container-heredoc-needs-stdin-flag]]、
[[env-claims-must-be-reverified]]。
