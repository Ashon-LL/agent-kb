---
name: container-image-source-patches-need-replay-script
description: 打进容器镜像内的源码补丁扛 docker restart、不扛 rm/镜像升级；必须配一个幂等重放脚本（锚点唯一性断言 + 语法预检 + 已打则跳过），镜像升级后第一件事重跑，别指望它自己还在
type: pitfall
source: APIShow/AstrBot v4.27.4（2026-09-18 三个源码补丁：token 计数 / 压缩闸门 / 历史图片剥离）
date: 2026-09-18
verified: 2026-09-18
topic: container, ci, security, methodology
---

**经验**：容器里"改源码"有四种持久性，选错一种等于没改——

| 改法 | 扛 restart | 扛 rm / 重建 / 镜像升级 |
|---|---|---|
| `docker cp` / `docker exec` 改文件 | ✅（写层还在） | ❌ 全丢 |
| `docker commit` 成新镜像 | ✅ | ⚠️ 视编排而定，易被 `pull` 覆盖 |
| 宿主 bind mount 的**数据**目录 | ✅ | ✅ |
| 改**镜像内**的应用代码（pip 安装位置、`/app`） | ✅ | ❌ 全丢 |

**Why**：这类补丁改的是应用自己安装目录里的源码，上游一发新镜像、或有人 `docker rm` 重建，补丁就**无声消失**——应用照常启动、日志照常干净，你只在几天后遇到"那个 bug 又回来了"，而这时已经很难想起曾经打过补丁。本次三个补丁（图片持久化、历史图片不重发、压缩闸门取值）全属这一类。

**How to apply**：

1. 打镜像内补丁的同时，**当场写一个重放脚本**并纳入版本库（如 `scripts/ops/<app>_reapply_patch.py`）。补丁代码留在脚本里，而不是只留在容器里。
2. 重放脚本必须满足四条：①**幂等**——检测到补丁标记就跳过，重复跑无副作用；②**锚点唯一性断言**——`content.count(anchor) == 1`，不等于就报错退出（上游改一行就静默错位）；③**改完 `py_compile` 预检**——语法错要在写盘前拦住；④**备份原文件**——`<file>.bak-<日期>-<标签>`，每个文件独立标签。
   - ⚠️ **锚点静默不匹配的第一嫌疑是「空白行/缩进差异」，不是「你抄错了」**（2026-09-20 实测）：手写替换串时漏掉原文里 `written += 1` 与 `logger.info(...)` 之间的**一个空行**，`count()` 直接返回 0；屏幕上看两段文本几乎一样。**对策：先把原文片段原样导出成独立文件（不要在 shell 输出里看，会被截断/转义），用 `cat -A` 逐字节比对，再写替换串。** Windows/Git Bash 下还要先排除 heredoc 吃反斜杠（见 [[windows-scripting-terminal-gotchas]]）。
3. 结构用"绝对路径 + 各自备份标签"的元组表遍历，一条命令全量重放，别写成一串手工步骤。
4. **镜像升级后的第一件事就是重跑它**，并核对每个补丁都回报 `[skip] 已打过` / `无需改动`。
5. 把"重跑补丁脚本"写进项目的镜像升级清单，否则下一个升级的人不会知道有补丁存在。

**相邻**：改第三方应用**数据**（DB 列 / 配置文件）的同类边界见 [[third-party-db-columns-typed-by-reading-code]]；容器里喂 stdin 见 [[container-heredoc-needs-stdin-flag]]。
