---
name: android-adb-ime-and-coordinate-gotchas
description: adb 操作安卓的两类静默坑——① `input text` 走中文 IME 会把 ASCII 拼成汉字（禁用 IME 后 input text 又不生效，因无输入连接）；② `input tap` 用显示坐标，截图文件实际像素才是真坐标（Read 会缩放显示），须用像素分析定位而非目测
type: pitfall
source: default 会话 2026-11-08（vivo V2134A Android 13 + 搜狗/百度 IME，实测）
date: 2026-11-08
verified: 2026-11-08
topic: toolchain
---

**经验**：

1. **`adb shell input text` 不是「直接输入 ASCII」**：它发的是 KeyEvent，会经过当前 IME。中文 IME（搜狗/百度/vivo）处于中文模式时，会把 `https://api.longcat.chat/openai` 这类 ASCII 拼成汉字（实测字段里出现「还天天平时：、、哦那个擦插头、」）。`adb shell ime disable <id>` 禁用 IME 后，`input text` 又常常不生效——Flutter 文本框失去 IME 输入连接，键事件不被提交为文本。
   - 可行做法：用 IME 的英文模式；或用应用自带的「粘贴」按钮（如 dsh-go 的 API Key 字段有「粘贴」）；或把文本放进剪贴板再触发粘贴。
   - 禁用/启用 IME 会破坏当前输入连接，需重启 Activity（home + 重新拉起）才恢复键盘。

2. **`input tap` 的坐标是屏幕物理坐标**，而截图工具（Read）会把 PNG 缩小显示。若按显示尺寸估算坐标再乘比例，容易偏几十到几百像素。实测截图文件 1080×2376，某按钮文字实际在 y≈2258，按显示尺寸估算是 2048，差 200+。
   - 可行做法：对**原始 PNG** 做像素分析（PIL 扫颜色边界）定位控件边框，按文件实际像素坐标点击；不要凭显示画面目测。

3. **辅助定位**：`dumpsys input_method | grep mInputShown` 看键盘是否真的弹出（`true`/`false`）；`ime list -s` 列可用输入法；`uiautomator dump` 对 Flutter 界面常取不到文本（无障碍语义未开），不要依赖它。

**Why**：中文 IME 会把 ASCII 当拼音合成，且禁用 IME 会断输入连接；坐标错位导致点不到控件，两者都静默（不报错），容易误判成「按钮没反应」。

**How to apply**：adb 往安卓文本框写英文/URL/key 时，优先用 IME 英文模式或剪贴板粘贴；点击前用 PIL 对原图做像素边界分析定位，再用 `input tap`；键盘没弹先查 `mInputShown`。相关：[[dsh-go-config-paths-and-credentials]]。