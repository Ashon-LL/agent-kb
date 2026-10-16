---
name: pkill-self-match-kills-own-shell
description: `pkill -f "<pattern>"` 的 pattern 会匹配到承载它的那条命令行本身 ⇒ 连自己的 shell 一起杀掉，后续步骤静默丢失（同坑 2026-10-13、2026-10-14 两次踩，用户点名「以后少犯这样的错」）
type: pitfall
source: MH-Agent-Open（本机 Git Bash 与 ssh 远程两侧都踩过）
date: 2026-10-14
verified: 2026-10-14
topic: safety, toolchain
---

**经验**：任何"按 pattern 杀进程"的命令，**pattern 会匹配到执行它的那条命令行自身**——因为命令行里就写着该 pattern。
典型形态：`ssh host 'pkill -f "uvicorn main:app"; nohup ...新起...; curl health'`
⇒ 远端 shell 的命令行文本里含 `uvicorn main:app` ⇒ `pkill` 杀掉目标后**顺手把承载它的外层 shell 也杀了** ⇒ 后面的"重启、验证、输出"**全部静默不执行**（无报错、无输出，看起来像"什么都没发生"）。

**Why（为什么特别隐蔽）**：
- 命令**部分生效**（目标进程其实被杀掉了），所以"看结果"不能判断命令是否跑完；
- **后续动作全丢**（杀旧 → 起新 → 验证 只完成第一步），故障延迟暴露；
- 在**一行式 ssh 命令**里最危险，且与"命令没输出"的常见误判（超时、断连）撞脸，容易归因错。

**How to apply**（优先前两条）：
1. **先取 PID 再杀**：`pgrep -f "[x]xxx"`（或 `ps aux | grep "[x]xxx" | awk '{print $1}'`）→ `kill <pid>`；
2. **方括号技巧**（最省事）：`pkill -f "[u]vicorn main:app"` —— 命令行文本是 `[u]vicorn`，正则匹配 `uvicorn` 但**不匹配自己**；
3. Windows 侧 `taskkill //PID <pid> //F`（PID 先由 `netstat -ano | grep :<port>` 取，**先确认再杀**）；
4. **破坏性动作拆成两次独立调用**：第一次「杀 + 验证（端口释放/进程消失）」，第二次「起 + 验证（health/日志）」——**不要塞进同一条链**。

**判据**：这类命令发完，必须**独立验证后续步骤真的执行了**（端口已释放、新进程 health 正常），⛔ 不能以"命令返回了"当作成功。
