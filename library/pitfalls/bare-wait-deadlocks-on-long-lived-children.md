---
name: bare-wait-deadlocks-on-long-lived-children
description: 测试/运维脚本里裸 `wait` 会等待**所有**后台子进程，包括常驻服务（假上游/mock server/守护进程）⇒ 永久挂起；且释放它的 kill 若写在 wait 之后则不可达。附"任务卡死"的远程取证法（读日志尾部 + 重取一次比行数）
type: pitfall
source: MH-Agent-Open（CNB NPC 工单 cnb-eke-1k2paekff 挂起事故）
date: 2026-09-18
---

**经验**：脚本里 `cmd &` 起了常驻进程后再裸 `wait`，**必然死锁**。
`wait`（不带 PID）等待**当前 shell 的全部后台任务**，常驻服务自身永不退出 ⇒ 永不返回。

## 症状（真实案例）

一个 CNB NPC 工单跑 Q3 锁行为测试时**永久挂起**：

- 派发方实测：工单 `status` 长期 `pending`，`npc go` stage 长期 `start`
- 日志共 4489 行，**最后一条时间戳停在 12:03:15**，此后静默 **1h47m**
- 最终 CNB 在 **`npc go` duration = 7,260,853 ms（正好 2h01m）** 处判 `error`
  —— 即**被平台 2h 上限掐断**，不是自己完成

## 根因（脚本全文取证）

```bash
# ❌ 死锁写法
node upstream_slow.mjs 59995 12000 > up-slow.log 2>&1 &   # 假上游：常驻 HTTP 服务，永不退出
SLOWPID=$!
sleep 0.5
( timeout -k 5 60 node openclaw.mjs agent --local ... ) &   # 这两个有超时，65s 内会结束
sleep 2
( timeout -k 5 60 node openclaw.mjs agent --local ... ) &
wait                       # ⛔ 等「所有」后台任务 ⇒ 被假上游永久阻塞
cat lock-A.status lock-B.status
kill $SLOWPID 2>/dev/null  # ⛔ 释放假上游的动作排在 wait 之后 ⇒ 不可达
```

两个 `openclaw` 进程其实**有界**（`timeout -k 5 60` ⇒ 65s），
但 `wait` 被那个常驻假上游卡住 ⇒ `kill` 永远执行不到 ⇒ 自锁。

**注意这个坑的隐蔽性**：写脚本的人**确实加了超时**，但超时只包住了
「被测命令」，没包住「测试基础设施」和「脚本整体」。

## ✅ 正确写法（三选一，任选但必须做对）

```bash
# A（推荐）：显式等 PID，不用裸 wait
node upstream_slow.mjs 59995 12000 > up.log 2>&1 &
SLOWPID=$!
trap 'kill $SLOWPID 2>/dev/null' EXIT      # 兜底释放
( ...cmd... ) & PA=$!
sleep 2
( ...cmd... ) & PB=$!
wait $PA; wait $PB                          # ✅ 只等这两个，明确有界

# B：整体脚本套硬超时
timeout -k 5 180 bash run_test.sh || echo "timed out rc=$?"

# C：不让常驻进程成为本 shell 的子进程（setsid / 独立进程组）
#    但仍须保证脚本自身有硬超时
```

**判据（写任何起后台进程的脚本时自检）**：
1. 脚本里有没有裸 `wait`？有 ⇒ 同脚本内是否还有**永不退出**的后台任务？有 ⇒ **必挂**。
2. 释放常驻进程的 `kill` 是否写在 `wait` **之后**？是 ⇒ **不可达**，等于没写。
3. 脚本**整体**有没有硬超时兜底？（"我给的每条命令都有 timeout" **不算** ——
   本次事故就是这种。）

## 配套：远程诊断"任务是否卡死"的取证法

判断一个远端任务（CI job / 容器进程 / 长跑脚本）是「还在做」还是「已卡死」：

| 步骤 | 做法 | 关键判据 |
|---|---|---|
| 1 | 取日志，记**总行数**与**最后一条时间戳** | 时间戳与当前时间差 = 静默时长 |
| 2 | **等一会儿再取一次**，比**行数** | 行数**完全没变** ⇒ 无新输出（强证据） |
| 3 | 看最后一条命令**是不是一个可能阻塞的动作** | 如 `wait` / 交互式命令 / 无超时的网络调用 |
| 4 | 查平台侧**上限** | 本例 `npc go` 在 2h01m 被判 error ⇒ 平台有 2h 上限 |

⛔ **不要**只看 `status: pending` 就断言"还在跑" —— `pending` 既包含
"正常执行中"也包含"卡死中"。**必须结合日志静默时长**才能定性。
⛔ 也别把 stage 的 `duration` 字段当实时值读（快照里可能是静态的）。

## 附带教训：别把「引用」当「本批产出」

同一轮里我一度误判：在日志中看到一张锁测试**结果表**（5 个场景 + exit 码），
就以为"锁测试已经跑完"。实际那是 agent `cat` 了一份**前序证据文档**的内容，
**不是本批的运行输出**。取证时要分清「日志里出现的内容」是
**执行产物**还是**被读取的文件内容** —— 看它前后是否有 `cat`/`Read` 类命令。

**How to apply**：写测试脚本时，把「测试基础设施的生命周期」和
「被测对象的超时」**分开管**，并给**整个脚本**一个硬上限。
相关：[[agent-loop-follow-progress-not-liveness]]、[[windows-scripting-terminal-gotchas]]。
