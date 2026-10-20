---
name: no-new-artifacts-in-c-root
description: 位置纪律——工具装正规位（C:\Software / C:\Program Files(x86)，别丢 temp/缓存）；工作「产物」不许给 C 盘卫生添乱（进 ~/.zcode/workspace/<项目>，一次性物用 temp 且随手清）；已散落物=搬家+更新引用+删原位
type: workflow
source: default 会话 2026-10-16（装 Ghidra 于 C:\Tools 被纠正 → 用户两轮细化位置纪律）
date: 2026-10-16
verified: 2026-10-16
topic: windows
---

**经验**：位置纪律分两类，别混——
- **工具**（软件/工具链安装）：装到**正规安装位**——`C:\Software`、`C:\Program Files`、`C:\Program Files (x86)`（用户明示的可接受清单；`%LOCALAPPDATA%\Programs` 有既有先例）。工具是持久资产，**不要**丢进缓存/临时目录。
- **产物**（分析输出、工作目录、临时解包、证据件）：**不许给 C 盘卫生添乱**——项目产物进 `~/.zcode/workspace/<项目>/`；一次性物用缓存/临时目录并**随手清理**；不要在 C 盘散落。

**Why**：C 盘是全机公共面，用户的底线是"卫生不被弄乱"。两轮纠正的演进：① 在 C 盘根目录自造 `C:\Tools\` 装 Ghidra 被纠正（根目录不是杂物间）→ ② 我推断"工具放 %LOCALAPPDATA%\Programs、耗材进 temp"又被细化："工具不用放缓存临时目录——可以装在 C:\Software 或 C:\Program Files；但产物我不想给 C 盘卫生管理添乱"。要点：**工具进正位不算添乱，产物散落才算**；temp 是给耗材的，不是给工具的。

**How to apply**：装工具前先看 `C:\Software` / Program Files 既有布局跟先例（拿不准再问）；写产物前先定归属——项目产物→工作区、一次性→temp+清理、绝不让它散在 C 盘。已散落两类物的补救：搬家（同卷 mv）→ 更新全部引用（env/配置/文档/记忆，逐处 grep 复核）→ 删原位（含空壳目录）；工具搬完让引用方实测一次（如 REA `binary_session` 看 Ghidra 就绪）。相关：[[persisting-files-also-requires-exempting-cleanup]]、[[cross-agent-skill-dir-semantics]]。

关联 [[nvidia-driver-update-denied-by-service-key-lock]]、[[windows-hardware-reserved-memory-attribution]]、[[windows-memory-hogs-ui-hosts-and-everything]]、[[rustup-update-fails-when-stale-msvc-std-component-missing]]。
