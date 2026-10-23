---
name: user-list-to-plan-must-diff-each-item
description: 用户圈定的清单是契约——转成计划/任务书/脚本前必须逐项 diff（用户每项 ↔ 计划落点），缺项补上或显式说明「本批不含」；用户拍板的动词（恢复/删除/保留）不得替换成近似词，方向反了比漏项更危险
type: pitfall
source: MH-Agent-Open（2026-10-06 清单 10 项只落 4 项，用户一句「都是我全部要的吗？」点破）
date: 2026-10-23
verified: 2026-10-06
topic: delivery, methodology
---

**教训**：用户圈选的清单是**契约**，不是参考。把它转成计划/任务书/脚本的每一步，都可能无声丢项或改变语义。

## 事故

用户两次明确圈选 ArHub 增补清单（10 项 + 门禁改造）。我转成 dynamic workflow 脚本时只装了 4 项：
漏了审稿分数曲线、DOCX 预览、沙箱恢复；用户拍板的是「恢复」我还做成了「删掉/止血」；另有扩展中心、文件引用、附件徽章缺失。
用户一句「都是我全部要的吗？」点破。

**最危险的形态不是漏项，而是把「恢复」改成了自己的近似词「止血」——方向相反。**

## How to apply

1. 凡从用户清单转出执行物（workflow 脚本 / 任务书 / 批次计划），提交前**逐项 diff**：
   用户清单每项 ↔ 计划中的落点，一行一项；缺项必须补或显式写「本批不含、原因」。
2. 用户对已拍板的动词（恢复/删除/保留/合并）**不得替换**；要改口径先回去问。
3. 交付计划时附覆盖对照表，让用户一眼能核对。
4. 自检问句：「用户原话里点名的每一项，在计划里都能指到具体落点吗？」

关联 [[taskbook-write-the-property-not-your-guessed-mechanism]]、
[[spec-priority-official-first]]、[[minimal-change-and-no-scope-creep]]。
