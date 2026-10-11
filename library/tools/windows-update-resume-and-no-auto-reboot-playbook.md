---
name: windows-update-resume-and-no-auto-reboot-playbook
description: WU 搜索 0 项的真因常是"暂停更新"（UX\Settings 里的 Pause* 值可被设到 2053 年）而不是 NoAutoUpdate 策略；解除要删 Pause* 值并重启 WU 栈；"不自动重启"三件套=NoAutoRebootWithLoggedOnUsers+AlwaysAutoRestart=0+活动时段；CU 装完历史码 0x80242014=已装待重启、CBS\RebootPending 置位；新版本按机器分批推送，搜不到≠没有
type: tool
source: 2026-10-08 default 会话 Windows 11 25H2→26H2 升级准备（解除暂停+装CU+防自动重启）
date: 2026-10-08
verified: 2026-10-08
topic: windows, delivery
---

**判"更新为何停滞"的正确顺序**：`NoAutoUpdate` 策略**不是**唯一开关（本机它根本不存在），先看 `HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings` 里有没有 `PauseFeatureUpdatesStartTime/EndTime`、`PauseQualityUpdatesStartTime/EndTime`、`PauseUpdatesStartTime/ExpiryTime`（本机被设到 **2053-11-08**、配 `FlightSettingsMaxPauseDays=9999`）——暂停期间 WU 搜索恒为 0 项。解除＝删掉这些 Pause* 值，然后 `Restart-Service wuauserv,WaaSMedicSvc,BITS`（UsoSvc 有时也能重启），再 COM 搜索即恢复。

**"装更新但不自动重启"的三件套**（用户在使用机器时必写）：
1. `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\Automatic Updates\NoAutoRebootWithLoggedOnUsers=1`
2. `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AlwaysAutoRestart=0`
3. 活动时段放宽到全天：`HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings\ActiveHoursStart=0` + `ActiveHoursMaxRange=23`
改前用 `reg export` 备份这两个键。**功能更新/版本切换的必然结论：必须重启一次，没有"不重启就完成"的选项**；能做的只是停在"待重启"并保证不自动重启。

**用 COM 装更新的验证姿势**：`IUpdateDownloader.Download()` 返回 `resultCode=2` 只是下完；`IUpdateInstaller.Install()` 返回 `resultCode=2, RebootRequired=True` 才算装完。历史条目里 `HResult=0x80242014`（WU_S_REBOOT_REQUIRED）＝**已安装成功、待重启**（别当失败）；同时 `HKLM\...\Component Based Servicing\RebootPending` 会置位而 `WindowsUpdate\Auto Update\RebootRequired` 可能仍为 false——判据看 CBS。下载阶段可能十几分钟无输出（走 Delivery Optimization 时数据不进 `SoftwareDistribution\Download`），看 `ReportingEvents.log` 的 `AGENT_DOWNLOAD_PROGRESS` 事件判断活性，别中途打断。

**新版本推送是分批的**：26H2（build 26300）2026-09-29 GA，2026-10-08 本机仍搜不到——查过**没有** `UpdatePolicy\Settings\TargetReleaseVersion` 钉定、`DeferFeatureUpdates=0`、无保护性暂停，连"含隐藏项"的搜索（`IsInstalled=0`）也只有当前版本 CU——那就是 rollout 没轮到这台机器，不是被挡。搜不到 ≠ 不存在，可改走微软安装助手或 ISO 就地升级（两者都要一次重启；ISO 的 setup.exe 图形界面才有"稍后重启"可点，`/quiet` 会自己重启）。

**功能更新（feature update）有个分叉通道**：rollout 轮到后，**设置页会先出现"Windows 11, version 26H2 可用 · 下载并安装"，但 COM 搜索器（`Search("IsInstalled=0")`）仍返回 0、`usoclient StartInstall` 也拉不动**——因为它处于"已 offer、未 opt-in"状态，**必须用户在设置页点一次那个按钮才入队**（实测 2026-10-09 26H2 就是这样：脚本两条路都拿不到，截图里设置页已可见）。所以"脚本装不上功能更新"往往是正常现象，别误判成策略挡着；点完按钮后 WU 自己下载安装到"待重启"，防自动重启策略照旧生效。

关联 [[windows-uac-and-windows-update-policy-real-paths]]、[[subagent-absence-and-security-claims-need-selfcheck]]。

**功能更新会清空旧还原点——升级后立刻重建基线**：2026-10-10 实测，26H2 启用包装完重启后，升级前建的还原点（#198 基线）与升级过程自己创建的 #199/#200 **全部消失**（新还原点编号已跳到 #203），`vssadmin list shadows` 一条不剩。所以"删快照重建"时经常发现**没什么可删的——是功能更新替你删了**；反过来，任何功能更新之后都应立即建新基线还原点+配置备份，否则就失去了回退能力（回退版本只剩 ISO 就地降级一条路）。

**删还原点的正确姿势（再强调）**：PowerShell **不存在** `Remove-ComputerRestorePoint` 这个 cmdlet（pwsh 与 Windows PowerShell 5.1 都没有，别再试）；两条可用路径：① `vssadmin delete shadows /Shadow={guid} /Quiet` 删掉其影子副本，还原点记录随之消失（**`/Quiet` 必须带，否则停在 "确实要删除(Y/N)" 交互上**）；② `SRRemoveRestorePoint`（`srclient.dll` P/Invoke）直接删记录，返回 0=成功、**2=该记录已不存在**（先删过影子就会这样）。

**"新版本 = 大功能更新"是错觉（26H2 实例）**：26H2 / 25H2 / 24H2 **共享同一 servicing 分支**，符合条件的老版本通过**启用包（enablement package）**升级——本机实测是 eKB5121794（174KB 级）、只重启一次。微软支持页明说 26H2"继承了 25H2 月度更新引入的大部分功能"，它自身带来的主要是：① 默认启用部分此前"临时企业功能控制"的功能（Windows 设置备份、应用专属任务栏操作、文件资源管理器改进）；② 生命周期重置（Pro/Home 24 个月、Enterprise 36 个月）；③ 支持 hotpatch（季度基线需重启、其余月份免重启）。所以查"新版本有什么新功能"要找**当前分支的 What's new 页 + 该版本更新历史页里的行为变化**，别指望每个大版本都有专属功能清单页——26H2 的 What's new 文档至今未上线。