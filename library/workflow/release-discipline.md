---
name: release-discipline
description: 发布门禁硬阻断必做项、升级/回退包成对、发版后卫生、tag 与线上资产一致
type: workflow
source: 合并自 release-gate-requires-must-do-items-closed, release-package-must-pair-upgrade-and-rollback, post-release-housekeeping-mandatory, release-tag-must-match-published-artifact；zcodepro 复盘 2026-11-04（%USERPROFILE%/Downloads/Project/zcode改造/reports/project-retrospective-2026-11-04.md §6.2）; ZCode 桌面重打版（2026-11-02 用户纠正：只给了 update-zcode，没有 restore-zcode）; zcodepro v29.20（2026-11-09 用户明确「记住：每次发版后都要做项目清理卫生整理」）; zcodepro 复盘 2026-11-04（%USERPROFILE%/Downloads/Project/zcode改造/reports/project-retrospective-2026-11-04.md §6.3）
date: 2026-11-02
verified: 2026-11-10
topic: delivery, change-discipline, git
---
**经验**：发布门禁硬阻断必做项、升级/回退包成对、发版后卫生、tag 与线上资产一致

> 本条由 4 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## release-gate-requires-must-do-items-closed

**经验**：用户说「计入本版要修」的条目，发布前必须逐条核到**代码 + 产物 + 文档**三处都关闭；不能因为已写进待办清单就算处理。发布顺序里加一条显式闸门：列出本版必做项 → 逐条给出关闭证据 → 有任一项未关闭就停止发布。

**Why**：实测用户 10:03 指定了一项 P1 计入 v29.17，执行方只写进 `open-items` 且标题「暂不修」，发布时 README/RN 仍把它列为已知问题；用户质问后才于同日重制补修。随后又错误建议「升一个新版本」，被用户纠正「本来就该做到这一版里」。一个漏项连带引发：同版本重制、资产同名覆盖、tag 漂移、三轮文案纠错。

**How to apply**：① 建版本分支时把用户点名的必做项固定成清单；② 发布前一条命令/脚本逐项核对并输出「已关闭 / 未关闭 + 证据路径」；③ 未关闭就停，不用「下版再修」替代；④ 补做本版漏项**不新增版本号**，同名资产覆盖后同步 tag 与 release body（见 [[release-discipline]]）；⑤ 文案按 [[release-discipline]] 固定模板输出。发版后的清理另见 [[release-discipline]]。

关联 [[change-scope-boundary]]。

## release-package-must-pair-upgrade-and-rollback

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

## 发版后必须做项目清理卫生

### 经验

每次正式发版后，**自动**执行项目卫生清理，把它当成发版流程的固定收尾步骤，而不是等用户提醒才做：

- 清临时探针、一次性脚本、构建中间物、过期引用与失效链接、**上传凭据/token 残留**。
- 产物只留「当前交付 + 上一代 + 当前构建链」；更老的交付/解包目录核对无构建与文档引用后删除（哈希留档即可追溯）。
- 删除前逐个核对引用（构建脚本 grep + 文档/审计 grep），保留规则指定的对照链与审计证据，不顺手删线上版本。
- 留一份 housekeeping 记录（删了什么/保留什么/为什么），有流程决策补 ADR。
- 删 release/tag/分支仍须用户单独确认，卫生清理不顺势删线上版本。

### Why

zcodepro v29.20 发版后没自动做卫生，用户不得不补一句「并清理卫生」才触发——当时发版顺序清单只写到「文档改为已发布」，漏了卫生这一步，于是被当成可选。工作区会持续堆积旧交付（每个 ~1.7G）、解包中间物（每个 ~1G）和凭据临时件，不清理既占空间又留安全隐患（token 落盘）。本次清理约 7GB 并删掉了上传凭据 `_token.txt`。

### How to apply

- 任何项目「正式发版」收尾时，把卫生清理 + ADR 检查列为最后一步，主动做完再汇报，不等提醒。
- 把该步骤写进项目的发版顺序清单/AGENTS，避免下次又漏（与 [[release-discipline]] 同为发版纪律）。
- 清理遵循「先核引用再删、哈希留档、线上版本删除另行确认」。

## release-tag-must-match-published-artifact

**经验**：若发布体系允许「同一 tag/版本号覆盖资产」，就必须同时定义「重制后 tag 怎么处理」。规则：`tag` 所指 commit 的源码要与线上资产一致；重制发布后把 tag 移到含该修复的忠实提交并推送，release body、资产哈希、文档同步核对。

**Why**：实测 v29.17 初版发布后同日重制，tag 仍指初版 `f12010a`，重制在 `ede5539`，因此 tag / release body / 资产 / main 分处不同提交点；按 tag 复现不出用户实际下载的东西。v29.15 亦有三次同名覆盖、tag 停在更早时代。v29.20 又出现同类漂移（水印修复资产已覆盖、tag 落后 3 个提交），后经用户确认把 tag 移到忠实提交并 force 推送。

**How to apply**：① 发版时记录「tag commit ↔ 资产 sha256」对照；② 覆盖资产后立刻复核该对照，不一致就移 tag；③ 移动已发布 tag 属改写历史，需用户单独确认；④ 没有不可变 build id 时，至少保证 tag 与资产同源，别让「可复现」只剩口号。与 [[installer-completion-by-hash-not-mtime]]（用哈希判身份）、[[sync-semantics]]（同步≠发布）配合。

关联 [[release-discipline]]。
