---
name: wsl-docker-on-demand-startup
description: Windows 宿主机不装 Docker Desktop、容器基建放 WSL Kali 的配置要点——Windows 侧无 docker 命令须 wsl.exe 转发；user 组是"装好却跑不了"的典型坑；关自启后按需启必须走 -u root（Kali sudo 有密码那条路不通）；含 2026-10-12 docker build 长跑踩坑四连（systemctl 启 daemon / VM 中途重启清场 / 基础镜像先 pull / 构建进度可见性）
type: tool
source: default 综合事务 2026-10-04（用户选 WSL 内装+关自启）；2026-10-12 镜像重建四连坑实测补充
date: 2026-10-04
verified: 2026-10-12
topic: windows, container
---

**经验**【作用域=本机形态：工具放 WSL Kali、宿主 Git Bash 调 wsl.exe】：

- **Windows 侧不发 `docker` 命令**。装 `docker` 于 WSL Kali（本机 28.5.2，buildx/compose 齐），Agent 在 Git Bash 里一律转发：`MSYS_NO_PATHCONV=1 wsl.exe -d kali-linux -u kali -- docker ...`。`MSYS_NO_PATHCONV=1` 必须带（否则 MSYS 把 `-v /c/...` 这类参数吞成 `C:\...`）。
- **按需启**（关自启）：`systemctl disable docker.service docker.socket` 后 WSL 重启不自动起 daemon。启动链路：`wsl.exe -d kali-linux -u root -- systemctl start docker`（约 3s 就绪），之后 `-u kali` 正常用。**探测即自愈**：docker 命令报 socket 权限错/连接错 = daemon 没起，先拉起再重试。
- ⚠️ **WSL 内 `sudo` 要密码、Orchestrator 没有口令** ⇒ 管理动作（usermod/systemctl）走 `wsl.exe -u root` 这个原生免密入口，别尝试 `sudo`。
- ⚠️ **"装好了但跑不了"的头号坑是用户不在 docker 组**：dpkg 看着装齐、systemd active，`docker info` 起头几行 Client 正常，一路到 Server 段才 permission denied —— 只看前几行会误判装好。修：`wsl.exe -u root -- usermod -aG docker kali`，然后**新开会话**验证（组变更不进已存在会话）。

**2026-10-12 实测补充（docker build 长跑四连坑，发版 0.9.11 实况）**：

- ⛔ **启 daemon 走 `systemctl start docker`，别手搓 `nohup dockerd &`**：手搓路径在 VM 中途重启后撞「containerd not running → containerd is still running → timeout waiting for containerd to start」死循环。systemd 路径由 systemd 管进程生命周期，无此问题。
- ⛔ **WSL VM 会自己重启**（空闲回收/系统事件；实测 daemon 正在跑构建时 VM 整体重启、进程全灭）。跑大活时失联的处置：`pkill -9 -f dockerd; pkill -9 -f containerd; rm -f /var/run/docker.pid; rm -rf /var/run/docker/containerd` 清场→重启；**daemon 与构建必须放同一个后台任务**（跨任务的 daemon 会被会话回收连带杀掉）。
- **基础镜像可能不在本地 store**（`docker system prune -a` 类清理后）：build 前先 `docker pull <base>`；daocloud 镜像源的 502 是**瞬时抖动**（健康判据 `curl -sI https://docker.m.daocloud.io/v2/` 返 401），隔一会儿重试即过，不要急着换源。
- **构建进度可见性**：`docker build … | tail -N` 会把输出缓冲到结束才吐（外层再套 `| tail` 双重缓冲更看不见）。要看实时进度：`ps -eo pid,comm | grep MainThread` 找到 buildkit 步骤进程，读 `/proc/<pid>/cmdline` 即知当前在跑哪步（如 `playwright install chromium`）。
- ⛔ **`docker build .` 直接在 `/mnt/c` 上跑会挂死（2026-10-14 实测，第五坑）**：build context 要先**遍历整棵仓库树**——
  `.dockerignore` 只决定最终带哪些文件，**不减少遍历**；`/mnt/c` 跨文件系统遍历 + 仓库含 `.git`/`node_modules` ⇒ 客户端卡在
  `futex_do_wait`、`/var/lib/docker/buildkit` 零增长、dockerd 无日志、无网络，**看起来像"构建卡死"，实为 context 扫描挂住**。
  **判据（三同现即判卡）**：`du -sm /var/lib/docker/buildkit` 两次采样不变 + `pgrep -af "[d]ocker build"` 有进程但无活动 +
  `journalctl -u docker --since "3 min ago"` 无输出。**解法**：最小 context 用 tar 流拷进 WSL 内部再构建——
  `tar -C /mnt/c/<仓库> -cf - --exclude='*node_modules*' --exclude='*__pycache__*' Dockerfile Dockerfile.npc .dockerignore backend frontend/dist | tar -C /root/mha-build -xf -`，
  然后 `cd /root/mha-build && docker build --progress=plain -t <tag> -f Dockerfile .`（`--progress=plain` 让输出**逐行**落日志；
  默认 TTY 进度条在重定向时几乎不可见。`Dockerfile.npc` 只需它自己 + 本地已有产品镜像，无需额外 context）。
- ⚠️ **别把 push 重试误读成 pull 失败（2026-10-14 同日）**：日志里 `d310d80567ba: Retrying in N seconds` 这类行在 **`docker push`**
  阶段同样出现（daemon 侧原文是 `Upload failed, retrying: received unexpected HTTP status: 502 Bad Gateway`——
  推 `docker.cnb.cool` 也会 502 抖动，docker 内建重试通常能过）。**判据**：`journalctl -u docker` 的原文（`Upload failed` = push；
  `failed to resolve`/`dial tcp` = pull）+ `pgrep -af "[d]ocker pull"` 是否有进程。⛔ 只看「Retrying」字样会把"正在推"误判成"拉不动"。
- 推库凭据：WSL root 的 `/root/.docker/config.json` 常驻 `docker.cnb.cool` 部署令牌凭据，直接 `docker push` 即可（无需每次 login）。

**Why**：Docker Desktop 形态（2~3G、后台常驻 1~2G）与"只给 Agent 开发用"的定位不匹配；WSL 内装零额外产品，但 Windows 侧天然没有 docker 二进制、systemd=关自启后无 daemon，两次转发给 Agent 造成"明明装了却调不动"的假故障；长构建期 daemon 生命周期脆弱（VM 回收）叠加手搓启动 = 连环误诊。

**How to apply**：Agent 需要容器时按上面前缀命令；daemon 不在先 `-u root` 拉起；报错先分清"没起 daemon / socket 权限（组）/ 真命令错误"三种再动手。**跑 docker build 等长任务前先读本条目**——2026-10-12 四连坑里有两条（MSYS 转换、-u root）本条目早已写明，当时没读才是根因。相关：[[windows-scripting-terminal-gotchas]]、[[container-heredoc-needs-stdin-flag]]、[[bind-mount-owner-must-match-container-uid]]。

关联 [[container-host-file-and-exec-boundary]]、[[docker-compose-config-expands-secrets]]、[[host-gateway-port-allowlist-before-relay-onboarding]]。
