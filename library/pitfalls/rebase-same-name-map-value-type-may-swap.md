---
name: rebase-same-name-map-value-type-may-swap
description: 跨基线复锚时，同一名字的 Map 可能从「存对象」变成「存字符串」；只核对名字与锚点命中数会漏掉这类语义互换，补丁静默失效
type: pitfall
topic: verification
source: zcodepro
date: 2026-11-05
verified: 2026-11-05
---

**经验**：跨基线复锚时，**必须确认所读 Map/变量的 value 类型**（对象？字符串？数字？），不能只核对「名字还在、锚点命中 1 次」。同一套 minified 名字在不同构建里角色可能互换，读错不会报错，只会让判据**永久为假**——补丁看起来在，实际是死代码。

**Why**：真案例——ZCode 桌面端的 v4 订阅路由表。2330 里 `ne` 存「路由键 → 订阅对象」，我方 `__zcodeWsdBusy` 遍历 `ne.values()` 取 `.workspaceKey` 判工作区是否忙，工作正常。rebase 到 1012 后地图角色互换：`ne` 变成「所有权键 → 路由键」的**字符串 map**，订阅对象挪到了 `re`（`re.set(routeKey, pe)`）。我方补丁仍遍历 `ne.values()`，取到的 `.workspaceKey` 永远是 `undefined` → 判据恒 false → 空闲回收不再避开有会话的工作区，把用户一条跑了 2 分钟的 Bash 命令连同 agent 进程一起杀掉。**而且这类错误 `node --check` 与锚点断言都发现不了**，只有真实语义测试能。

**How to apply**：
1. 复锚凡是「读 Map 的 value 再取字段」的补丁，先在基线里找到该 Map 的**写入点**（`X.set(k, v)`），确认 `v` 是对象还是字符串/数字。同基线里往往有一处 `for (const x of thatMap.values()) x.someField` 的反例可直接引用为证。
2. 给这类判据配一条**真实数据测试**：把基线形状的 Map 灌进去（对象 map 与字符串 map 两种都灌），断言判据分别为 true/false。只断言「函数存在」等于没测。
3. 症状特征：某个治理/门禁**从不生效**（或永远生效）时，优先怀疑「读的对象不对」，而不是阈值不对——参考 KB `no-assertion-without-measurement`。
4. 与 KB `guard-installed-by-the-mechanism-it-fixes` 一起看：那条讲「钩子挂在可能失效的机制上」，这条讲「钩子读的数据结构换了角色」，都属于「补丁在但没作用」。

关联 [[idle-reclaim-criteria-must-be-work-not-attention]]、[[guard-installed-by-the-mechanism-it-fixes]]。
