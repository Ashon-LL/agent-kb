---
name: tautological-assertion-and-self-scoped-recheck
description: 恒真断言（assert ... or True / 自比）比没写守卫更危险——它让人以为有兜底而判据从写下那天起就不存在；配套铁律：复检范围必须独立于改动范围，否则「改动=复检=守卫」三圈重合产出假绿
type: pitfall
topic: verification
source: MH-Agent-Open（2026-10-23 CNB issue #209 独立检验；维护者 P0-02 首轮假绿被推翻）
date: 2026-10-23
verified: 2026-11-04
---

**经验**：交付自检时有两类假绿，形态不同但同源——**判据存在但不可能失败**，以及**判据只看我改过的地方**。

## 一、恒真断言：`assert ... or True` 比没有守卫更危险

危险在哪：**没有守卫**时你知道自己没兜底；**有恒真守卫**时你会拿它当证据去汇报「残留 = 0」。

实锤（2026-10-23 一次扫出 5 处，全是同一形态）：
```python
assert "AGENTS.md" not in line or "$_MH_CTX" in line or True     # 恒真
assert lc._kill_proc_tree is not lc._kill_proc_tree or True       # 同对象自比 + or True
assert argv[:2] == ["gateway", "run"][:0] or True                # 右侧是空列表切片，等式本身恒真
assert all(... for f in res["auto_failed"]) or True
assert new.samples[0]["args"] == old_p.samples[0]["args"] or True  # ← 删掉 or True 后立刻红
```

**最后那条最有说服力**：删掉 `or True` 后用例立刻失败，暴露的是一个 fixture 不一致（新骨架写 `evals/inputs/nums.json`、旧骨架写 `inputs/nums.json`，所谓「两种骨架等价」的前提被自己的 fixture 破坏了）。⇒ **恒真断言不是「多余的保险」，它长期盖着真问题。**

## 二、三圈重合：改动范围 = 复检范围 = 守卫范围 ⇒ 假绿

P0-02 首轮的完整假绿链（三层完全重合，任一层宽一点就能抓到）：
1. **改动范围** = 登记册点名的 12 个技能；
2. **复检范围** = 同样那 12 个（「残留 = 0」就是这么得出的）；
3. **守卫范围** = 也只覆盖那 12 个技能，而且那行守卫末尾还有 `or True`。

⇒ 三层同时收窄，结果「改了 12 个、查了 12 个、守卫守 12 个」全绿交付。**独立检验换个范围一扫，全仓还有 32 处**，其中 `experiment-bridge` 的 `open('CLAUDE.md')` 在 `except` 里静默回落 pdf —— 正是这条 P0 的原句现象（Word 论文缺主结果表）。

## How to apply

1. **写完断言后用变异反证**：把被测缺陷注回去，断言**必须红**。不红就是恒真（或判据没锚在焦点上）。
2. **新增/修改守卫时同时写「守卫的守卫」**：一条用例专门验证「判据正则/判据函数能抓到已知坏形态」，并配反向用例防误报。否则守卫自己也可能空转。
3. **复检范围必须由「机制」定义，不由「我改了哪些」定义**：例如「全仓 `grep -rn` 该模式的**所有**命中」而不是「我改过的那 N 个文件」。改动范围是最不可信的边界——它恰好等于我认知的边界。
4. **全仓扫描守卫要排除自身文档**：本仓新守卫用 `tokenize` 只取真实代码 token（`STRING`/`COMMENT` 不进流），否则守卫会抓到 docstring 里写的示例代码 = 假红。
5. 汇报口径：**「残留 = 0」必须附扫描命令与范围**；只说数字不附命令，等于让读者替你猜边界。

## 三、自注入前提与裸恒真（2026-11-04 zcodepro 全量审计实测）

两种新形态，同属「判据不可能失败」：
- **裸 `assert(true, 'xxx present')`**：提取了被测函数体却没有任何断言使用它，PASS 照打——该补丁零覆盖。
- **自注入前提**：测试声称「产物若误删常量声明会抛 ReferenceError」，但常量是测试自己注入 vm 的硬编码串——
  产物里删没删永远测不出。修法：前提（常量/绑定）必须**从产物自身提取**，提取不到直接红；
  桩要真回调（setTimeout 桩不回调 = 只测同步段，异步路径零覆盖）。

**How to apply**：产物级测试三问——断言用的是被测对象吗？前提来自产物还是测试自带？异步路径真的跑了吗？
任何一问答错就是假绿。变异反证同样适用：把缺陷注回去必须红。

**检索症状词**：assert(true)、自注入常量、桩不回调、or True、恒真、断言空转、假绿、残留 0、复检范围、守卫没抓到。

**同族**：[[guard-must-cover-the-changed-layer]]（跨层守卫=没有守卫）、[[guard-criteria-anchored-to-spelling-always-escape]]（锚写法被绕）、[[test-scope-must-be-pinned-by-index-not-walk]]（扫描范围/前提/断言三类假单）、[[silent-continue-masks-lost-check-coverage]]（continue 掉缺项）、[[measurement-and-sampling]]（测试抓到错≠机制在生效）。

## 2026-11-15 补：用户阈值不能被内部更短宽限窗否决（zcodepro idle reclaim 误杀）

用户配置「15 分钟空闲回收」，但 host busy 补丁内部用 2 分钟 `session/event` 通知宽限判断忙闲。
长回合没有稳定通知时，15 分钟定时器仍把在途 Agent 杀掉，表面看「配置是 15 分钟」，
实际判据是 2 分钟。这是自圈复检之外的新形态：**测试只证明当前启发式按设计跑，
没证明用户给定的阈值/语义真的决定行为**。

How to apply：
1. 把用户配置、内部宽限窗、运行态真值分层写清；短窗口只能优化，不能否决长阈值语义。
2. 回收/停止/清理类判据必须查权威在途状态（DB/运行时 activeTurn/tool/presence），通知桥只作补充。
3. 验收用例必须覆盖「配置阈值内无通知但仍在跑」和「真闲才回收」两种，不能只测通知窗口。
4. 上游功能页的另一条 release 链路不等于本地 idle 修复；逐符号定位后再决定照抄还是自补。

