---
name: windows-host-open-from-linux-volume-export-on-demand
description: Linux 容器命名卷可能含 Windows 无法表示的文件名，Windows 宿主打开文件时不要强迁全量 bind mount，应按需导出单个文件到宿主缓存
type: pitfall
source: MH-Agent-Open Windows+WSL 容器产物打开（2026-10-29）
date: 2026-10-29
verified: 2026-10-29
topic: container
---

**经验**：Windows + WSL 运行 Linux 容器时，若历史命名卷里可能出现 Linux 合法、Windows 非法或乱码的文件名，不要为了让 Explorer 看见路径而把全量卷迁到 Windows bind mount。保留 Linux 命名卷为权威数据源；用户要打开某个文件时，只把经过工作流 ID + 相对路径校验的单个文件 `docker cp` 到 Windows 宿主缓存，再调用默认程序或 Explorer。

**Why**：MH-Agent-Open 实测全量 tar 解包到 NTFS 时，多个历史中文乱码文件名触发 `Invalid empty pathname`，继续强迁会丢文件。按需导出 `PAPER_BACKFILL.md` 到 Windows 缓存后，路径可被 Explorer 使用，文件大小与容器源文件同为 6559 字节，同时原命名卷不变。

**How to apply**：容器权威数据需要被 Windows 原生程序打开时，桥只接受逻辑身份（容器名固定、工作流 ID、相对路径），拒绝绝对路径和 `..`，用安全扩展名白名单限制直接打开；导出目录标为缓存而非权威数据。Linux 原生部署没有宿主桥时只提供页内预览，不伪装打开成功。

相关：[[container-host-file-and-exec-boundary]]、[[bind-mount-owner-must-match-container-uid]]。
