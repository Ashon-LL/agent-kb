---
name: windows-uefi-variable-read-write
description: Windows 用户态枚举/读取/写入 UEFI 变量——NtEnumerateSystemEnvironmentValuesEx(class 2) 条目结构、SeSystemEnvironmentPrivilege 启用样板（ctypes 需 argtypes）、GUID 规范序坑（枚举给小端存序、直读 API 要规范序）、SetFirmwareEnvironmentVariableEx 保 attr 写入+回读验证
type: tool
source: default 会话 2026-10-16（AMD carveout 探底自研，carveout-re/uefi-*.py）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：Windows 用户态读写 UEFI 变量（NV+BS+RT，attr=0x7）全流程可行，四个必知点：
1. **特权**：需 `SeSystemEnvironmentPrivilege`（管理员默认持有）。ctypes 启用 AdjustTokenPrivileges 时必须显式写 argtypes/restype，不写会 err=6 假失败。
2. **枚举**：`ntdll.NtEnumerateSystemEnvironmentValuesEx(2, buf, &needed)`（先探长度收 0xC0000023）。条目结构：`{u32 NextEntryOffset; u32 ValueOffset; u32 ValueLength; u32 Attributes; GUID(16B); WCHAR Name[]}`——ValueOffset 相对条目起点。
3. **GUID 坑（最易错）**：枚举缓冲里 GUID 是**小端存序**（前三字段 LE），而 `Get/SetFirmwareEnvironmentVariableEx` 要**规范序字符串**。两者直接互换必查不到（表现为"变量明明在列表里却读不到"）。转换=Data1/Data2/Data3 各字节反转；用已知 EFI 全局 GUID {8be4df61-93ca-11d2-aa0d-00e098032b8c} 自检。
4. **写入**：`SetFirmwareEnvironmentVariableExW(name, "{guid}", data, len, attr)`——attr 用原值；写完**必须回读验证**。固件接受写入 ≠ 写入被固件使用（实测写入 carveout 相关变量成功但开机行为不变——有效性必须另证）。

**Why**：固件排障/取证常需在 Windows 侧读改 NVRAM 变量；不知道 GUID 序和 argtypes 两个坑会在"系统里好像没这个变量"上浪费大量时间。

**How to apply**：直接复用 `carveout-re/uefi-{diff,check,write,probe-names}.py` 四件套（全量枚举快照+diff / 定稿检查 / 单变量写入回读 / 候选名×GUID 直探）。排查"驱动/固件把设置存哪儿"：全量枚举 diff（设置时＋重启后各一份）→ 零命中再按候选名×已知 GUID 直探 → 仍零命中则残差=固件私存。
