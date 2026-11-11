---
name: acceptance-tool-version-drift-false-failure
description: 一键验收脚本若把版本号/产物哈希/包目录写死，换代后会拿旧包对已正确安装的新版，把「装对了」误报成 FAIL；验收工具必须从当前交付元数据动态读取期望值
type: pitfall
source: zcodepro 2026-11-10 装机验收（%USERPROFILE%/Downloads/Project/zcodepro/tools/quick_post_install_check_v2919.py 实测）
date: 2026-11-10
verified: 2026-11-10
topic: verification, delivery
---

**经验**：验收脚本的期望值（代次、asar/CLI sha256、交付目录、previous 版本）一律从当前包的 `CURRENT-META.json` / manifest 动态读取，不要在脚本里写死上一代常量。换代后至少要有一条自检证明工具仍指向当前交付物。

**Why**：实测 `quick_post_install_check_v2919.py` 写死 v29.19 的 `ZCode-v29.19-PATCH` 与 `8383d9c4…`；用户正确安装 v29.21（`8b415929…`）后它报 `installed app.asar bytes: got 373524338 want 373506918` 并输出「请先运行 update-zcode.bat」——**假红会诱导用户重装甚至覆盖正确安装**。改用当前交付包跑 Go 检查器即 PASS。工具本身随版本漂移，与 [[runtime-acceptance-needs-user-install-not-static-proxies]]（静态全绿只是代理信号）互补：那条讲别把静态当运行态，这条讲别把过期工具的输出当真。

**How to apply**：① 脚本参数化 `-patch-dir/-manifest`，默认值也取「当前 manifest 指向」而非固定字面量；② 输出里打印期望值来源与生成时刻；③ 发版卫生（[[post-release-housekeeping-mandatory]]）把「验收工具是否仍指向当前代」列为检查项；④ 遇到验收 FAIL 先核对工具期望值，再判断是不是装机问题，绝不据假红让用户重装；⑤ 保留旧脚本时注明「仅适用于 vX.Y」，或统一改为通用检查器。
