---
name: injected-ui-feature-failure-check-credential-plumbing-first
description: 注入式 UI 增强失效时先查「取凭据/取上下文」那段而不是引擎；判据是桩 DOM 跑真块 A/B；主 chunk grep 不到 testid ≠ 不存在
type: pitfall
topic: verification
source: zcode-mod
date: 2026-10-19
verified: 2026-10-19
---

**经验**：往打包 Electron 应用（app.asar）里注入的 UI 增强功能「用不了」时，**默认先怀疑"取凭据/取上下文/取选中项"那一段，而不是功能引擎**。这类块往往引擎写得很全（候选地址推导、多种鉴权头、宽容解析、重试），却把「当前是哪个对象 / API Key 从哪来」压在**反查框架内部结构**（React fiber 找 service、读 context 值）上，且**没有兜底**：反查不中就在 gate 处静默 return —— 用户看到的是「按钮点了没反应 / 提示先去填 Key / 搜不到模型」。再叠上「整块不打任何日志」，就变成查不出原因的黑洞。

**Why**：真案例——ZCode「自动搜索所有模型」失效。逐段实测后：扫描引擎直打真实中转站全部 200（24/471/16/2 个模型）；三个版本的包里锚点 testid 都在；preload 桥与主进程 handler 也都在；**病灶就是「取凭据只靠 React fiber 反查、API Key 无兜底」**——反查不中时弹窗停在「请先填写 API Key」根本不发起扫描。桩 DOM A/B 一眼看穿：旧块 scan 调用 **0 次**，修复后 **1 次**。查了很久没定位，就是因为一直在读引擎和锚点，没把「gate 之前的那几行」当成第一嫌疑。

**How to apply**：
1. **判据用桩 DOM 跑真块**：写 ~200 行最小 DOM（`querySelector(All)`/`createElement`/`insertBefore`/`removeChild`/`MutationObserver`，`innerHTML` 赋值时从字符串里抽 `data-*` 造子节点），把**真实代码块**跑起来，对照「旧块 vs 修复块」在同一场景下的**调用次数**。⚠️ 选择器匹配器**必须支持复合属性选择器** `[a="1"][b^="2"]`（导航项的选中态就是这种），否则会误判成"按钮根本没挂"。
2. **grep 不到 ≠ 不存在**：打包应用的设置类页面通常是**独立 lazy chunk**，且常量被压缩成 `ei`/`zre`/`dr` 之类的短变量名——主 chunk 里 grep 全文都会 0 命中。要在**整个 renderer 资源树**里搜，并且**刨掉自家注入块再数**（否则数到的只是自己写进去的字符串）。压缩常量要顺 export/import 别名表还原（`export{X as Y}` + `import{Y as Z}` 复合出「本地名 → 原常量」）。
3. **修法优先级**：① 首选**复用已桥接的 IPC 通道做多路复用**（把 `command:"log"/"add"/"scan"` 塞进已有入参），避免改 preload、避免扩 contextBridge 白名单；② 主进程**按 id 从配置文件取明文凭据**做兜底，比渲染层任何反查都稳；③ 兜底写配置**只追加数组字段**，不碰校验更严的子结构（zod 可能整份拒绝）；④ 先按页面凭据扫一轮，失败再用配置凭据复扫一轮（覆盖"刚改没保存"与"反查不中"两种情形）。
4. **注入块必须自带落盘日志**（打包版渲染层 console 没有出口），每步一行：取凭据来源/第一轮/第二轮/写入。没有它，下一次还是黑洞。

关联 [[defect-localization-methodology]]、[[electron-renderer-heap-oom-governance]]、[[frontend-bundle-recovery-without-sourcemap]]、[[no-assertion-without-measurement]]。 [[config-load-failure-check-file-refs-and-schema]]、[[run-level-failure-text-is-not-sub-operation-failure]]、[[multi-line-log-attribution-use-baseurl-not-model]]、[[model-capability-verdict-needs-official-docs-not-probes]]。
