---
name: electron-renderer-heap-oom-governance
description: Electron 渲染进程 JS 堆耗尽的判读与治理——pointer compression 4GB cage 让 --max-old-space-size 无效；靠 v8-oom 转储注解定位线程、压力驱动回收+优雅 reload+崩溃自恢复做兜底；顺带记录 tsc -b 污染源码树与 bundle 默认目标两个构建坑
type: tool
source: zcode 桌面端内存卡退调查（2026-10-15，本机 zai-org/ZCode 源码 + crashpad 转储 + 60s 内存日志实测）
date: 2026-10-15
verified: 2026-10-15
topic: zcode
---

**经验**：Electron 应用跑数小时后「整个应用凭空消失」，先按 renderer V8 堆耗尽处理，且要认清两件事。

**一、`--max-old-space-size` 基本无用。** 崩溃转储的 `v8-oom-*` 注解里若有
`main-cage-size=4096.00MB` + `main-cage-last-alloc-status=ran out of reservation` +
`largest-free-region` 只剩个位数 MB，说明 V8 开了 pointer compression，整个堆被关在一只 **4GB cage**
内；heap total 已到 3.4GB，调参最多多几十 MB。真正可做的只有三件：**别再让堆涨上去 / 到顶前优雅重载 /
真崩了自动恢复**。

**二、先看转储注解，别先读代码。** `%USERPROFILE%\.zcode\v2\crash\archive\*.dmp.json` 的
`v8OomSummary` 直接给出 `oomKind` / `isMainIsolate` / `old_space` 用量与容量 / `lo_space` /
`memoryAllocator` / 最后一次 GC 报文 / 截断的 `stackHead`。判据：
`last resort` + `Mark-Compact (reduce) X -> X`（回收量为 0）= 全是**仍被引用的活对象**，即真泄漏，
不是「垃圾没来得及收」；`stackHead` 只是**压垮时的最后一根稻草**（本次是 RPC 端口消息校验函数里的
`Object.keys`），**崩溃点 ≠ 泄漏点**，不要顺着栈去改那个函数。

**三、用产品自带的埋点做排除法，别加新埋点。** 若应用已有「每 60s 落一行的角色内存 + 领域计数器」日志，
先把时间序列按进程拉出来，看 `heapUsedKb` 的斜率，再找**同一行里跟着涨的计数器**；
更有效的是跨进程对照：本次两个 renderer 一个 3.3GB、另一个 207MB，而 `shiki.tokensCache` 分别 3 与 0、
`projection.rows` 后者反而更多 —— **同样的计数器、差 17 倍的堆占用，直接把已埋点的那几张表全排除**，
省掉一轮白修。同 [[measurement-must-verify-control-group]] 的道理：对照组要选「本来就正常的同类状态」。

**四、兜底治理的可落地形状**（本次实现，纯主进程、零协议改动）：
- app ready 前 `app.commandLine.appendSwitch("js-flags", "--expose-gc")`（只能早期设，仿
  `desktopEarly*Bootstrap` 副作用模块）。注意 `appendSwitch` 在 `CommandLine` 上，**不在 `App` 上**
  ——main 侧拿的是 `app.commandLine`，类型上别把它当 `App` 传。
- 复用既有的 60s heap 样本通道加**只读观察者**，不要另注册一个 `ipcMain` 监听器：这类通道常带
  `removeAllListeners` 语义，第二个监听器会被下一次注册静默清掉。
- 阈值三档：**低档抓取证堆快照**（经 `webContents.debugger` + `HeapProfiler.takeHeapSnapshot`，
  流式写盘），**软档** `executeJavaScript` 调 renderer 注册的释放钩子 + `globalThis.gc()`，
  **硬档** 再 `webContents.reload()`。快照务必放在**低档**：3GB 堆上抓快照自身要近乎等量临时内存，
  很可能把进程直接推死 —— 想拿 retaining path 就得趁余量充足时抓。
- reload 通常比想象的安全：Electron 主窗口 reload 后 host/agent 子进程是存活的，`dom-ready` 里
  补挂一条新 RPC MessagePort 即可，会话不丢；关键是确认目标应用有没有这条重挂逻辑，有才敢用。
- `render-process-gone`（排除 `clean-exit`）自动 reload，并加「N 分钟内 M 次则熔断」防重载循环。

**五、两个构建坑（Windows 交叉/本地打包）**：
- `tsc -b <某个 emits-in-place 的 tsconfig>` 会把 `.js/.d.ts` **直接写进 `src/`**，
  在仓库里留下一堆非故意的改动（`git status` 才看得见），必须 `git checkout` + 删掉再打包，
  否则「打包的源码树 ≠ 你审过的源码树」。
- electron-builder 类打包脚本常把**目标平台默认值写成内部发版平台**（本次 `DEFAULT_TARGET_OS=mac`），
  在 Windows 上不显式传 `--os win --arch x64` 会直接以「Build for macOS is supported only on macOS」失败。

**How to apply**：遇 Electron 长时运行掉线/消失 → 先读 `v8-oom` 注解判 cage 与真泄漏 → 用产品自带
计数器做跨进程对照排除 → 实现「早期 flags + 低档抓快照 + 软档释放&GC + 硬档 reload + 崩溃自恢复」。
相关 [[zcode-platform-verified-facts]]、[[electron-builder-nsis-silent-install-fallback]]。
