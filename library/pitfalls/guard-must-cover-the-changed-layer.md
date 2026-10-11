---
name: guard-must-cover-the-changed-layer
description: 守卫必须覆盖改动实际发生的那一层——Python 守卫不覆盖 Rust 改动等于没有守卫
type: pitfall
topic: verification
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：加守卫（测试/门禁/静态扫描）时问一句：它扫的那一层，和我这次改动的那一层，是同一层吗？跨层守卫等于没有守卫。

**Why**：Python AST 扫 `subprocess.*` 的守卫完全不覆盖 Rust 的 `Command::new` 链式块。改 Rust 层新增子进程时守卫一条都没拦到，回归直接漏过。新增子进程时先看同文件既有的写法（如 `creation_flags(0x08000000)`），别自创。

**How to apply**：守卫的扫描范围必须与改动层对齐。同文件既有纪律要照做（如 CREATE_NO_WINDOW 字面量只在 helper 模块出现，新调用点必须复用 helper）。绕开守卫是错的。

关联 [[ablation-must-self-verify-change-applied]]、[[stated-provenance-needs-evidence-and-conditions]]、[[plan-before-acting-and-verify-before-claiming]]。
