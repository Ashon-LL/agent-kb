---
name: module-acceptance-four-file-set
description: 项目膨胀后按「模块目录 + 四件套（说明/验收标准/试验方案/验收报告）」拆，并把「先看文档与已有轮子」写成硬规矩
type: workflow
topic: methodology
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：项目变大到「一个目录塞几十个脚本 + 多个注入层」后，拆分的最小单位不是文件夹，而是**可验收的子模块**：每个模块一个文件夹，固定四件套——模块说明（边界/依赖/已有轮子）、验收标准（判据命令+期望+严重度）、验收试验设计方案（先写证伪点）、验收报告（逐条给证据，未测写原因）。再加一份 md 总目录当「目录页」，把模块、耦合红线、状态挂在上面。

**Why**：ZCode 改造工程到 2026-11-16 已 26 GB、11 层/53+51+37 个注入点、约 80 个工具脚本、72 条 ADR。审计发现三件事都因为缺这道结构：① 同一份逻辑在 CLI 与主进程各实现一份（双源不一致）；② 守卫门禁把退役测试当执行型覆盖，因为没人维护「注入点→执行型测试」映射；③ 改一个模块不知道会连带破坏哪个模块（耦合红线缺失）。把「先看文档与已有轮子」写进项目 AGENTS（新增 §10）+ 一份 START-HERE（必读顺序 + 已有轮子总表 + 动手前 5 问）后，新增能力前必须先证明无同类实现。

**How to apply**：① 先建模板与总目录，再逐模块填四件套，用一个 lint 脚本校验「四件套齐全 + 索引可达 + 验收/试验条目存在」并接进门禁；② 验收项必须是可判定命令，禁止「基本可用」；③ 试验先写证伪点；④ 把可复用流程沉淀成技能（SKILL.md + frontmatter），并装进工作区 `.zcode/skills/` 让后续会话自动发现；⑤ 跨模块改动按「耦合红线」一起验收，不要单模块自说自话。

关联 [[plan-before-acting-and-verify-before-claiming]]、[[guard-must-cover-the-changed-layer]]、[[retired-test-is-not-execution-coverage]]、[[read-upstream-specs-before-probing]]。
