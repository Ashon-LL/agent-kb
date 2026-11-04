---
name: computer-use-windows-action-timing
description: Computer Use（Windows）动作按时延分档：系统热键须 holdSeconds≈0.6s；快速 typeText 在 Qt 编辑器会把连字符变双并吞后一字符（≥50ms 间隔或 paste 可解）；面板动画中截图报 geometry changed、打开的搜索面板只回白帧；后台键盘输入会显式拒发
type: tool
source: zcode改造 CUA 复测矩阵（2026-11-01）
date: 2026-11-01
verified: 2026-11-01
topic: toolchain,windows
---

## 经验

Windows 上的 Computer Use（computer-use 0.6.5）动作要按"时延档位"给参数，不要一律瞬发：

1. **系统组合键必须带 holdSeconds**（实测 0.6s）。`alt+tab` 瞬发 3/3 不切换窗口；`holdSeconds:0.6` 2/2 成功（计算器→画图→计算器）。单键 `super`、`super+e` 瞬发正常。
2. **快速整串 typeText 在 Qt 编辑器会坏**（Notepad--）：`-` 变 `--` 并吞掉紧随的一个字符，总长度不变。同一 6 行块连续 2 次结果逐字符相同：`2026-11-01`→`2026--11--1`、`a-b-c`→`a----`、`ZCode-v29.14-PATCH`→`ZCode--29.14--ATCH`。逐字符 + 50/120/300ms 间隔 3/3 正确；`paste()` 39 字符含 4 个连字符 1/1 正确；WinUI（资源管理器地址栏）快速 typeText 2/2 正确。
3. **元素 click、setValue、paste 即时调用即可**，无需延迟。
4. **截图两种失效**：目标面板正在关闭/动画中报 `selected panel identity, geometry or relationship changed during capture`（2/2）；搜索面板打开后 4/4 返回"成功"，但都是同一张 15,495 B 纯白帧（WebView 型 CoreWindow 截不到内容）。普通窗口（计算器/资源管理器/记事本--）截图正常有内容。
5. **后台应用键盘输入要求前台激活**：绑定后台 ZCode 发 `alt+tab` 直接 `activation_failed`、`action_sent:false`；元素点击可在后台生效。
6. **元素索引随树变化失效**（`element index N no longer refers ...`），每次观察后重新取索引；搜索流程要先真正打开面板（`super` 键）再对最新 textfield 索引输入，`setValue` 与 `typeText` 都可用，结果行点击与回车都能启动应用（4 条路径全通）。
7. **UWP 打包应用按 pid 绑定报 no UIA tree**；须按 Start 菜单显示名绑定（计算器→ApplicationFrameHost）。同一 host 挂同名多窗口时按名解析歧义，且 `getApp` 不支持 `window_id` 绑定（只认 name/bundle_id/pid）。

## Why

瞬发不是"慢"而是"丢"：热键被 shell 忽略、Qt 编辑器把 `-` 插成两个并吞后一字符，看起来像应用或工具随机故障；搜索面板若未真正打开，`setValue` 会把值写进框却不触发搜索，误判为"结果面板为空、回车无效"；动画中截图报错、打开后回白帧，会被当成页面空白；索引用旧值会点到别的元素。

## How to apply

写 CUA 脚本或手工验证时：热键加 `{holdSeconds:0.6}`；导入文本优先 `paste`，逐字键入留 ≥50ms；只有读/点/赋值可即时。观察→取索引→动作在同一轮完成，别跨观察复用索引。截图前等稳定；对 WebView/CoreWindow 面板不要依赖像素，改读 AX 树。搜索类流程先 `super` 打开，再用最新索引输入，并用结果行或 Enter 验证启动。
