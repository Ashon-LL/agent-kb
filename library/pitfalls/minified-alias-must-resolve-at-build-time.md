---
name: minified-alias-must-resolve-at-build-time
description: 向 minified 产物注入代码引用宿主绑定时，别名必须构建期从 import/定义动态提取并断言；硬编码别名+空 catch 会把错绑变成静默行为降级（reveal 变默认程序打开）
type: pitfall
topic: reverse-engineering
source: zcodepro（2026-11-04 reveal 误用默认程序事故）
date: 2026-11-04
verified: 2026-11-04
---

**经验**：补丁注入代码若要调用宿主模块的绑定（如 electron shell），别名必须在构建期
从源码动态提取（正则 `import{shell as (\w+)}from"electron"` 取捕获组）并断言命中；
禁止照抄上一版基线的别名。

**Why**：zcodepro 的 reveal 修复硬编码 `Nf.showItemInFolder`，但 2330 基线里 `Nf` 是
编辑器列表函数、shell 另有别名。调用抛 TypeError，被注入点自带的空 `catch{}` 吞掉，
静默落回 `shell.openPath`——「在资源管理器中打开」变成「用默认程序打开」，全链测试绿
（marker 在、语法过），只有用户点击才暴露。

**How to apply**：
1. 注入代码里的宿主绑定一律用构建期捕获的别名模板（`{shell}` 占位 + format）；
2. 提取正则断言恰好命中；同一文件可能有多个 shell import 别名，任取其一即可但必须真是 shell；
3. 空 catch 兜底路径要审查：兜底行为若与意图相反（openPath vs showItemInFolder），
   等于把错误藏成错误行为——兜底也应保持语义或响亮失败；
4. 行为级验收不能只查 marker：对「点击后到底调了谁」要有产物级断言（如 win32 分支
   必须 showItemInFolder）。

**检索症状词**：minified 别名、硬编码绑定、空 catch 吞错、reveal 变打开、showItemInFolder、openPath。
