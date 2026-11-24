---
name: retired-test-is-not-execution-coverage
description: 门禁把「已退役 / rc=1」的测试当执行型覆盖 ⇒ 覆盖率与全绿都是假的
type: pitfall
topic: verification
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：任何「守卫覆盖率 / 全绿」统计，必须以**本次真正执行且 rc=0** 的测试为准。把 registry 里 retired/replaced 的测试（或 rc=1 的测试）当执行型覆盖，得到的数字全是假的。

**Why**：ZCode 工程的 `check_injected_guards.py` 不读 `tests_3180_registry.json`，把 `test_guards_behavior.cjs` 当作 9 个 `globalThis.__*` 守卫的唯一「执行型测试」；该测试已 retired、回归里不执行、且实测 `rc=1`（ReferenceError）。门禁仍报 37/37 PASS。同一轮审计还发现 `verify_3180.py` 断言一段**死代码字符串必须存在**（3.18.0 的 ipcMain 别名 `hD` 在 3.18.2 已是别的函数，整块被 try/catch 吞掉，通道从未注册）⇒ 门禁把「坏掉的代码」钉成了「必须存在」。

**How to apply**：① 覆盖率统计前先解析 registry，判定测试是否在 active 且 `rc=0`；② 判据不许钉住「字符串存在」作为行为证明，要能证明判据会变；③ 发现死代码后，同时删死代码与那条钉住它的断言，否则下次照样绿；④ 报告里写清每个守卫的真实执行测试文件名。

关联 [[guard-must-cover-the-changed-layer]]、[[rebuilt-bundle-diff-needs-stable-anchors]]、[[minified-alias-must-resolve-at-build-time]]。
