---
name: windows-hardware-reserved-memory-attribution
description: 「为硬件保留的内存」大头通常是 BIOS 给核显的固定显存切分（UMA carve），与独显直连(MUX)无关；归因三步=SMBIOS求和−系统可见量、dxdiag 专用内存/qwMemorySize、CurrentRefreshRate 验证当前输出卡
type: pitfall
source: default 会话 2026-10-16（机械革命蛟龙15 GM5RGEE 实机：独显直连已生效但核显仍占 4GB）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：Windows「为硬件保留的内存」大头通常是 **BIOS 给核显的固定显存切分（UMA carve）**，与「独显直连」（MUX 只切显示输出）**无关**——核显不被禁用就照样占着那块内存。**2026-10-16 本机逆转结论：首选通道不是 BIOS，而是最新 AMD 驱动的「内存优化器」档位（AMD Software → 性能 → 调整 → 系统）；且该通道只有两档：产能=512MB / 游戏=4GB，512MB 为硬地板（三层互证，见文末终审节）。**

三步归因（全只读）：

1. **算总量**：`sum(Win32_PhysicalMemory.Capacity) − Win32_OperatingSystem.TotalVisibleMemorySize`。⚠️ 别用 `Win32_ComputerSystem.TotalPhysicalMemory`——实测它≈可见量（已不含保留），会算出"保留=0"的假象。
2. **定位 carve**：`dxdiag /t` 输出里每块卡的 `Dedicated Memory`；注册表 `HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-…}\000x` 的 `HardwareInformation.qwMemorySize`。核显这两处 ≈ UMA carve（本机 660M：dxdiag 4069MB / 注册表 4096MB；总保留 4.26GiB 减 4GB 后残差仅 ≈0.26GiB 固件底噪，对得上）。
3. **设置生效 ≠ 占用释放**：`Win32_VideoController` 里 `CurrentRefreshRate` 非零的才是当前输出卡（本机 = RTX 3050，独显直连确实生效），核显 carve 依旧在——两个正交系统。

**Why**：看到"独显直连 + 硬件保留 4G"极易误判成设置没生效/系统有毛病，然后在 Windows 里瞎找开关；也容易把固件底噪（~0.2–0.3GiB，任何机器都有、永远降不到 0）错当成异常。

**How to apply**：遇到"硬件保留内存大"先跑三步对账再下结论；**首选路径（2026-10-16 本机实测反转）＝升级到最新 AMD 驱动后，在 AMD Software → 性能 → 调整 → 系统 → "内存优化器"里换档（产能=小 carve）→ 重启**；BIOS/UMAF 的裸变量写入在 SMM 锁批次上会被静默忽略（读得到、不生效），只能是第二顺位。

**2026-10-16 实机反转（本机蛟龙15 Rembrandt）**：整夜走 BIOS/UMAF 路线全部失败（值存得住、内存初始化不采纳＝"静默忽略型"锁定）；当天装完 **AMD Software 26.9.2** 后，把"内存优化器"从默认改为**产能**档并重启——carve 4096→512MB、硬件保留 **4.255→0.755 GiB**（=512MB carve + 262MiB 固件底噪，与对账吻合）。设置导出 `rssettings.json` 中记录为 **`UMA Carveout` ComponentID 157 State=1,Value=1**。机理：**AMD 驱动的"内存优化器"档位在每次启动时主导该分配**（产能=512M / 游戏=**4GB**（2026-10-16 下午逆向实测修正，此前误记 2G），就这两档——社区与微软问答均有"BIOS/UMAF 改了被 Adrenaline 覆盖"的同款案例），UMAF 的裸 NVRAM 变量写入会被它扳回/忽略；官方通道按档位生效。该档位由新驱动才暴露（旧 31.x/原厂驱动控制面板无此项）。相关 [[env-claims-must-be-reverified]]。

**2026-10-16 逆向终审（REA + Ghidra + Frida 全链路，最终版）**：① Frida 钩住 RadeonSoftware.exe 抓到真实提交调用 `ADL2_Adapter_GPUUMACarveout_Size_Set(ctx, 0, 1|2)`——**值1=产能=512MB、值2=游戏=4GB**；**点"继续"即提交并立即自动重启**（无二次确认，`shutdown /a` 拦不住）。② Ghidra 反编译 atiadlxx.dll（副本 SHA256 `157568287b97af557283e0ad75d859bda501286af0ac4d3dad9f8bb3c81d8e1a`）：Size_Set 用户态白名单 {1,2,3}（其余一律映射 0）；`Info_Get` 返回 [存在位, 默认值, 当前值, **支持位掩码**]，本机恒为 **6=0b110=仅支持模式{1,2}**（历史"6"之谜即此）。③ V2 富通道（`InfoX2_Get` / `X2_Set(ctx,适配器,mode,KMDIndex,&reboot)`，可带容量选项）在全部 9 个适配器实测被驱动拒绝（rc=-1）；ACPI VFCT 提取的本机 VBIOS（113-REMBRANDT-X37）无任何更细尺寸表。⇒ **512MB 是三层互证的硬地板**；262MiB 固件底噪不可动。复现工具包存工作区 `carveout-re/`（frida 钩子/probe 脚本/Ghidra 脚本/反编译与 VFCT 证据）。


