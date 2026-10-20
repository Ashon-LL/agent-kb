---
name: cross-env-file-handoff-must-use-native-mechanism
description: 跨 Git Bash 与 Windows Python 传文件/凭据时，/tmp 两边不通且会造出明文凭据副本；应直接用项目现成加载器（load_secrets/tomllib），别手写解析、别落临时明文文件
type: pitfall
topic: windows
source: APIShow 邮箱整理任务（2026-10-19 用户当场指出「有经验库有记忆了仍然犯错」）
date: 2026-10-19
verified: 2026-10-19
---

**症状**：把服务器上取的授权码先 `ssh ... > /tmp/creds.txt` 落地，再让 Windows 侧 Python 读 `/tmp/creds.txt`
⇒ `FileNotFoundError`。看起来是「路径写法错了」，重试一次就好。

**真因是两个错叠在一起**，只修路径会漏掉更严重的那个：

1. **`/tmp` 在 Git Bash 与 Windows Python 之间不是同一个目录**。Git Bash 的 `/tmp` 映射到
   `C:\Users\<user>\AppData\Local\Temp` 的**某个子路径**（MSYS 挂载），而 Windows 原生 Python 看到的
   `/tmp/creds.txt` 是**当前盘根下的 `\tmp\`**。两边写读同一字符串，落点不同。
   同类坑：`/c/...` 路径在 bash 里合法、在 Python 里不合法；`cmdkey`/`reg` 的路径格式又不一样。
2. **为了「传递」一个秘密，我在盘上造出了第二份明文副本**。项目铁律是真值只进
   `.local_secrets/`，我却让它以临时文件形态存在过——即使随后删掉，也已经违反最小暴露原则。

**正确做法（按优先级）**：

- **跨环境传值，优先根本不落盘**：让**目标侧**自己取。例：凭据最终要进本地
  `credentials.toml`，就写一小段 Python，在**同一个 Python 进程里**读服务器 SQLite / 调
  `get_secret`，然后直接写目标文件；不要 bash 管道过手。
- **必须过文件时，用目标侧的原生临时目录**（`tempfile.gettempdir()` / `$TMPDIR` 由 Python 自己取），
  并在同一段代码里 `try/finally: os.unlink()`；别手写 `/tmp` 或 `AppData/Local/Temp`。
- **凭据解析一律用项目现成加载器**（`scripts/load_secrets.py` → `tomllib`/`tomli`），
  不要手写「逐行 split('=')」的迷你 TOML 解析器：注释行、引号内 `=`、数组、多行值都会让它静默解析错。
- **写完立刻自证**：不要用「文件字节数看着对」当验证（本次就是靠 `wc -c` 才发现少了一行，
  属于运气）。要断言**键存在 + 值非空 + 类型正确**，最好由实际使用方（登录一次）来验。

**反模式信号**（出现即停）：
- 我为了拿一个值，开始写「解析 / 中转 / 落盘」三段式胶水代码；
- 项目里已有 `load_secrets`/`get_secret` 这类加载器，我却在写自己的版本；
- 我在命令里 `echo` 或 `cat` 一个可能是凭据的文件（即使只是想确认写对了）。

**关联**：[[no-assertion-without-measurement]]（别靠运气发现静默失败）、
[[fail-open-except-swallows-caller-type-errors]]（自写解析器的错会被宽 except 吞掉）。
