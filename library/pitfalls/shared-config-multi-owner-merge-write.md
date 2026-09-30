---
name: shared-config-multi-owner-merge-write
description: 第三方工具的同一份 config 常有多个主人（官方向导写凭据、doctor 写 meta、你写渠道），整文件覆盖会静默抹掉别人的键——必须读-合并-写；且插件的「信任开关」就在 config 里，缺它静默不装载
type: pitfall
source: openclaw gateway config 多主人覆盖实弹 2026-09-26
date: 2026-09-26
verified: 2026-09-26
topic: api-gateway, security, methodology
---

驱动外部工具时，**同一份 config 文件往往有多个写入者**，各自只认自己那几个键。
你只覆盖"自己拥有的键"是对的；**整文件覆盖 = 静默抹掉别人的键**，且通常**没有任何报错**。

## 实弹（openclaw gateway，20260926）

一份 `openclaw.json` 有三个主人：

| 键 | 谁写的 |
|---|---|
| `channels.<ch>.{appId,clientSecret,streaming,mediaMaxMb}` | **官方扫码向导**（用户交互产生，不可再生） |
| `plugins.entries.<plugin-id>.enabled=true` | 外部插件的**信任开关**（官方文档/doctor） |
| `agents.entries` / `meta.migrations` / `wizard` | 官方 `doctor` / 向导 |

我写了「生成 config」函数整文件覆盖 ⇒ 两个连环事故：
1. **抹掉信任条目** ⇒ 渠道**静默不装载**：只有一条 warning
   （`installed without explicit trust`），**无 error 级日志**，界面显示"运行中"，
   用户看到的现象是「绑定了但机器人连不上」。
2. **抹掉扫码凭据** ⇒ 用户已绑定成功的 appId/clientSecret 丢失，**只能重扫**。

## ⛔ 三个反直觉点（各花了我很久）

1. **`plugins list` 说 enabled，渠道却不起**：该命令读的是 **state 记录**，
   而装载判据是 **config 里的显式条目**。两个数据源不一致，
   只信前者会得出「已就绪」的错误结论。
   ⇒ **真判据是启动日志的插件清单行**：`http server listening (14 plugins: ..., <plugin-id>, ...)`
   —— 数一下你的插件在不在里面。
2. **故障只有 warning 级**：这类"配置不全 ⇒ 静默跳过"的设计不留 error。
   ⇒ 排查第一步必须是**拿到子进程完整输出**（见下条），别指望 `xxx logs` 子命令
   （实测是空的）。
3. **覆盖有时序性**：向导写的键**在你下次写 config 时才会被抹**。所以"绑定时好的、
   重启后失效"这种时序症状，先怀疑自己的 config 写入。

## 做法

- 写 config 一律「**读回 → 只改自己那几块 → 写回**」；解析失败先备份改名再按空配置继续，
  绝不静默丢用户数据。
- 保留"已有具体值就别用占位值盖掉"的判据（本例：向导已写具体 openid 时不得写哨兵值）。
- 配一条源码级护栏测试：构造一份"含别人键 + 凭据"的 config，跑自己的写函数，
  断言别人的键**原样还在**。
- **子进程 stdout/stderr 绝不可 DEVNULL**：丢输出 = 故障不可诊断。落盘（带大小滚动），
  并把尾部日志抽成状态字段回传 UI，让用户直接看到原因。

同族：[[override-config-drops-implicit-fallbacks]]（覆盖式配置丢隐式默认）、
[[config-field-name-is-not-spec-read-consuming-code]]（字段名不是规格）。
