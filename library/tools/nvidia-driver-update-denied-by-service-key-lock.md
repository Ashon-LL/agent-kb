---
name: nvidia-driver-update-denied-by-service-key-lock
description: NVIDIA 驱动升级报"图形驱动程序失败"且 UserPnp 20003 显示 NVDisplay.ContainerLocalSystem 返回值 5（拒绝访问）：服务键被安全软件（实测火绒）拦改放删、ACL 清白且 SYSTEM 也写不进=内核过滤；解法=退出安全软件→sc delete 容器服务→重装
type: tool
source: default 会话 2026-10-16（蛟龙15 + 火绒环境下 610.88→617.42 失败一轮后修复）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：NVIDIA 升级失败（安装器报"图形驱动程序 失败"、设备一度从系统消失）时，先查系统日志 `UserPnp` 事件 ID 20003：

- "…添加服务 **NVDisplay.ContainerLocalSystem** …返回的状态值为: **5**" = 拒绝访问，**卡点就是它**（同批 `nvlddmkm` 返回 0 = 成功，驱动本体没问题）。
- 判别"权限 vs 内核过滤"：对该服务键做**同值写**（`Set-ItemProperty ... -Name Start` 写原值）与 `sc config <svc> start= demand`——若被拒、但 `Get-Acl` 显示 Administrators=FullControl、且**以 SYSTEM 身份跑任务也写不进** ⇒ 内核级过滤（安全软件的驱动保护），不是 ACL 问题。
- 实测凶手＝**火绒的驱动保护**：它"**禁改、放删**"——退出火绒后同值写立即放行（对照组证据）。

**解法三步**：① 退出火绒（或其他安全软件）② `sc delete NVDisplay.ContainerLocalSystem`（`NvContainerLocalSystem` 如同样被锁一并删；删除动作放行）③ 重跑安装器（静默 `-s -noreboot` 即可）——它会**全新创建**服务，绕开"修改被拒"的死结。装完恢复安全软件。

**Why**：安装器默认走"更新现有服务"路径，改被拒 → 整包判定失败 → 旧驱动已被自己卸掉、新的装不上 → 设备从系统消失（靠核显接管显示才没黑屏）。只重试、只提权都不会成功（连 SYSTEM 都被拦）。

**How to apply**：NVIDIA 升级失败先 `Get-WinEvent -FilterHashtable @{LogName='System'; Id=20003}` 定位卡点；三步法恢复；DriverStore 清理用 `pnputil /delete-driver <oemNN.inf>`（在用包会被自动拒绝删除，属保护）。
