---
name: periodically-overwritten-state-file-cannot-be-hand-edited
description: 有进程在周期性全量重写某个状态文件时，手改那个文件既会被冲掉、也不影响行为——权威状态在内存里；判据是隔几秒采样 mtime，修法只能走它自己的接口
type: pitfall
source: APIShow/WorkBuddy 账号池（2026-09-21）：state.json 每 5 秒被上位机全量覆盖，想让账号停用必须调 /admin 接口而非改文件
date: 2026-09-21
verified: 2026-09-21
topic: methodology
---

**经验**：**有进程在周期性全量重写某个状态文件时，手改那个文件是无效操作**——双重无效：① 下一次写回会把你的改动**覆盖掉**；② 就算侥幸没被覆盖，**程序读的是内存态，不是文件**，行为不会变。这类系统的状态**只能通过它自己的接口改**。

**Why**：2026-09-21 要让 WorkBuddy 账号池里的一个账号「摘掉流量但保留签到保活」。当时的候选做法之一是直接改 `/opt/workbuddy2api/data/state.json`（里面有每个账号的 `manual_disabled` 字段，看起来改一下就行）。**实测否掉了这条路**：

```
stat -c %y state.json   # 隔 4 秒采样 3 次
02:57:46.634  1875 bytes
02:57:51.634  1875 bytes   ← mtime 每 5 秒推进，大小不变 = 周期性全量重写
02:57:51.634  1875 bytes
```

源码也印证：持久化是内存池的**快照写出**（flusher 5s 一把），**加载只在启动时**。所以手改必然被下一次 flusher 覆盖，而运行中的选号逻辑读的是 `p.byUID[uid].manualDisabled` 内存字段。**该系统的状态权威在内存，文件只是它的落盘镜像。**

**How to apply**：

1. **判据（10 秒内可判）**：隔几秒采样两三次 `stat -c "%y %s" <file>`。mtime 持续推进而大小基本不变 ⇒ **有进程在周期性重写**，手改无效。
2. **再加一层确认**：`grep` 该文件在源码里的**写入方**与**加载方**。若写入是周期任务/定时刷盘、加载只在**启动时**，则**运行期内存是权威**——改文件需要重启才可能生效，且重启前后都可能被覆盖。
3. **正解是找它的接口**：`grep -rnE '"(GET|POST|PUT|PATCH|DELETE) /' <源码>` 枚举全部路由，找**语义匹配**的那个（注意有些接口**默认关闭**，如 `admin.enabled=false`，要先把开关打开）。
4. **⛔ 别用"改文件＋重启"当兜底**：即使重启后能读到你改的值，也存在竞态（重启窗口里旧进程可能再刷一次盘）；而**有正规接口时这条路根本不必要**。
5. **验证要落到行为**：改完别只看状态字段变没变，要看**目标行为是否真的发生**（本例：用近 3 分钟的请求日志确认流量确实只落在另一个账号上）。
6. **顺带区分两类"改文件无效"**（容易混）：① 本文这类——**文件被覆盖 / 内存才是权威**；② [[file-change-not-code-running]] 那类——**改了文件但新代码没跑起来**（需重启进程）。判据不同，别拿一条解释另一条。

**相邻**：同概念的多个实现语义不同见 [[same-concept-multiple-implementations-pick-semantics]]；改 DB 列要按代码期望的类型写见 [[third-party-db-columns-typed-by-reading-code]]。

关联 [[persisting-files-also-requires-exempting-cleanup]]。
