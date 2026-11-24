---
name: flaky-test-needs-margin-and-full-failure-log
description: 偶发失败要先留全量证据再改判据；阈值边界断言必须留余量（别用 boundary-1ms），否则回归里随机红、单跑却全绿
type: pitfall
topic: verification
source: zcode改造-v29.22-audit-2026-11-16
date: 2026-11-16
verified: 2026-11-16
---

**经验**：遇到「偶发失败」（回归里红、单跑全绿）时，**先让失败留下完整证据，再改判据**；并且阈值类断言**必须留余量**，不要贴着边界写。

**Why**：ZCode 工程的回归里 `test_host_idle_sweep_3180.cjs` 偶发 rc=1，而单跑 6/6 全绿。原因是断言用「年龄 = 阈值 − 1ms 判忙」：求值时真实时钟已越过阈值 ⇒ 偶发翻红。更糟的是回归器**只保留失败输出的最后 3 行**（"1 } | | Node.js v24.19.0"），看不出是哪条断言、没有堆栈，排查只能靠反复重跑碰运气。两条都是**工具与判据的缺陷**，不是产品缺陷。

**How to apply**：① 回归器把失败测试的**完整 stdout/stderr 落盘**（如 `out/logs/regression-fail-<test>.log`）并在汇总里给出路径 —— 没有全量证据就不要动判据；② 边界断言留 1 秒量级余量（`grace-1000` 而不是 `grace-1`），"边界外"那侧用 `grace` 或更大；③ 若被测逻辑本身用真实时钟，尽量注入假时钟消除求值时刻漂移；④ 结论要写明「这是测试缺陷还是产品缺陷」并给出证据，别把偶发红当成产品回归去改实现。

关联 [[tautological-assertion-and-self-scoped-recheck]]、[[no-assertion-without-measurement]]、[[fixing-a-bug-turns-stale-tests-red-rewrite-the-criterion-not-delete]]。
