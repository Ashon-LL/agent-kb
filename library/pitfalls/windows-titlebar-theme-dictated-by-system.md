---
name: windows-titlebar-theme-dictated-by-system
description: Windows 11 未自绘的窗口标题栏外观由系统设置 SystemUsesLightTheme 支配；DwmSetWindowAttribute 可能「设了值但不渲染」
type: pitfall
source: Windows 11 标题栏主题实测（2026-09-21）
date: 2026-09-21
verified: 2026-09-21
topic: windows

---

# Windows：标题栏明暗由系统设置支配，应用改不动

## 事实

Windows 11 上，**未自绘**（即 `decorations: true`）的窗口标题栏外观由**系统设置**支配：

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
  SystemUsesLightTheme = 0/1   ← 窗口标题栏跟这个
  AppsUseLightTheme     = 0/1   ← 应用内容跟这个
  EnableTransparency    = 0/1   ← 透明效果（另关一件事：见下）
```

应用通过 `DwmSetWindowAttribute(DWMWA_USE_IMMERSIVE_DARK_MODE)` 设的「深/浅」
**在部分 Windows 版本上不生效** —— 属性值写进去了，但系统不按它渲染。

## 实测证据（20260921，Windows 10.0.26200）

| 观测 | 结果 |
|---|---|
| 系统 `SystemUsesLightTheme` | `0`（深色） |
| 应用调 Tauri `setTheme('light')` 后查 DWM 属性 | `DWMWA_USE_IMMERSIVE_DARK_MODE = **0**`（值**写对了**）|
| 但标题栏实际渲染 | **仍是黑的** |
| 把系统切到浅色（随即还原） | **标题栏立刻变浅** ✅ |

⇒ 排除「API 没执行」与「权限不足」，确认是**系统优先**。

## 出路

**唯一可行方案 = 自绘标题栏**：
- `tauri.conf.json`：`"decorations": false`（去掉原生栏）
- 前端画一条自己的栏，颜色走**应用自己的 CSS 变量** ⇒ 天然跟随应用主题
- 代价：需自己实现拖拽 + 最小化/最大化/关闭 + 窗口圆角/边框

## 实现要点（实战）

1. **拖拽**：`data-tauri-drag-region` 属性**可用**（由 Tauri 的注入脚本处理，
   **不走 IPC**）。⛔ 按钮区域**不要**挂这个属性（挂了就点不动，点下去变拖窗口）。
2. **三按钮**：若 IPC 不可用（见 [[tauri-remote-url-has-no-ipc]]），
   走「前端 HTTP → 后端 → Rust」的通路。
3. **关闭语义**：若原应用是「关闭→隐藏到托盘」，自绘后必须**保持**
   （否则点 × 会杀掉后台任务）。**不要**去改原生 `CloseRequested` 分支，让新按钮调自己的隐藏命令。
4. **`decorations: false` 后窗口没有系统边框** ⇒ 靠底色与桌面区分会「糊在一起」，
   需补 1px 描边 + 阴影。
5. **圆角**：最大化时 Tauri 会移除圆角，布局要能适配。

## 附带：`EnableTransparency = 0` 会连带压低玻璃效果

同一注册表项下 `EnableTransparency = 0`（系统关「透明效果」）会让 Chromium 恒报
`prefers-reduced-transparency: reduce` ⇒ **应用里所有 CSS 玻璃效果被静默降级**。
实测症状：用户反馈「看不出玻璃效果」而代码全对。
⇒ 排查玻璃/模糊「没效果」时，**先查这个开关**，别一头扎进 CSS。

## 纪律

- 「应用主题」与「系统外壳主题」在 Windows 上是**两套设置**，别混为一谈。
- 排查标题栏问题：**DWM 属性查询 + 系统设置对照，两个都要看** ——
  单看一边会误判成「代码没执行」。
- ⛔ **临时改系统设置做对照实验时，备份必须写「改前」的值**
  （本次曾把「改后的值」误存为备份，还原时写错一次 —— 所幸旁证记录了原值）。
