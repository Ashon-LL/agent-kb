---
name: release-package-must-pair-upgrade-and-rollback
description: 发桌面补丁包必须同时给升级脚本和回退脚本；回退至少覆盖上一版/官方/最近备份，回退前备份当前成品，-Check 绝不写盘
type: workflow
source: ZCode 桌面重打版（2026-11-02 用户纠正：只给了 update-zcode，没有 restore-zcode）
date: 2026-11-02
verified: 2026-11-02
topic: delivery, change-discipline
---

**经验**：任何“替换安装目录文件”的桌面补丁包，交付物必须成对：`update-*.bat/.ps1` + `restore-*.bat/.ps1`。用户装完新版本后随时可能要求回退；只给升级脚本等于没有安全网，用户只能手工找备份、改 Program Files，风险和沟通成本都高。

**Why**：升级脚本会覆盖 `app.asar` / CLI，并把旧文件改名成 `.bak-*`；没有回退入口时，用户要么不知道备份在哪，要么用错备份（例如把官方基线当成上一版）。2026-11-02 实锤：v29.15 升级成功、用户确认“我好了”，紧接着问“还原脚本呢？”——这不是额外需求，是交付完整性的一部分。

**How to apply**：
1. 包内固定放 `restore-zcode.bat` + `restore-zcode.ps1`，与 `update-zcode.*` 同级；`.bat` 只做 ASCII/CRLF 启动器，`.ps1` 用 UTF-8 BOM。
2. 回退模式至少四种：
   - `Previous`：回退上一版成品；**包内 `previous/` 自带上一版 asar/CLI**（自包含，不依赖外部目录），按 `previous-release.json` 哈希严格校验；包被裁剪时才退到同级 `ZCode-v<prev>-PATCH` 或上一版 7z。
   - `Official`：优先用安装时留下的官方 `.bak`（按 `CURRENT-META.json` 的 `baseline_asar_sha256` / `baseline_cli_sha256` 过滤），没有备份再用包内官方安装包重装基线。
   - `Backup`：取最新 `app.asar.bak-*` / `zcode.cjs.bak-*`。
   - `Custom`：显式 `-Asar` / `-Cli`，便于只换 UI 或只换 CLI。
3. 回退前先把**当前成品**备份成 `.bak-<stamp>`，保留 2 代；这样回退后还能用 `Backup` 回到刚被替换的版本。
4. 升级脚本本身也要留回退点：**只有没装 / 资源缺失时才重装官方基线**；已装同体系且 cua-helper/sharp 完整时原地替换 asar/CLI，否则基线安装会把上一版 asar 冲掉，回退脚本再自包含也只能回到「官方原版」或更早的包。升级前把当前 asar/CLI 快照到包内 `rollback/`，`Backup` 优先用它。
5. `-Check` 必须全程只读：不能跑安装器、不能留下解压临时目录；把“会重装官方基线”打印出来即可。真实回退前应先用 `-Check` 校验源/目标哈希。
6. 真实替换逻辑要在临时文件上做一次模拟（dummy target + 小文件 source），验证备份、替换、校验、清理整条链；不要为了测试回退去动用户正在用的安装。
7. 回退会关闭并重启 ZCode：文档和脚本都要先提醒保存工作；`-NoStart` 留给自动化，`-KeepRunning` 用于拒绝自动杀进程。
8. 文档里写明“升级/回退成对”，并在 `CURRENT-META.json` 记录 `restore.scripts` 与 `previous_generation`，让下一版构建时不会漏。
