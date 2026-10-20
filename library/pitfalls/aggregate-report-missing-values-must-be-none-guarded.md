---
name: aggregate-report-missing-values-must-be-none-guarded
description: 聚合报表里任一数据源都可能返回 None，做差/求和前必须判数值类型；这类崩溃是间歇的，别据一次成功就认为没事
type: pitfall
topic: reporting
source: APIShow 日报脚本 None - int 崩溃（2026-10-17）
date: 2026-10-17
verified: 2026-10-17
---

**经验**：多源聚合的报告/看板里，**"这一期采不到值"是常态**（源超时、账号被限、接口改版）。
凡是把「本期」和「上期」做差、把同族多个值求和的地方，**必须先判数值类型**，不能只判其中一边是否为 None：

```python
# ✗ 只判了 pv —— v 为 None 时直接 TypeError，整封报告构建失败
d = (v - pv) if pv is not None else None
# ✓ 两边都要是数值
d = (v - pv) if isinstance(v, (int, float)) and isinstance(pv, (int, float)) else None
# ✓ 求和同理：只在全员都是数值时才合并，否则退回逐项展示
if all(isinstance(rows[k], (int, float)) for k in members):
    total = sum(rows[k] for k in members)
```

渲染层也要一起兜：`None` 显示成 `—` / `n/a`，别让 `str(None)` 漏进客户看到的表格。

**Why**：APIShow 各源池积分日报在手动重跑时炸了 —— `emit()` 里 `None - int`（某号余额采不到），
整封报告构建中止、一封都发不出去；同族合并的 `sum()` 有同一个病（原判据只排除了 dict）。
**关键教训是"间歇性"**：同一个脚本当天早上 08:00 的定时任务跑得好好的（那次全部采到数）——
**一次成功不能证明健壮，一次失败也别急着判服务全挂**；判据要看"这次输入里有没有 None"。

**How to apply**：
1. 聚合路径上的每个算术点都过一遍「有没有可能有一边是 None」；宁可多写一个 `isinstance`。
2. 缺失渲染成显式占位（`—`/`n/a`），让人一眼看出"这次没采到"而不是当成 0。
3. 修完用**真的缺值输入**验一遍（本例：直接跑一次采集，用真实缺值复现），别只跑 happy path。
4. 报告类脚本改完记得同步部署路径（APIShow 的定时器 ExecStart 指向 `/opt/apishow/scripts/ops/`，改本地不 scp 等于没改）。

关联 [[report-what-you-did-not-what-you-meant-to-do]]、[[automation-artifacts-lie-existence-and-freshness]]
