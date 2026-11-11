---
name: backup-prune-must-sort-by-mtime
description: 清理「只留最近 N 份」备份时按文件名字母序排序会删错版本；必须按 mtime/时间排序，且先确认待删清单再执行
type: pitfall
source: APIShow 2026-11-07 WorkBuddy 面板二进制备份误删（pre-wb-fix5 / pre-wb-upgrade 被删）
date: 2026-11-07
verified: 2026-11-07
topic: change-discipline
---

**经验**：做「保留最近 N 份」的备份清理时，**不能**用 `ls -d <前缀>* | head -n -N | xargs rm -rf` 这种按**文件名字母序**的写法——目录名里的日期不一定和字母序同向（`pre-wb-upgrade-20261102` 排在 `pre-wb-video-*` 前面，但时间更旧；`pre-wb-fix5-20261107` 反而是较新的那个）。结果一次误删了 3 个目录，其中两个是更早的二进制备份。

正确做法：
1. **按 mtime 排序**：`ls -dt <前缀>* | tail -n +N+1`（`-t` 按修改时间倒序），或 `find <dir> -maxdepth 1 -name '<前缀>*' -printf '%T@ %p\n' | sort -rn`；
2. **先打印待删清单**（`echo` 出来肉眼确认），再执行删除；
3. 新建的备份目录**不要放进同一条命令里一起 prune**——先备份、再单独清理，否则可能把刚建的备份删掉（本次就发生了）。

**Why**：2026-11-07 给 WB 面板部署 MCP schema 修复前做备份，命令写成 `ls -d /opt/apishow/backups/pre-wb-* | sort | head -n -2 | xargs -r rm -rf`。字母序下 `pre-wb-fix5-20261107` / `pre-wb-mcp-negprompt-20261107` / `pre-wb-upgrade-20261102` 落在「后 2 个」之外，被整批删除，连带刚 `mkdir` 的备份目录。回滚所需的那一版（2026.11.7.1000）靠立刻重建才保住；更早的 2026.11.5.1120 备份丢失（站主确认不需要）。

**How to apply**：任何「留 N 份」的清理动作，先按时间排序、先列清单、后删除；备份与清理拆成两条命令。关联 [[newapi-disable-must-sync-abilities]]（同类「一条命令里做太多事」的坑）。
