---
name: source-tree-and-commit-backup
description: 服务器源码工作树必须提交 git（未提交工作树在下次上游合并时极易丢失/冲突失控）；本地提交也要有远端备份（fork 无远端时用 bundle 兜底）
type: pitfall
source: APIShow docs/分析/20261105_审计_上游与补书面.md（2026-11-05 仓库与服务器实测）
date: 2026-11-10
verified: 2026-11-10
topic: git
---

**经验**：两条备份纪律——① **服务器上正在跑的源码树要提交进 git**（哪怕是本地 commit），
不能长期挂在未提交工作树；② 本地仓库的提交要有**远端备份**，fork 没有远端时用 `git bundle` 定期兜底。

**Why**：2026-11-05 审计实测：WB 服务器源码树 /opt/wb2api-panel-a 的 C2 视频全套 + 节流补丁
**全部未提交 git**（8 个修改 + ~20 个未跟踪文件，HEAD 还停在两周前）——下次上游合并时
这些本地补丁极易丢失或冲突失控；Trae 本地 HEAD 也无远端备份（fork 停在 10-05），只有 bundle 兜底。

**How to apply**：每次在服务器上改源码，改完就 git add -A && git commit（提交信息写清改了什么）；
对无远端的关键 fork，定期 git bundle create 到另一台机器/目录，并记录生成时间。

相关：[[diff-deployed-vs-vcs-before-reimplementing]]、[[post-release-housekeeping-mandatory]]
