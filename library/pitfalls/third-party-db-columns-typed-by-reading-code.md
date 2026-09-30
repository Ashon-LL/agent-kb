---
name: third-party-db-columns-typed-by-reading-code
description: 手工改第三方应用的 DB 前必须 grep 读该列的代码——类型/格式由代码决定不由 SQL 常识决定；同一列可逐行存不同类型而 ORM 按固定类型扫，一行不符即整表查询失败（列表全挂）；改完必须 typeof() 整表分布回读，且先用真实消费方验证
type: pitfall
source: APIShow/AstrBot v4.27.4（2026-09-18 updated_at 写成 int 崩 fromisoformat）；APIShow/New API rc.26（2026-09-19 channel_info 写成 TEXT 而其余 30 行是 BLOB，致渠道列表与选路全挂）
date: 2026-09-19
---

**经验**：SQLite 是弱类型，你写进去的任何类型它都收——**收得下不等于读得动**。第三方应用的列类型由其代码的读法决定，不由你的 SQL 常识决定。

**⚠️ 二次踩坑后的强化（2026-09-19）**：**同一列在不同行里可以是不同存储类型**（SQLite 逐行存类型），而 ORM 通常把列声明成固定类型（Go 的 `[]byte`、`json.RawMessage` 等）。**只要有一行类型不符，整个查询就抛错**——不是那一行取不到，是**列表接口全挂、依赖该表的选路也全挂**。本次表现：前端「获取渠道列表失败，请稍后重试」+ 所有走该渠道的模型调用「Failed to get available channel」。所以改完**必须做整表 `typeof()` 分布统计**，不能只看值对不对。

**Why**：本次把 `conversations.updated_at` 按 SQL 习惯写成 `int(time.time())`（Unix 秒），用户下一条消息就报 `fromisoformat: argument must be str`——应用是用 `datetime.fromisoformat(row["updated_at"])` 读的，SQLite 把 int 原样交出来，函数直接抛异常。表象是"我修完数据后应用坏了"，排查极易跑偏成"是不是删错了行"。同族坑：布尔列存 `0/1` vs `"true"`、JSON 列存字符串 vs 对象、枚举列存序号 vs 名字。

**同族二次实例（2026-09-19，影响面更大）**：改 New API 渠道表的 `channel_info`（JSON 列）时用 Python `str` 写入 → 存成 **TEXT**，而其余 30 行全是 **BLOB**（Go `[]byte`）。gorm 扫描即 `Scan error on column index 27, name "channel_info"` → **整个 `SELECT * FROM channels` 抛错** → 前端渠道列表打不开、`Failed to get available channel` 使该渠道所有模型请求失败。**修法**：以 `bytes` 写回（sqlite3 传 `bytes` 即 BLOB），或 `CAST(? AS BLOB)`。

**How to apply**：

1. **动手前** `grep -rn "<列名>" <应用源码>`，看它怎么读（`fromisoformat` / `json.loads` / `bool(...)` / 直接字符串比较），照着代码期望的格式写。
2. **⛔ 动手前还要查这个字段有没有已知坑**：`git log -S "<列名>"` 搜历史提交、翻项目文档。本次 `channel_info` 的 TEXT→BLOB 问题**项目里早已修过一次**（`48d55c9 fix: channel_info TEXT->BLOB 修复 b.ai ch118-123 定时任务报错`），我没查历史就动了同一字段，等于重犯。**一个字段被前人专门修过，就说明它脆**。
3. **最省事的格式来源**：在同表里 `SELECT` 一条**应用自己写的**行，抄它的格式与**存储类型**（本次时间列抄成 `'2026-09-17 13:25:37.899479'`；BLOB 案例则抄 `typeof()`）。
4. **改完立即回读类型，并做整表分布统计**：`SELECT typeof(<列>), COUNT(*) FROM <表> GROUP BY 1`——本次应为单一 `blob`；出现落单的 `text` 就是没改干净。改前先整库备份（`.bak-<日期>-<标签>`）。
5. **只改目标行/列**，别顺手 `UPDATE` 全表（会踩别人的列，尤其是它自己维护的时间戳/计数列）。
6. **验证必须用真实消费方**：用 Python 直读 DB **验证不了类型问题**（Python 对 TEXT/BLOB 都宽容，本次我的 verify 因此全绿却线上全挂）。要走应用自己的接口（列表 API / 渠道测试）或至少模拟它的类型期望。
7. 报告时把"我改了 DB"和"应用实测恢复正常"分开说——前者是动作，后者才是结果。

**相邻**：镜像内源码补丁的持久性边界见 [[container-image-source-patches-need-replay-script]]；验证必须走应用自己的管线见 [[verify-with-real-pipeline-and-readonly-probes]]；多层服务各有凭据见 [[layered-service-credentials-must-match-layer]]。
