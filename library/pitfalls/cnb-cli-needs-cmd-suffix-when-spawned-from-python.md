---
name: cnb-cli-needs-cmd-suffix-when-spawned-from-python
description: 在 Windows 上用 Python subprocess 调 `cnb` 会报 FileNotFoundError——它不是 exe，只是无扩展名的 sh 包装脚本；必须用同目录的 `cnb.cmd`（或 .ps1）。附「同族 CLI 包装脚本」的通用识别法。
type: pitfall
source: MH-Agent-Open（后台监测脚本 watch_sn1.py 第一次运行就 FileNotFoundError）
date: 2026-09-18
verified: 2026-09-18
topic: windows, powershell, cnb, python
---

**经验**：`which cnb` 找到的路径**不代表 Python 能 spawn 它**。
npm 全局安装的 CLI 在 Windows 上通常是**三件套**：

```
<name>        ← 无扩展名，#!/bin/sh 包装（给 Git Bash / MSYS 用）
<name>.cmd    ← 给 cmd.exe / CreateProcess 用   ← Python spawn 要用这个
<name>.ps1    ← 给 PowerShell 用
```

**在 Git Bash 里敲 `cnb ...` 一切正常**（shell 认 sh 脚本），
**但 Python 的 `subprocess.run(["cnb", ...])` 会报**：

```
FileNotFoundError: [WinError 2] 系统找不到指定的文件。
```

因为 Windows 的 `CreateProcess` 只认可执行扩展名（`.exe`/`.cmd`/`.bat`），
**不会**去执行一个无扩展名的 sh 脚本。

## 事故经过

我写了个后台监测脚本，用 `subprocess.run(["cnb", "build", "get-build-status", ...])`。
第一轮干跑：**所有 cnb 调用都返回 `__ERR__ FileNotFoundError`**，
而函数内部把它当成「没输出」静默吞掉了 ——
解析器于是返回空字符串，看起来像「状态字段没解析到」，
**差点误判成「日志格式变了」**去改解析逻辑。

真因：`cnb` 是 sh 脚本；`ls` 同目录能看到 `cnb.cmd` 与 `cnb.ps1`。

## 正确写法

```python
CNB_DIR = os.path.expanduser("~/.workbuddy/binaries/node/cli-connector-packages")
CNB = os.path.join(CNB_DIR, "cnb.cmd")
if not os.path.isfile(CNB):
    CNB = "cnb"          # 非 Windows 或路径不同 → 退回 PATH 查找

subprocess.run([CNB, "build", "get-build-status", ...])
```

**更稳的通用写法**（不写死目录）：

```python
import shutil
CNB = shutil.which("cnb.cmd") or shutil.which("cnb") or "cnb"
```

## 同族教训：别把「子进程调用失败」当成「数据没解析出来」

本次真正的隐患不是路径，而是**错误被静默吞掉**：

```python
def run(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True)
        return r.stdout + r.stderr
    except Exception as e:
        return f"__ERR__ {type(e).__name__}: {e}"   # ✅ 必须带可识别的哨兵
```

⛔ 若写成 `except Exception: return ""`，下游**无法区分**
「命令失败」与「命令成功但无内容」，会把调用错误误诊为解析问题。
**哨兵前缀（`__ERR__` / `__TIMEOUT__`）让调用方必须显式判断。**

## How to apply

- **Windows 上用 Python 调任何 npm 装的 CLI**：先 `ls` 一下有没有 `.cmd`，
  有就用 `.cmd`（或 `shutil.which("x.cmd")`）。
- 判断一个路径是否可被 `CreateProcess` 执行：**看扩展名**，不看可执行位。
- 子进程包装函数**必须**用哨兵值区分失败形态，禁止 `return ""` 兜底。

相关：[[windows-scripting-terminal-gotchas]]、
[[log-text-is-not-spec-read-emitting-code]]（同源：别把表象当结论）。
