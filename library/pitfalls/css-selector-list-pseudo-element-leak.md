---
name: css-selector-list-pseudo-element-leak
description: 逗号选择器列表里只给最后一条加伪类/伪元素时，Chromium 会把该声明应用到其余选择器命中的元素本身；症状是控件突然变成小圆点、absolute、飞出布局
type: pitfall
source: zcodepro（2026-10-25 ZCode v27→v28 设置页开关显示）
date: 2026-10-25
verified: 2026-10-25
topic: browser, diagnosis, verification
---

**事故**：给三处设置分区统一画药丸开关，CSS 写成

```css
#a input[type=checkbox],
#b input[type=checkbox],
#c input[type=checkbox]::after { width:14px; height:14px; border-radius:50%; background:#fff; position:absolute }
```

结果只有 `#c` 正常，`#a/#b` 的 checkbox 被画成 **14×14 白点 + `position:absolute` + `opacity:.5`**，
全部叠到同一个坐标、脱离文档流、在深色背景上几乎看不见。用户看到的是「开关没了 / 只剩一个小圆点」。

**Why**：选择器列表里只要有一条带伪元素，Chromium 就把这条规则按「伪元素规则」处理，
其余选择器命中的**元素本身**会拿到这些声明。隔离实验（同页面三个 input）复现：

| 选择器 | 结果 |
| --- | --- |
| `.t1 input`（列表第 1 条） | 40×20、`absolute`、红底 ← 被套上了 `::after` 的声明 |
| `.t2 input`（列表第 2 条） | 同上 |
| `.t3 input::after`（最后一条） | 13×13、`static`、透明 ← 正常 |

**How to apply**：
1. 伪类/伪元素后缀**逐条展开**：`list.map(sel => sel + suffix).join(',')`，绝不写「列表 + 末尾单个 `::after`」；
2. 一旦发现「控件莫名缩小/变成圆点/脱离布局」，先做**删除对照**：把自己的 `<style>` 摘掉再看基线。
   `appearance` 生效但 `width/background` 不生效，通常意味着声明被套到了错误的目标（元素 vs 伪元素）；
3. 静态门禁：遍历生成的 CSS 规则，若某条规则的选择器列表里只有**部分**成员带 `::after`/`:checked`/`:disabled`，直接失败；
4. 用 `getComputedStyle(el)` 与 `getComputedStyle(el,'::after')` 分别取值，能立刻区分「元素被污染」和「伪元素没画出来」；
5. 注入第三方表单样式时优先用 token 变量（`currentColor` / 主题变量）而不是写死颜色，避免深/浅色主题下又出现「看不见」。

关联 [[react-node-reuse-vs-imperative-dom]]