**2026-10-16 晚·全通道封卷（用户态可达路径穷举完毕）**：512MB 之下无路——写入点被锁在「AMD 签名驱动 + 固件私有存储」内。清单与实测：① ADL Size_Set 白名单{1,2,3}、支持掩码恒=6（仅{1,2}），值3实测无效；② V2 富通道 InfoX2/X2_Set（带 KMDIndex）全适配器 rc=-1；③ VBIOS v2_3 选项表不存在（VFCT 全扫 + minimum/Medium/High 零命中）——Linux 官方路径（内核 amdgpu_uma_carveout / fwupd / LACT）在本机固件无实现；④ ACPI 无 ATCS 设备（DSDT/SSDT 全扫）——ATCS 0x6/0xA 通道不存在；⑤ 模式持久化=固件私存：95 个 UEFI 变量全量 diff（设置时/重启后仅 LastBoot/计数器 churn）＋ 15 候选名×6 GUID 直探 ＋ 注册表三子树全量 diff，全部零命中；⑥ 组合写入实验（UmaCarveoutModePreserved=0 ＋ UmaCarveOutDefault=1，两者写入均成功）→ carve 纹丝不动 ⇒ 无效。方法论：「持久化必在固件可读处」⇒ 逐一排除用户可见存储后残差=固件私存；唯一入口=ADL V1 两档白名单。工具/证据：工作区 carveout-re/（含 UEFI 变量四件套，见 [[windows-uefi-variable-read-write]]）。

**2026-10-16 深夜·字段级穷尽（第四轮，终局定案）：256MB 也不可达，512MB 为最终地板**。探底再进一步：从 GitHub 找到**同 OEM 蛟龙16Pro 固件 dump 的完整 IFR 文本**（`GaoXanSheng/JiaoLong16ProDump` 的 `Bios/CbsSetupDxeRPL.txt`），其中 `VarStore 0x5000 [3A997502-…] Name=AmdSetupRPL` 即本机 `AmdSetup` 变量本体，并给出官方字段表：**@0x44 iGPU Configuration**（1=UMA_SPECIFIED/2=AUTO/3=GAME_OPTIMIZED/0xF=Auto 默认）、**@0x45 UMA Version**、**@0x46 UMA Frame buffer Size（u32 MiB，官方枚举含 64M/128M/256M=0x100/512M/…/16G）**；IFR 条件逻辑（`Suppress If {A5==1}`+`Not`）证实 **size 仅在 UMA_SPECIFIED 模式生效**（即"1+size"就是官方唯一正确组合）。**实机判决（全部实测）**：① 直写 `@0x44=1, @0x46=256M` → 重启 carve 纹丝不动（值保存完好，固件不重写变量）；② **极端值判决** `@0x46=16G` → 仍纹丝不动（最强"字段不被消费"证据）；③ **安全模式**（safeboot network，不加载 AMD 显示驱动 amduw23g）→ 仍 512MB ⇒ 排除"驱动运行期覆盖"；④ 布局同构性量化校验：16Pro IFR 574 字段对本机字节 **shift=0 命中率 92.5%**（布局高置信同构，"写对了地方"）；⑤ PBS 变量对星曜14 字段表核验 **92% 对齐且表内无 UMA 字段**（PBS@0x09 的 u32=512 非 UMA，勿赌）；⑥ GPD 7840U 新 BIOS 的 **"UMA Carveout Index Max: 0"**=同代平台 Index 机制同样未启用。⇒ **归因：本机 OEM 固件的 GFX 初始化不消费 CBS 的 UMA 字段**（模板/存储存在、消费路径缺），carve 由「驱动 + 固件私有存储」独占；**256MB 在本机当前固件+驱动体系下不可达，512MB=用户态终局**。**方法论沉淀（可复用）**：a) 跨机型固件字段表**必须先做同构性校验**（字段占用位图 × 数据字节命中率统计，或已知字段值域抽样）再动手；b) **"写入保存住 ≠ 被固件消费"**——否定式结论用**极端值判别**（写一个"若生效则一眼可见"的值，如 16G）+ **无驱动环境判别**（安全模式）双刀交叉；c) UEFI 变量读/枚举、AmdSetup 字段补丁（含一键 revert）、VFCT ATOM 主表正经解析等工具在 `carveout-re/`（`uefi-read.py`、`amds-patch.py`、`parse-integrated-info.py`）。

关联 [[no-new-artifacts-in-c-root]]、[[nvidia-driver-update-denied-by-service-key-lock]]、[[windows-memory-hogs-ui-hosts-and-everything]]、[[rustup-update-fails-when-stale-msvc-std-component-missing]]。
