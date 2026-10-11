---
name: npc-iterate-by-sending-failure-text-back
description: NPC 派单迭代时，把「红的断言原文 + 失败行 + 期望语义」整段回传给同一分支，别自己改；既有用例回归必须单独标为必修
type: tool
topic: cnb, agent-orchestration
source: CNB NPC 派单迭代 D38（2026-10-02 实测，回归用例 test_delivery_audit_split.py）
date: 2026-10-02
verified: 2026-10-02
---

**经验**：取回复算发现测试红之后，**不要自己动手改**——把失败原文整段回传给 NPC，让它修同一个分支。
回传里必须包含三样：① 断言原文（含期望值 vs 实际值）② 失败的具体行 ③ 你期望的语义（不只是"让它绿"）。

**Why**：自己改就退化成"我在替它写代码"，丢掉分工；而只说"有测试红了"会让它猜，容易只顾自己的新用例、
漏掉被它改坏的**既有用例**。实测（20261002 D38）：它新契约红 + 既有用例 `test_delivery_audit_split.py`
因 `_normalize_deliverable_name` 未 re-export 而断链；我在回传里把后者单独标为「必修 + 二选一修法」，
它才能对准。

**How to apply**：
- 回传模板：`上一版分支 <branch> 我已取回复算；方向对，但有 N 条红：` → 逐条给「现象 / 原因 / 修法（可二选一，由你判断）」。
- ⛔ 不许写「把断言放宽让它绿」——那是取消判据。
- 让它**更新同一分支**（不新建），我这边 `git fetch` 后在同一 verify 分支上复跑即可。
- 复算范围 = 改动到的 tests + 相关既有门禁用例，**必须全绿**才合入。

关联 [[cnb-token-usage-audit]]、[[cnb-npc-dispatch-essentials]]。