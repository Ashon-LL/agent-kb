---
name: fixing-a-bug-turns-stale-tests-red-rewrite-the-criterion-not-delete
description: 修好一个缺陷后，钉住「修复前形态」的旧测试必然变红——把判据改写成行为判据（含负控），不要删测试、也不要改弱
type: pitfall
topic: verification
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：当一个缺陷被真正修好后，断言「缺陷形态存在」的旧测试会转红。这时正确做法是**把判据改写成行为判据**（真/假两态 + 负控），而不是删测试、也不是把断言改弱成永远成立。

**Why**：ZCode 改造工程一次修 25 条缺陷时，两个旧测试同时转红，根因都是「判据钉住修复前的形态」：
① 主进程 live-TPS 测试断言 `__ZsmHash("sha256").update(raw)` 必须出现在产物里——但那行只存在于一段**从未注册成功**的死注入里（别名写死 + try/catch 吞异常），死代码删掉后断言必然红；正确判据是「CLI writer 与主进程 reader 对同一 id 算出同一个文件名」（端到端比对 + 不同 id 必须不同文件的负控）。
② 端点覆盖测试断言产物里必须出现 `t&&t.endpointOverrides`——而那正是死链形态（`t` 是 providerId 字符串，数学上不可能同时有 `.endpointOverrides`），**正确修复与该断言互斥**；改成断言修复后的接线形态，并额外断言「死读法已消失」。
两个案例的共同点：测试在验证**实现的样子**而不是**行为**，所以实现一改就红。

**How to apply**：① 断言前先问「这条断言锁的是行为还是写法」；锁写法 ⇒ 改成行为断言（端到端比对 + 负控：人为退回旧形态时测试必须红）；② 修缺陷后主动跑全量回归，凡转红的先判断「是回归还是判据过期」，过期就改判据并在报告里写明为什么不是弱化；③ 负控（人为退回旧实现 ⇒ 对应断言转红）能证明判据真的会变；④ 绝不删测试、绝不把断言改成恒真。

关联 [[retired-test-is-not-execution-coverage]]、[[guard-criteria-anchored-to-spelling-always-escape]]、[[test-scope-must-be-pinned-by-index-not-walk]]。
