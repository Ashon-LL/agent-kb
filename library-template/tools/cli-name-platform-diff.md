---
name: cli-name-platform-diff
description: npm 装的 CLI 在 Windows 上有 .cmd 扩展名，Python subprocess 直接 run 工具名会 ENOENT
type: tool
source: 从 Python spawn CNB CLI 调起失败
date: 2026-09-20
---

**经验**：npm 全局装一个 CLI，Windows 上会产出三件套（无扩展名 sh 脚本 / `.cmd` / `.ps1`）。Git Bash 里直接敲名字能跑，但 Python `subprocess.run(["cnb", ...])` 会报 `FileNotFoundError`——CreateProcess 不执行无扩展名脚本。

**Why**：Windows 的 CreateProcess 会先找 `xxx.exe`、`xxx.cmd`、`xxx.bat`，但 Python subprocess 默认只找 PATH 里的无扩展名版本。

**How to apply**：用 `shutil.which("x.cmd") or shutil.which("x")` 拿到真实路径再传给 subprocess。
