---
name: detached-process-causes-console-window-storm
description: Windows 上 DETACHED_PROCESS 会让子进程族的每个 console 子进程都新建一个可见黑窗（实测一次 26 个）；且它与 CREATE_NO_WINDOW 同用时后者被忽略——二者只能选一个
type: pitfall
source: gateway 重启黑窗风暴实弹 2026-09-26（用户报「重启 gateway 弹出很多黑屏」）
date: 2026-09-26
---

Windows 上为了「父进程退出后子进程仍存活」而加 `DETACHED_PROCESS`，
会产生**黑窗风暴**：该进程**没有控制台**，于是它 spawn 的每个 console
子进程都被 Windows **新建一个可见控制台窗口**。用户看到的是「一闪一闪的黑框」。

**实弹规模**（20260926，用户报「重启 gateway 为什么会弹出黑屏好多次」）：
一次启动弹 **26 个**可见控制台窗口（逐个子进程一个）。

## ⛔ 最坑的一点：两个 flag 不能叠加

Windows 进程创建标志文档明确：**`CREATE_NO_WINDOW` 与 `DETACHED_PROCESS`
同时指定时 `CREATE_NO_WINDOW` 被忽略**。
⇒ 先加 `DETACHED|NEW_GROUP`（26 个），再「顺手补上」`CREATE_NO_WINDOW`
变成 `DETACHED|NEW_GROUP|NO_WINDOW` —— **仍然 15~26 个**。
不是叠加，是**二选一**。

| flags | 新增可见控制台窗口 |
|---|---|
| `DETACHED \| CREATE_NEW_PROCESS_GROUP` | **26 个** |
| `CREATE_NEW_PROCESS_GROUP \| CREATE_NO_WINDOW` | **0 个** |
| 无 flags | 0 个 |

**正确组合 = `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`**，且
「父退出后存活」**不退化**（实测：spawner 立即退出，子进程 8s 后仍健康响应）。

## 怎么量（别靠肉眼）

用 `EnumWindows` + `GetClassNameW` 找 `IsWindowVisible` 且类名含 `console` 的
窗口，在启动前后各采样一遍取差集，**用背景线程 20~30ms 轮询**（窗口一闪就没了，
单次采样必漏）。⚠️ 用**真实目标进程**测，不要用 `node -e` 代替 —— 单进程探针
对纯 `subprocess.Popen` 恒为 0 窗（我自己先被这个假阴性骗过一次，误判「flag 无关」）。

## ⛔ 测「父退出后存活」的两个陷阱

1. **必须换独立 state-dir + 独立端口**：直接复用正被占用的目录，新实例会因
   目录级独占**根本没起来**，`curl` 失败会被误读成「父退出把它杀了」。
2. **先确证「它真的起过」**：查日志里有 `starting...`/`ready` 再判存活，
   否则「没起来」会被误判成「起来了又被杀」→ 得出相反的结论。

## 收口纪律

别在各调用点自己拼 flag。把组合抽成一个 helper（如
`detached_quiet_popen_kwargs()`）放在已有 `CREATE_NO_WINDOW` 的那个模块里，
与原有的 `quiet_popen_kwargs()` 并列；本仓已有 AST/文本守卫断言
「`CREATE_NO_WINDOW` 字面量全仓只在该模块出现」，新调用点**必须复用 helper**
（我第一次自己拼就被守卫拦下——守卫是对的，绕开它才是错）。

同族：[[windows-scripting-terminal-gotchas]]、[[shared-config-multi-owner-merge-write]]。
