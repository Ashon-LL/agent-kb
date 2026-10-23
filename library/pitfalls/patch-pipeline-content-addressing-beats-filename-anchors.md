---
name: patch-pipeline-content-addressing-beats-filename-anchors
description: 给无源码的成品包打补丁，锚点必须按「代码形状/字节 marker」内容寻址而不是文件名或变量名；配套要求是桩测试的动态名解析，否则版本升级时测试会静默失真
type: pitfall
topic: verification
source: zcode-mod
date: 2026-10-23
verified: 2026-10-23
---

**经验**：长期给「无源码的成品包」（Electron `app.asar`、压缩混淆后的 bundle）打补丁，**锚点必须内容寻址**——用代码形状、唯一字符串、字节 marker 定位，**绝不写死文件名和压缩变量名**。变量名在每个版本都会全换（实测三代里 renderer 主块 `styles-BXiGbfT-`→`styles-n-UNIiNg`→`styles-D3JcQHr-`，行池类 `xYe`→`sde`→`nde`，一批函数名整体漂移），写死等于每次升级全部返工。内容寻址的收益可以直接量化：某个新版本 27,995 个条目里只有 1 处针脚失配，其余 8 个补丁零改动直接出包。

**Why**：两个真教训叠出来的。① 内容寻址的**反面**：曾用文件名 + 具体函数名（`function rT(e){let t=new Uf(e),`）定位「管理器工厂」，新版本把它重构成 `function PT(e){let t=new im(e),`（同一个类改了 import 别名）⇒ 直接失配，必须新写一个适配模块。② 更要命的是**桩测试写死被验代码的压缩名**：单测的桩注入格式化函数名 `MAt`，新版本改名成 `KOt` ⇒ then 回调 `ReferenceError` ⇒ state 恒为 null ⇒ **17 个 FAIL，但补丁本身完全正确**（grep 确认改写后的代码在位）。失败长得像产品缺陷，实际是测试桩过期——如果当时信了测试，就会去"修"一个没坏的东西，或者更糟：把测试改成断言那个错误行为。

**How to apply**：
1. **锚点用形状，不用名字**：正则锚「调用点 + 参数形态 + 相邻的唯一字符串」，例如 `(0,Q\.useEffect\)\(\(\)=>\{if\(\w+\(null\),\w+\(!1\),!\w+\|\|!\w+\)return;` —— 把会漂移的部分留给 `\w+`，把稳定的部分（调用序列、字面量、日志文案）写死。锚点命中数必须 assert 等于 1，≠1 直接 raise，绝不静默跳过（宁可用显式 note 记「**跳过**(!!!)」让人看见）。
2. **需要引用原名时，用正则取回而不是复制**：给函数挂调试名 `i(ot,"rememberV4SubscriptionRoute")` 后要追加注入，写成 `re.compile(r'i\((\w+),"rememberV4SubscriptionRoute";\)')` 取回 `ot` 再拼——直接写死 `it` 会把别人的调试名改掉（功能无碍，但排查时对不上号）。
3. **桩测试必须动态解析绑定名**：从被测片段本身正则抽出各压缩名（`SU/SE/PO/SV/FMT/LG`）再注入沙箱，别在桩里写死。这样版本改名后测试自动跟上。判据：**任何「测试失败」先怀疑桩，再去怀疑产品**——尤其当失败集中在某个具体函数的输出上时。
4. **注入点的查找方式也要防漂移**：用 `text.find('/*zsm:')` 找「第一个自家标记」当插入点是稳的（自家标记前缀不变），但要注意新版本可能在标记前加了字节（实测 +1 字节换行）——插入点偏移不影响，但别把偏移量算进断言。
5. **每轮都跑完整校验电池**：entry-diff（恰好 N 个条目变化）、integrity 重算、`node --check`、roundtrip 逐字节一致、单测、沙盘演练、哈希负测试。纯重新打包的版本（只改版本号 JSON）也应该零适配直接出包——如果它没做到，说明锚点里混进了会漂移的东西。

关联 [[injected-ui-feature-failure-check-credential-plumbing-first]]、[[no-assertion-without-measurement]]、[[measurement-must-verify-control-group]]、[[user-given-equalities-must-stay-equal]]。
