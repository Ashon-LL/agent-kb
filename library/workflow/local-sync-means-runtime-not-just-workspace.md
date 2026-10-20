---
name: local-sync-means-runtime-not-just-workspace
description: 用户说「本地同步到最新」= 打开软件看到最新（运行时同步：镜像重建/容器重启/安装区），⛔ 不只是 git pull 开发区；漏做运行时会让他误判"什么都没做"并发出错误指示
type: workflow
source: 用户 2026-10-19 纠正（MH-Agent-Open 本地同步）
date: 2026-10-20
verified: 2026-10-19
topic: delivery, container
---

用户 2026-10-19 纠正：「记住：我说本地同步到最新 就是希望我打开软件时是看到修复/完善/改进后的，不是只更新开发区！！！不然我会以为什么都没做！导致发给你/npc错误的指示」。

**Why**：用户的验收面是**产品运行态**（他打开 `http://127.0.0.1:18088` 看到的软件），不是 git 日志。只 `git pull` 更新仓库 = 他打开软件看到旧代码 ⇒ 误判"这几小时白干了" ⇒ 基于错误判断给 AI/NPC 发指令（如重复派单、质疑进度）——这是比"漏同步"更贵的二次伤害。

**How to apply**：听到「本地同步到最新 / 更新到最新 / 把本地弄最新」时，按运行形态做全套：
1. **先认运行形态**：本机 = Docker 容器（`mh-agent` + 卷 `mh-data`，端口 127.0.0.1:18088；安装区 `C:\Software\MH-Agent-Open` 不存在 = 桌面形态已不在用）；
2. **代码层**：git pull 两远端（origin/bx）并核对 SHA；
3. **运行层**（关键）：容器落后时代码必须**重建镜像**（`docker build -t mh-agent-open:0.9.11 -f Dockerfile .`）→ 重启容器 → **实测 `curl /api/health` 的 version** 证明"打开就是最新"；
4. **报告口径**：必须给出「镜像构建时间 + 容器重启时间 + health 实测 version」三件套，⛔ 不许只说"代码已同步"。

（WSL 内 build 的标准做法见 docker 构建相关条目。）

关联 [[same-config-key-different-semantics-per-step-type]]、[[user-given-equalities-must-stay-equal]]。
