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
