---
name: build-gate-must-verify-artifact-freshness
description: 语法/构建闸门不能无条件接受上一轮残留产物：干净环境会因缺件失败、有残留时旧产物冒充本轮而过闸，导致交付件版本错位且全链绿灯；闸门必须按本轮实际执行的步骤动态决定检查集并校验产物新鲜度
type: pitfall
source: zcodepro 全量审计 2026-11-04（%USERPROFILE%/Downloads/Project/zcode改造/reports/audit-2026-11-04/01-build-chain.md P1-2）
date: 2026-11-10
verified: 2026-11-10
topic: ci, verification
---

**经验**：构建闸门检查的文件集合必须来自**本轮实际执行的步骤**，且要能证明被检查的产物是本轮生成的。默认流程不带 CLI 步骤时，语法闸门若恒含 `zcode.cjs`：干净环境必因缺件失败；工作区留有上一轮 CLI 时，闸门拿旧 CLI 通过，asar（本轮）与 CLI（旧轮）版本错位却全链绿灯。

**Why**：该 CLI 不进 asar、由升级脚本单独落盘，所以「语法过了」和「交付组合一致」是两件事。实测一次 8 步构建日志里出现 `SYNTAX OK: zcode.cjs`，靠的正是上一轮残留；没有任何新鲜度校验。这与 [[silent-continue-masks-lost-check-coverage]] 同为「门禁全绿但漏检」，但漏的是**产物身份**而非校验项。

**How to apply**：① 闸门按 `--with-cli` 之类开关动态决定检查集，未跑的产物要么显式豁免并打印提示，要么直接失败；② 每个被检查文件记录本轮生成时刻/哈希，与闸门读取值比对；③ 交付前把所有交付件（含不进主包的旁挂文件）作为一组对账；④ 用一条测试模拟「工作区残留旧产物 + 本轮未生成」，断言闸门红而不是绿。

关联 [[installer-completion-by-hash-not-mtime]]、[[local-sync-must-reach-user-visible-layer]]。
