---
name: av-quarantine-removes-project-files
description: 项目文件"自己消失"先查杀软隔离区，不要先怀疑自己或工具——火绒隔离库是 SQLite 文件 QuarantineEx.db 表 FilesV3_60（含原路径/SHA1/判定名），Defender 用 Get-MpThreatDetection，回收站兜底；扫描器与反连测试用例最易被启发式命中
type: pitfall
source: SRC 项目（2026-11-07 tracking/ 下 3 个外来 Python 被火绒静默隔离）
date: 2026-11-07
verified: 2026-11-07
topic: windows, diagnosis
---

**经验**：目录里的文件在会话中途"自己没了"，第一个要查的是**杀软隔离区**，不是自己的命令、不是编辑器、也不是 git。判定顺序：Defender 检测历史 → 回收站 → 火绒隔离库（SQLite 可直接读）→ 全盘同名搜索。查到隔离记录后，原路径、SHA1、判定名都在，能直接说明"是谁搬走的、为什么"。

**Why**：2026-11-07 实测，项目 `tracking/` 下 3 个 Python 文件在两个命令之间蒸发（231KB，此前刚 `head` 读过、确认存在）。第一反应是"我哪条命令删的"，逐条回看 `rm`/`rmdir` 全是无关路径 —— 实际是火绒实时防护在 11:51 一次性隔离，我这边 0 条删除命令。如果只盯着自己的脚本，会一直找不到并最终误判成"文件系统坏了"或"另一个 agent 删的"。

三个可直接照抄的证据源：

```
# 1) 火绒：隔离库是 SQLite，直接读（先 cp 一份避开 WAL 锁）
#    Windows 路径下读，Git Bash 的 /tmp 给 Windows Python 是看不见的
python -c "import sqlite3;c=sqlite3.connect(r'<copy>\QuarantineEx.db');\
print(list(c.execute('select id,fn,sha1,vn,ts from FilesV3_60 order by id desc limit 10')))"
# 字段：fn=原路径 vn=判定名 ts=unix 时间；隔离体在 Quarantine/<SHA1>，前缀 16 字节文件头后是加密流（别想手工还原）

# 2) Defender
powershell -NoProfile -Command "Get-MpThreatDetection | Sort-Object InitialDetectionTime -Descending | Select -First 10"

# 3) 回收站（杀软隔离不进回收站，但只要不是隔离就还有救）
powershell -NoProfile -Command "\$sh=New-Object -ComObject Shell.Application; \$sh.Namespace(10).Items() | Select Name,Path"
```

本次判定名：`HEUR:Trojan/Python.ReverseShell.f`、`HEUR:Trojan/Python.ShellLoader.y` —— 命中的是**含反连 payload 的安全工具与其测试用例**（skill 扫描器 + pytest 用例），典型启发式误报形态，但**未复核前不要假设是误报**：这类"看起来就像恶意样本"的代码，默认保持隔离、从 GUI 恢复到独立目录再审，别直接放回业务目录。

**How to apply**：① 文件消失 → 立刻按上面三源取证，不要先自我归因；② **扫描器 / 探测脚本 / 反连测试用例 / 免杀样本**这类项目，把"杀软会吃掉工具和产物"当常态写成风险项，长跑前先确认 `tools/` 与输出目录没被隔离；③ 隔离是可逆的（火绒 GUI 隔离区可恢复原路径），但恢复前先想清楚要不要恢复、恢复到哪里；④ 别把"我以为删了/我以为没删"写进结论——用隔离库时间戳 + 原路径说话；⑤ 跨工具读 SQLite 时路径必须用真实 Windows 形态（`r'C:\Users\...'`），Git Bash 的 `/tmp` 传给 Windows Python 会 FileNotFoundError，见 [[windows-scripting-terminal-gotchas]]。

关联 [[windows-home-cleanup-safe-vs-traps]]、[[automation-artifacts-lie-existence-and-freshness]]。
