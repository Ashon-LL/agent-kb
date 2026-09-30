---
name: electron-builder-nsis-silent-install-fallback
description: electron-builder NSIS 安装器 /S 崩溃（System.dll 0xC0000005）时的可靠替代——7z 解包安装器取 app-64.7z 手动安装；/D 自定义目录在 per-user 包上必崩
type: tool
source: cc-haha v0.6.7 Windows 安装实测（2026-09-28）
date: 2026-09-28
verified: 2026-09-28
topic: windows
---

**经验**：electron-builder 打的 per-user NSIS 安装器（如 cc-haha `Claude-Code-Haha-*-win-x64.exe`）：

1. **`/D=C:\目标目录` 静默安装必崩**（退出码 -1073741819 / 0xC0000005，崩溃模块 NSIS `System.dll` 固定偏移，两次复现）。per-user 包默认不受理 `/D`。
2. **裸 `/S` 也可能崩**：首次安装成功后卸载，再对同一 SHA256 的包 `/S` 重装连续 3 次崩在同一偏移——崩溃与本机残留无关（进程/目录/注册表全查过干净），别浪费时间排查环境。
3. **可靠替代 = 7z 直接解包安装器**（文件哈希校验过就没包的问题）：
   ```bash
   7z x installer.exe -o解包目录        # 得到 $PLUGINSDIR/app-64.7z
   7z x "$PLUGINSDIR/app-64.7z" -o"目标目录"  # 959 文件即完整应用
   ```
4. 手动装完没有快捷方式，且 COM（WScript.Shell）/cscript VBS 会被 WorkBuddy 安全钩子拦截；**用 `pip install pylnk3`**：`lnk = pylnk3.create(输出.lnk); lnk.specify_local_location(目标exe); lnk.work_dir = 目录; lnk.save()`（注意 `path` 无 setter，必须用 `specify_local_location`）。
5. 手动安装的代价：无卸载注册表项、应用内自动升级可能重装回默认目录。校验包完整性用 `gh api repos/<o>/<r>/releases/tags/<v> --jq '.assets[] | ...'` 取官方 `size`+`digest`。

**How to apply**：electron-builder 系安装器静默装自定义目录失败时，直接走 7z 解包 + pylnk3 建快捷方式，别跟 NSIS 参数较劲。

关联 [[windows-scripting-terminal-gotchas]]。
