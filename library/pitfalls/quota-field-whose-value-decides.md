---
name: quota-field-whose-value-decides
description: 配额/额度响应里常有多个"看着都像剩余量"的字段，实际计费口径只看其中一个（周期字段优先）；对"名义额度"字段求和会高估，甚至把已耗尽的号报成有钱
type: pitfall
source: APIShow/WorkBuddy 额度口径（2026-09-27，同一账号两种算法差 500~4092 分）
date: 2026-09-27
verified: 2026-09-27
---

**经验**：配额响应里普遍有多个额度字段，**求和必须用消费方实际使用的那个**（本项目是"周期字段优先"），否则会得出与平台判断相反的结论。

**Why**：实测同一个账号、同一份响应，两种算法结论完全相反：

| 账号 | 对 `CapacityRemain` 求和 | 按消费方口径（`CycleCapacitySize>0` 时取 `CycleCapacityRemain`） | 实际可用 |
|---|---|---|---|
| 号A | 4092 | **3592** | ✅ 可用 |
| 号B | 2031 | **1531** | ✅ 可用 |
| 号C | **500** | **0** | ❌ 429 额度已用尽 |

号C 最致命：`CapacityRemain=500` 看着有钱，但同包里 `CycleCapacityRemain=0 / CycleCapacityUsed=500`（**周期额度已用尽**）。上游真实行为是拒绝调用——**信了名义字段就会把废号当可用号接入**。

**How to apply**：
1. **别自己发明求和口径**——先 `grep` 消费该响应的代码（或读对方文档），找到它实际取哪个字段、有无优先级分支。本例消费方实现是 `if CycleCapacitySize > 0 { 取 CycleCapacityRemain } else { 取 CapacityRemain }`。
2. **口径要能解释"平台的拒绝行为"**：如果算出来有余量、但真实调用被拒，说明口径选错了——以**拒绝行为**为准反推正确字段。
3. **同一响应里的多个额度数字要分别说明来源**，汇报时写清"按哪个字段算的"；别只报一个数字。
4. **周期性字段 vs 名义字段**要分清：`Cycle*`（本期用量）/`*Remain`（名义剩余）常并存，前者才是计费依据。
5. 缓存/回填延迟会造成**第三个数**（如池内显示 0 而真实 350）——三个数不一致时，以**能解释调用结果的**那个为准。

**相邻**：字段名不可信的通用族见 [[config-field-name-is-not-spec-read-consuming-code]]；两类不可用（额度尽/封禁）的区分见 [[quota-exhausted-vs-banned-distinguish]]。
