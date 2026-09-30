---
name: bind-mount-owner-must-match-container-uid
description: bind mount 的文件属主由宿主机决定，容器内 chown 无效；给挂载文件设 chmod 600 而容器以非 root uid 运行 = 容器读不到、崩溃循环，且报错文案常指向别处（"permission denied" 只说文件不说 uid）
type: pitfall
source: APIShow 部署 workbuddy2api（2026-09-19）：config.json 设 600 + 容器 uid 10001 → 崩溃循环；管理端 data/ 同款
date: 2026-09-19
verified: 2026-09-19
topic: container
---

**经验**：`bind mount` 挂进去的文件/目录，**属主与权限完全由宿主机那一侧决定**——镜像里写的 `chown` 对它不起作用（镜像内的 chown 只作用于构建时 COPY 进去的文件）。所以「宿主机上按安全习惯 `chmod 600` + 容器以非 root uid 运行」这个组合，会直接让容器读不到自己的配置文件。

**典型症状**：容器起来就重启（`Restarting (1)`），日志一行：
```
load config: read config: open /app/config.json: permission denied
```
文案只说"权限不足"，**不说 uid 不匹配**——很容易误判成"路径配错了"或"挂载没生效"，去反复检查 `docker compose config` 的 volume 映射（那里看起来完全正确）。

**Why**：本次实测。部署 workbuddy2api 时按安全习惯把生成的 `config.json` 设成 `0600`（属主 root），而该镜像 `USER app`（uid 10001）——容器读不到，崩溃循环 6 次。修法只有 `chown 10001:10001`（或放宽到 644，但那样丢了保护）。同一类问题在该项目文档里叫「issue #108」，`auths/`、`data/` 卷全部同源：宿主机 `./login.sh` 以宿主 uid 落盘凭证（0600），容器以 10001 读 → `/status` 账号数为 0，也是同样的静默失败。

**How to apply**：

1. **凡是 bind mount 且容器非 root 运行的，先确认容器内 uid**：`docker inspect <ctr> --format '{{.Config.User}}'`，或读 Dockerfile 的 `USER`（常见 10001 / 1000 / app）。
2. **宿主机侧把挂载点 chown 成那个 uid**，而不是按"root 可读就行"的思路设权限：
   ```bash
   mkdir -p ./data ./auths
   chown -R 10001:10001 ./data ./auths
   chown 10001:10001 ./config.json && chmod 600 ./config.json   # 600 可以保留，属主对了就行
   ```
3. **别只在构建期/容器内修**——`RUN chown` 与容器内 `chown` 对 bind mount 一律无效，只有宿主机侧生效。
4. **验收看"容器是否真的读到了内容"，而不是看文件存在**：本次是 `/healthz` 从 503 变可应答、日志出现 `loaded N account(s)` / `listening on :7863`；如果只 `ls` 一下文件在不在，会误判成已修好。
5. **命名卷（named volume）可绕开此问题**：Docker 会按镜像内该路径的属主初始化命名卷。文件系统不支持改属主（NFS/SMB）时改用它。
6. **安全与可用的折中**：`chmod 600` + `chown <container_uid>` 是既保权限又保可读的正解，不要因为踩坑就直接 `chmod 777`。

**相邻教训**：容器内改源码的补丁问题见 [[container-image-source-patches-need-replay-script]]；进容器跑 here-doc 的 stdin 坑见 [[container-heredoc-needs-stdin-flag]]。
