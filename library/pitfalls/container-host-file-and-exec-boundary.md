---
name: container-host-file-and-exec-boundary
description: 容器内 /tmp 不等于宿主 /tmp 需 docker cp 取回；容器 stop 后 exec 直接失败，改容器 SQLite 应停容器后操作 bind-mount 路径
type: pitfall
source: apishow（2026-10-05 删 astrbot cron_jobs 一行）
date: 2026-10-05
verified: 2026-10-05
topic: container
---

**经验**：两条容器/宿主边界，实测删 astrbot 一行 `cron_jobs` 时撞全：

1. **容器内 `/tmp` 是容器自己的文件系统**。`docker exec ctr python3 - <<'PY'` 写 `/tmp/_x.json` 之后，宿主侧 `mv /tmp/_x.json ...` 报 `cannot stat`。取回用 `docker cp ctr:/tmp/_x.json <宿主路径>`，再 `docker exec ctr rm -f /tmp/_x.json` 清容器侧。
2. **`docker stop` 之后 `docker exec` 直接失败**（`Error: ... is not running`）。要改容器的 SQLite 就停容器，在**宿主侧对 bind-mount 路径**操作（`/opt/astrbot/data/data_v4.db`），改完再起容器。

配套校验：`PRAGMA integrity_check` 返回 `ok`、行数 23→22、`docker ps` 确认容器恢复运行。

**Why:** 容器有独立命名空间与挂载视图，`/tmp` 不在 bind-mount 内所以两侧互不可见；exec 依赖一个已运行的任务句柄。两条都表现为「命令跑了但没生效」，极易误判成「数据不存在 / 代码没跑」——后者曾让我白烧一轮去查查询条件。

**How to apply:** 需要跨边界的临时产物一律走 `docker cp`，或直接写进 bind-mount 目录，别指望 `/tmp` 相通；改容器内 DB 或配置的前置是「容器处于 stopped」，操作对象换成 bind-mount 的宿主路径，然后重启容器。凡 `exec` 失败先看容器是不是 running，别先怀疑代码。

相关：[[container-heredoc-needs-stdin-flag]]（stdin 转发）、[[bind-mount-owner-must-match-container-uid]]（bind mount 属主）。
