---
name: powershell-start-process-argumentlist-strips-quotes
description: PS Start-Process -ArgumentList 会剥掉参数内层双引号并静默失败，且不抛异常；改把脚本落盘传路径
type: pitfall
source: mh-agent-open（2026-09-19 实弹，家族第 2 例）
date: 2026-09-19
verified: 2026-09-19
topic: powershell
---

**症状**：`Start-Process -FilePath node.exe -ArgumentList @('-e', $js)` 里，
`$js` 是一段含双引号的 JS 源码。目标进程**只收到被切断的片段**（实测 node 只拿到
`var` 三个字符），报 `SyntaxError: Unexpected end of input`。

**根因**：`-ArgumentList` 会把数组元素拼成命令行字符串时**剥掉内层双引号**，
于是带空格的源码被按空白切碎成多个参数。

**⛔ 最坑的一点**：`Start-Process` **不抛异常**（它成功"启动"了进程，是子进程自己退出）。
⇒ 外层 `try/catch` **抓不到** ⇒ 脚本照常打印成功日志（实测打印
`[watchdog] armed: ...`，而收尾时 `disarmed (timer pid  released)` —— **pid 为空**，
坐实那个对象从未持有有效进程）。**假成功比报错更危险。**

**A/B 实测**（PS 5.1 / node v24.19.0）：

| 变体 | 写法 | 结果 |
|---|---|---|
| A（原样） | `-ArgumentList @('-e', $js)` | ❌ `exit=1`，子进程只收到 `var` |
| **B（修复）** | JS **落盘**，`-ArgumentList @(<文件路径>)` | ✅ `exit=0`，正常输出 |

**How to apply**：
- 要向 `Start-Process` 传**含空格/引号的代码或长文本**时，**一律先落盘再传路径**。
  ⚠ 写临时文件时注意扩展名与模块制式（`.mjs` 里 `require` 不可用）。
- **判据不能信成功日志**：要验证子进程真的起来了，得看**它持有的 pid/句柄是否非空**，
  或让它写一个可验证的产物（实测 B 变体输出 `PROBE_FIRED` 就是这种可验证产物）。
- 家族同源：**「解释器/调用层会改写我的参数」**是一类反复出现的坑 —— 已见
  `subprocess` 调 Windows sh 脚本要加 `.cmd`、`-ArgumentList` 剥引号、
  Windows 命令行长度上限。凡"参数没按我写的到"都先怀疑这一层。

**适用范围**：与项目无关的 PowerShell 通用坑。⛔ 若被调方是**本仓产品代码**，
它走 Python 列表直传 `execve`，**不受此坑影响**（别误诊）。
