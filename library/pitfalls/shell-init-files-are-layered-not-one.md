---
name: shell-init-files-are-layered-not-one
description: 改 PATH/环境变量时，登录 shell、交互 shell、ssh 命令执行三者读不同的初始化文件，只改一处会出现"同一台机器两个版本"的假象；另外 ssh host 'cmd' 两者都不读；2026-10-10 补：Debian 的 /etc/profile 会**重置** PATH，出现"非登录壳正常、登录壳丢"的反向假失败
type: pitfall
source: MH-Agent-Open / CNB 云原生开发容器（2026-09-30 调试 Python 3.13 + Node 26 落位）；2026-10-10 补 Docker 产品镜像 Node 26/openclaw/cnb-cli 登录壳丢失
date: 2026-09-30
verified: 2026-10-10
topic: methodology
---
<!-- hook-reviewed 2026-10-20：已人工确认 INDEX 钩子覆盖本条全部更新内容 -->


**经验**：给容器/远程机装了新版本软件后，**"装上了"和"敲命令能用"是两件事**。
Linux 的 shell 初始化文件是**分层**的，只改一层就会得到「`bash -l` 是新版本、
`bash -i` 是旧版本」这种看起来自相矛盾的实测结果——**两个结果都是真的**，
不是缓存、不是镜像没生效、也不是你装错了。

**Why**（2026-09-30 实测，同一容器、同一时刻）：

| 调用方式 | 读哪些文件 | 实测 `python -V` |
|---|---|---|
| 登录 shell `bash -l` | `/etc/profile` → `/etc/profile.d/*.sh` → `~/.bash_profile` | **3.13.7** ✅ |
| 交互 shell `bash -i` | 只 `~/.bashrc` | 3.12.14（旧的） |
| `ssh host 'cmd'` | **都不读**（非交互非登录，只认 `BASH_ENV`） | 3.12.14（旧的） |
| 绝对路径 `/opt/py313/bin/python3 -V` | 不依赖任何初始化文件 | **3.13.7** ✅ |

Dockerfile 里的 `ENV PATH=...` 只对**后续 RUN 与容器默认 env** 有效，
它不会自动写进任何 shell 的初始化文件——所以 `docker exec` 进去敲裸命令未必拿到新版本。

**How to apply**：

1. **装完新版本要同时写三处**，别只写一处：
   - `/etc/profile.d/<name>.sh`（覆盖登录 shell）
   - `~/.bashrc` **和** `/etc/bash.bashrc`（覆盖交互 shell；VS Code 集成终端读的是 `.bashrc`）
   - 保持 `ENV PATH` 也写（覆盖容器 exec 与派生进程）
2. **构建期就做落位校验，且两种 shell 都验**：
   ```dockerfile
   bash -lc 'python -V' | grep -q "3\.13" || { echo "登录 shell 未拿到"; exit 1; }
   bash -ic 'python -V' | grep -q "3\.13" || { echo "交互 shell 未拿到"; exit 1; }
   ```
   不加校验的话，你会带着一个"看起来装好了"的镜像跑很久才发现问题。
3. **写自动化脚本时用绝对路径**，不要依赖 PATH。这是唯一对调用方式免疫的写法。
4. **判断"环境到底有没有生效"时，先确认你是用哪种方式问的**。
   我第一次 `ssh host 'python -V'` 看到 3.12 就以为镜像没生效，
   实际是 SSH 命令执行模式不读初始化文件——**差点把一条正确的配置改坏**。
5 ⃣. **下载用官方预编译二进制时补运行时库**：最小镜像常缺 `libatomic1`，
   Node 会报 `libatomic.so.1: cannot open shared object file`（退出码 127，
   落盘成功但一执行就崩）。同理 `libstdc++6` / `libgcc-s1` / `zlib1g` 一起装。
6. **从 github release 下载要 `-L --fail --retry 3`**：会 302 到对象存储，
   不带 `-L` 会把 302 响应体当归档解；不带 `--fail` 则 404 也返回"成功"。

**相邻**：断言"改到了吗"要自证，见（消融自证那条已不在库中，链接暂缺）；
配置字段名/注释不是规格，见 [[config-field-name-is-not-spec-read-consuming-code]]。

**2026-10-10 补充实测（反向失败：非登录壳正常、登录壳丢）**

- 现象（Docker 产品镜像，`FROM python:3.13-slim-bookworm` + Node 26 装 `/opt/node26` + `ENV PATH=/opt/node26/bin:$PATH`）：
  `docker run --entrypoint bash <img> -c 'node -v'` → **v26.9.0 ✅**；同一镜像 `bash -lc 'node -v'` → **command not found**。
  ⇒ 与上表"登录壳拿到新版"**方向相反**——因为 **Debian 的 `/etc/profile` 会把 PATH 重置为默认值**
  （`/usr/local/sbin:/usr/local/bin:...`），`ENV PATH` 里的自定义前缀在登录壳里被**顶掉**。
- 波及面：凡是靠 `ENV PATH` 落位的工具（node/npm/全局 npm 包如 openclaw、cnb-cli）在登录壳里全部失踪；
  容器 `CMD` 与派生进程不受影响（走容器默认 env），所以**产品运行正常、只有"人/Agent 进容器敲命令"时才炸**。
- 修法（一条 RUN，追加层缓存全命中）：
  ```dockerfile
  RUN printf '%s\n' 'export PATH=/opt/node26/bin:$PATH' > /etc/profile.d/00-node26-path.sh \
   && chmod 0644 /etc/profile.d/00-node26-path.sh
  ```
- 判据：**"登录壳报缺件"是假失败**——判镜像缺件必须两种壳各验一次（`bash -c` 与 `bash -lc`），
  或先查 `/etc/profile.d/` 是否已覆盖；只验一种会把好镜像误判成坏镜像（本次差点回退一个正确配置）。

关联 [[ssh-heredoc-delimiter-must-be-quoted]]、[[git-bash-ampersand-breaks-gh-auth-login]]。
