---
name: windows-wsl2-memory-accounting
description: WSL2 内存三层核对法（.wslconfig 上限/回收、WSL 内 free -m、宿主 vmmemWSL 工作集与提交、容器另用 docker stats）；WSLg 是第二个隐藏 VM；autoMemoryReclaim 与 vmIdleTimeout 的取舍
type: tool
source: default 会话 2026-10-16（本机 kali-linux 实测：上限 8GiB、实占 1.7GB、vmmem 工作集 2.4GB）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：回答"WSL/容器占多少内存"要分三层取证，只报一个数都会误导：

1. **上限**：看 `~/.wslconfig` 的 `[wsl2]` 段——`memory=`（字节数）是硬顶，另有 `swap=`、`processors=`；`vmIdleTimeout`（毫秒）是空闲关机阈值，设成极大（如 3.6e8≈100 小时）等于永不关机＝保常驻服务的代价；不设 `memory=` 时上限可达宿主一半。
2. **实占**：WSL 内 `free -m`（total=上限、used=真实占用；本机 1.7GB/8GB）；容器单独 `docker stats --no-stream`；`ps -eo rss,args --sort=-rss` 定位大头（本机=网关 node ~0.6GB + 容器 ~0.5GB + docker 引擎 ~0.14GB）。
3. **宿主视角**：任务管理器里看不见 WSL——查进程 `vmmemWSL` 的**工作集**与**提交**两个数（本机 2.4/3.7GB）；另有个 `vmmemCmZygote` ＝ **WSLg（图形支持）的第二系统 VM**（提交 ~0.9GB），不用 WSL 图形程序可 `[wsl2] guiApplications=false` 关掉。

回收与调优：WSL 的空闲内存不保证立即还给 Windows，加 `autoMemoryReclaim=gradual`（可选 `sparseVhd=true`）；改 `.wslconfig` 必须 `wsl --shutdown` 才生效（会瞬断 WSL 内服务）。

**Why**：单数字必错——`free` 的 used 不含 WSLg 第二 VM 与引擎开销；vmmem 工作集会把缓存算进去；不设上限的机器一旦跑泄漏型服务会把宿主吃干。

**How to apply**：被问"WSL/容器是不是太占内存"时按三层给账再下结论；优化顺序＝停不用的容器（先查 `restart=unless-stopped` 这类会随引擎自回的策略）＞ 关 WSLg ＞ 加自动回收 ＞ 最后才考虑把服务搬去远端（本地钩子/端口直连的价值通常大于那几个 GB）。相关 [[warp-split-tunnel-china-direct]]。

**2026-10-18 补（本机实测定案）**：`autoMemoryReclaim=gradual` 在本机近乎无效——空闲时 vmmemWSL 2.5GB，而 WSL 内 used 仅 945MB（cache 约 1.4GB）。改成 **`dropcache`** 后空闲稳定 **410–500MB**。压力验证：灌页缓存把 vmmem 拉到 **7.7GB**（撞 8GiB 上限），静止 **90 秒回落 475MB**；跑一次 team-memory recall 后瞬时 2.8GB → 90 秒回落 499MB。⇒ vmmemWSL 的“大”主要是页缓存，`dropcache` 是有效开关；改完必须 `wsl --shutdown`，distro 内 systemd 会自动拉起 `tdai-gateway`（8420；Windows→WSL 回环实测可通）。启动时会出现一条 `wsl2.autoMemoryReclaim … 键"10"未知` 的告警，实测设置已生效，属无害提示。回滚=恢复 `.wslconfig.bak-20261018` 再 `wsl --shutdown`。2026-10-18 深夜按用户要求再把 memory 8GiB→**4GiB**、processors 4→**2**：`nproc=2`，free total 3917MB、swap 4096MB（未用），空闲 vmmemWSL **370MB**；8420 网关内/外均健康。注意：内存 4GiB 下重负载（大编译/大容器）可能触发 OOM，swap 4GiB 是兜底；processors=2 会限制并行度。
