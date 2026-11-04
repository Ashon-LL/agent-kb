---
name: no-new-artifacts-in-c-root
description: 位置纪律——工具装正规位（C:\Software / Program Files）；产物只放当前工作目录；用户目录 C:\Users\<用户> 是禁区（连自建 _归档/_tmp 也不行，2026-10-29 明确纠正）；已散落物=搬家+更新引用+删原位
type: workflow
source: default 会话 2026-10-16（装 Ghidra 于 C:\Tools 被纠正 → 用户两轮细化位置纪律）；2026-10-29 再次纠正（用户目录下自建 _归档 放报告/备份）
date: 2026-10-16
verified: 2026-10-29
topic: windows
---

**经验**：位置纪律分三类，别混——
- **工具**（软件/工具链安装）：装到**正规安装位**——`C:\Software`、`C:\Program Files`、`C:\Program Files (x86)`（用户明示的可接受清单；`%LOCALAPPDATA%\Programs` 有既有先例）。工具是持久资产，**不要**丢进缓存/临时目录。
- **产物**（分析输出、报告、备份、临时解包、证据件）：只放**当前工作目录** `~/.zcode/workspace/<项目>/`；一次性物用缓存/临时目录并**随手清理**。
- **用户目录是禁区**（2026-10-29 用户明示，属"最不喜欢"级别）：`C:\Users\<用户>` 下不许新建任何自建目录——**包括 `_归档`、`_tmp` 这种看起来"整理过"的目录**。产物、报告、备份一律进工作目录；要长期保留的文档也先放工作区，由用户决定是否外移。

**Why**：C 盘是全机公共面，用户的底线是"卫生不被弄乱"。演进：① 在 C 盘根目录自造 `C:\Tools\` 装 Ghidra 被纠正（根目录不是杂物间）→ ② 推断"工具放 %LOCALAPPDATA%\Programs、耗材进 temp"又被细化（工具进正位、产物别添乱）→ ③ 2026-10-29 把环境体检报告和操作备份放进 `C:\Users\MECHREVO\_归档\2026-10-29\`，被明确批评"不要放在工作文件夹外，尤其是用户文件夹，是我最不喜欢的"。要点：**"归档得很整齐"不等于合规；只要在工作目录外就是违规**。

**How to apply**：写任何文件前先问自己"它在当前 working dir 里吗"——不是就先改路径，别事后搬。报告、备份、临时脚本、下载物、解包目录全部落在工作目录；需要跨会话保留就留在工作区并告诉用户路径。环境修复类改动（PATH、shim、依赖目录迁移）属"工具位"可按既有规则处理，但不得顺手在用户目录新建目录。已散落物的补救：搬家（同卷 mv）→ 更新全部引用（env/配置/文档/记忆，逐处 grep 复核）→ 删原位（含空壳目录）；工具搬完让引用方实测一次。相关：[[persisting-files-also-requires-exempting-cleanup]]、[[cross-agent-skill-dir-semantics]]。

关联 [[nvidia-driver-update-denied-by-service-key-lock]]、[[windows-hardware-reserved-memory-attribution]]、[[windows-memory-hogs-ui-hosts-and-everything]]、[[rustup-update-fails-when-stale-msvc-std-component-missing]]。