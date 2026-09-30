---
name: automation-artifacts-lie-existence-and-freshness
description: 文档写了"每日自动备份"不等于它在跑：既要查任务对象是否存在，也要查产物时间戳是否新鲜
type: pitfall
source: APIShow（2026-09-15 备份清理时发现本地 DB 拉取停摆 3 周）
date: 2026-09-15
---

**经验**：验收任何"自动运行的东西"（Windows 计划任务 / systemd timer / cron）必须做**两层独立检查**，缺一层就会假绿：

1. **对象存在性**：文档、脚本、AGENTS.md 里写了这个自动化，不代表任务还在。
   `schtasks /query /tn "名称"`、`systemctl list-timers`、`crontab -l` 实测；Git Bash 下调 schtasks 必须 `MSYS_NO_PATHCONV=1`（否则 `/query` 被当路径转换）。
2. **产物新鲜度**：产物文件存在 ≠ 还在更新。看**最新产物的 mtime 距今多久**，与声明周期比对。
   本例：本地保 2 份，最后两份是 23 天前的 → 早已停摆；而"份数合规"这个指标看起来完全正常。

**踩到的具体坑**：
- 计划任务被（不明原因）删除后**不会有任何告警**，日志停在最后一次运行。要判断停摆时刻，看日志尾部时间戳，别只看任务名对不对。
- 清理"过多的备份"这类任务，顺带做一轮自动化健康检查成本极低、收益极高——**备份的备份停摆是静默故障**。
- 脚本里的远端枚举若用 `ls -1t <dir> | head -1`，会把目录/其他文件当最新产物选中；必须按产物模式过滤（`ls -1t data_*.tar.gz | head -n 1`）。
- 修复后**必须当场实跑一次**（`schtasks /run` + 轮询产物落地与日志新行）才算闭环，"任务已创建成功"字样不是证据。
- 中文 Windows 的 schtasks 输出是 GBK，`Last Run Time` 等字段名 grep 不到；判定成败优先看脚本自己的日志文件，别解析系统输出。

**边界**：SSH 别名/凭据变更也会静默打断计划任务（任务内脚本用 `-i pem` 直连时，加固后密码登录关闭、或换 key 路径即失败）——迁移到 SSH config 别名是更稳的形态。
