---
name: user-large-files-hardlink-not-copy
description: 用户提供的安装包/大文件在交付目录用 NTFS 硬链接引用，不复制（python 调 `cmd /c mklink /H`，MSYS 直接写会被转义搞坏）；工作期解包产物留到该轮全部完成再清，绝不「删了发现还要用→重新解」；下载只在本地确实没有时发生
type: workflow
source: ZCode 改造项目（2026-10-20 安装包双副本、2026-10-22 删 base asar 后重新解 340MB，两次被斥责）
date: 2026-10-23
verified: 2026-10-22
topic: delivery, windows
---

**经验**：同一份数据不要重复弄——用户视重复副本为浪费，也反感「删了再解」。

## 三条规矩

1. **用户提供的安装包/大文件**：交付目录里用 **NTFS 硬链接**引用原文件，**不复制**。

   ```python
   subprocess.run(["cmd", "/c", "mklink", "/H", link, target])
   ```

   ⛔ 必须走 python 调 `cmd`：MSYS 里 `cmd //c mklink /H ...` 会被转义搞坏，报「无效开关」。
   硬链接后删用户那份也不丢数据（link count），交付仍自包含。
   校验：`fsutil hardlink list <link>` 应列出两条路径；sha256 与 manifest 一致。

2. **工作期间的解包产物**（base asar 等）：留到**该轮全部完成**（构建+验证+交付+入库）后再清；
   绝不「清完发现还要用 → 重新解」。要省空间就先确认本轮不再需要。

3. **下载只发生在本地确实没有时**：先找（用户指的位置、交付目录、硬链接源），再下载。

## Why

- 重复副本 = 双倍磁盘 + 两份可能漂移的版本。
- 「删了再解」会让用户看到同一份 340MB 反复出现，观感和效率都差。

## How to apply

- 收到大文件先问：要复制还是引用？默认硬链接。
- 清理前用「本轮是否还需要」判断，而不是「现在看起来没用」。
- 交付清单里标注哪些是硬链接（link count=2），避免下游误删源文件。

关联 [[hardlink-unify-shared-scripts-across-tools]]、[[windows-home-cleanup-safe-vs-traps]]、
[[user-paths-must-be-clickable-links]]。
