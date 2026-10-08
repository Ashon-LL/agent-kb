---
name: wsl-docker-on-demand-startup
description: Windows 宿主机不装 Docker Desktop、容器基建放 WSL Kali 的配置要点——Windows 侧无 docker 命令须 wsl.exe 转发；user 组是"装好却跑不了"的典型坑；关自启后按需启必须走 -u root（Kali sudo 有密码那条路不通）
type: tool
source: default 综合事务 2026-10-04（用户选 WSL 内装+关自启）
date: 2026-10-04
verified: 2026-10-04
topic: windows, container
---

**经验**【作用域=本机形态：工具放 WSL Kali、宿主 Git Bash 调 wsl.exe】：

- **Windows 侧不发 `docker` 命令**。装 `docker` 于 WSL Kali（本机 28.5.2，buildx/compose 齐），Agent 在 Git Bash 里一律转发：`MSYS_NO_PATHCONV=1 wsl.exe -d kali-linux -u kali -- docker ...`。`MSYS_NO_PATHCONV=1` 必须带（否则 MSYS 把 `-v /c/...` 这类参数吞成 `C:\...`）。
- **按需启**（关自启）：`systemctl disable docker.service docker.socket` 后 WSL 重启不自动起 daemon。启动链路：`wsl.exe -d kali-linux -u root -- systemctl start docker`（约 3s 就绪），之后 `-u kali` 正常用。**探测即自愈**：docker 命令报 socket 权限错/连接错 = daemon 没起，先拉起再重试。
- ⚠️ **WSL 内 `sudo` 要密码、Orchestrator 没有口令** ⇒ 管理动作（usermod/systemctl）走 `wsl.exe -u root` 这个原生免密入口，别尝试 `sudo`。
- ⚠️ **"装好了但跑不了"的头号坑是用户不在 docker 组**：dpkg 看着装齐、systemd active，`docker info` 起头几行 Client 正常，一路到 Server 段才 permission denied —— 只看前几行会误判装好。修：`wsl.exe -u root -- usermod -aG docker kali`，然后**新开会话**验证（组变更不进已存在会话）。

**Why**：Docker Desktop 形态（2~3G、后台常驻 1~2G）与"只给 Agent 开发用"的定位不匹配；WSL 内装零额外产品，但 Windows 侧天然没有 docker 二进制、systemd=关自启后无 daemon，两次转发给 Agent 造成"明明装了却调不动"的假故障。

**How to apply**：Agent 需要容器时按上面前缀命令；daemon 不在先 `-u root` 拉起；报错先分清"没起 daemon / socket 权限（组）/ 真命令错误"三种再动手。相关：[[windows-scripting-terminal-gotchas]]、[[container-heredoc-needs-stdin-flag]]、[[bind-mount-owner-must-match-container-uid]]。
