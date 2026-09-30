---
name: file-change-not-code-running
description: 后端代码文件更新≠在跑：重启后必须核对进程 CreationDate 晚于文件 mtime，防假重启
type: pitfall
source: mh-agent-open（2026-09-07 假重启事故）
date: 2026-09-14
---

**经验**：改后端核心模块后必须重启进程，且验证"新代码真在跑"：

- 核对**进程 CreationDate 晚于被改文件 mtime**：`Get-CimInstance Win32_Process` 按 CommandLine 找进程；`/api/health` 只证明有进程在听，证明不了代码版本。
- 最快佐证：看日志里是否出现**新版独有的错误文案/分支行为**。
- 假重启两形态：①kill 后旧进程未死、新实例 bind 报 10048 退出，旧内存代码继续服务——要轮询到**端口彻底释放**再启动；②Git Bash `start //B` 起的子进程可能即退，用 `subprocess.Popen(CREATE_NEW_PROCESS_GROUP|DETACHED_PROCESS)` 或 pythonw 之外的可靠方式。
- pytest 绿不能替代进程验证（测试直接 import，不经进程）。
- 反例边界：**数据值**变更若每请求实时读库则不需重启，只有代码模块要。
