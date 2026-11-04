---
name: react-node-reuse-vs-imperative-dom
description: React 复用同一个 DOM 节点、只改 props/id 时不会重建节点；挂在容器里的原生 DOM 表单若用「节点上的一次性布尔」当挂载守卫，切视图后内容不重渲染
type: pitfall
source: zcodepro（2026-10-25 ZCode v28 设置页分区串台）
date: 2026-10-25
verified: 2026-10-25
topic: browser, diagnosis, verification
---

**事故**：内容路由是三个同构 `div`（id 分别为 `zsm-notify-settings` / `zsm-autocont-settings` /
`zsm-advanced-settings`），三个原生 DOM 表单各自用 MutationObserver 挂载：

```js
function mount() {
  var root = D.getElementById(ROOT);
  if (!root || root.__zsmReady || busy) return;   // ← 一次性守卫
  ...
  root.__zsmReady = 1;
}
```

React 认为三者类型相同、位置相同，于是**复用同一个 DOM 节点**，切分区只改 `id` 属性。
节点上的 `__zsmReady` 一直在 ⇒ 换分区后 mount 立刻 return ⇒ **新分区一直显示旧分区的内容**。
用户描述为「切换不对」，但导航高亮、路由状态都正常，极难从截图推断。

**Why**：
1. React 的 DOM diff 只保证「节点能复用就复用」，不保证「换 key/props 就重建」；
2. React 改 `id` 是**属性变更**；`MutationObserver` 只配 `childList` 收不到，必须加
   `attributes: true, attributeFilter: ['id']`；
3. 异步读取数据回来时，节点可能已经被另一个视图接管，写入就会串台。

**How to apply**：
1. 挂在 React 容器里的 IIFE，守卫要绑「**当前挂的是哪个视图**」而不是「挂过没有」：
   `if (root.__owner === ROOT) return; root.__owner = ROOT;`；
2. 观察器加 `attributes + attributeFilter:['id']`（或 `data-*`），别只盯着 childList；
3. 异步回填前再校验一次 `root.id === ROOT`，慢回包不许覆写别人的内容；
4. 事件监听绑在容器上时用一次性标志（`root.__bound`），否则每次切视图都会叠加一份；
5. 取证套路：给节点打 `__probe` 标记 → 切视图 → 看标记是否出现在新 id 的节点上；
   跑一个 N×N 切换矩阵，逐格记录内容签名，能一眼看出「只有第一次生效」。

关联 [[css-selector-list-pseudo-element-leak]]
