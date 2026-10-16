---
name: windows-unquoted-path-redirect-accidents
description: Windows 含空格路径不加引号 → 重定向/参数在空格处被截断，产物是 C:\Program 这类 C 盘根目录怪文件（"文件名警告"弹窗的盯防对象）；三步排查=读怪文件内容→创建时间/属主→当刻 Prefetch 与应用日志对账
type: pitfall
source: default 会话 2026-10-16（本机 C:\Program 64 字节便签，溯源到 ZCode 补丁部署的一次临时命令）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：C 盘根目录出现名不对题的怪文件（`C:\Program`、`C:\Program1` 等）——先怀疑"含空格路径没加引号"。`echo 备份原文件 - > C:\Program Files\X\y` 这类命令中，`C:\Program` 会被当成重定向目标、`Files\...` 掉进正文（Git Bash 与 cmd 都在空格处切词，先生成的就是根目录截断文件）。它不只是垃圾：旧式不带引号的 `C:\Program Files\...` 调用会先撞上它，所以经常有软件弹"文件名警告"劝你改名/删除。

**三步排查**：① 读怪文件内容（`[IO.File]::ReadAllBytes` 后按 UTF8/UTF16 解码），内容往往直接指向所属项目（本机=部署便签，写明备份路径）；② 看创建时间与属主（属主是 Administrators=提权进程写的根目录）；③ 用创建时间对账当刻痕迹——`C:\Windows\Prefetch\*.pf` 的 mtime、应用日志、会话 rollout；**中文在日志里可能是原文 UTF-8 也可能是 `\uXXXX` 转义，两种形态都要搜**。找不到那条命令也别卡住：确认项目自带的 .bat/.cmd 引号规范清白后，即可定性为"某次临时 shell 命令"。

**Why**：怪文件容易被当病毒或被乱删；而"文件名警告"弹窗的来源软件常常查不到文案指纹（加壳/压缩的二进制扫不到字符串），越查越悬。正确次序=**先处置文件、弹窗自然消失，再谈溯源**。

**How to apply**：见到 C:\Program* 类残留按三步走；处置=内容核对无误后直接删除（比弹窗建议的改名更干净）；写含空格的 Windows 路径命令一律加引号。
