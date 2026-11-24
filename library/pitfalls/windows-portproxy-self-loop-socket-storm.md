---
name: windows-portproxy-self-loop-socket-storm
description: Windows portproxy 的 connectaddress 写成"本机 LAN IP"时，转发目标又落回同一个监听端口 ⇒ 自环扇出：单次连接在几十秒内堆出十万级 socket/句柄，表现为"鼠标能动但整个界面卡死、过一会儿自己恢复"；判据=某 svchost 句柄数暴涨 + netsh portproxy show 里 connectaddress 等于本机地址
type: pitfall
source: 2026-11-23 机械革命 GM5RGEE（Ryzen 5 6600H / Win 26H2 26300.9711）间歇卡顿排查
date: 2026-11-23
verified: 2026-11-23
topic: diagnosis
---

## 经验

`netsh interface portproxy` 的 `connectaddress` 必须是**服务真正所在的可达地址**；
写成本机的 LAN IP（如 `192.168.43.80`）且 `listenaddress=0.0.0.0`、端口相同，就是自环：

```
0.0.0.0 8000 -> 192.168.43.80 8000     # 转发目标 = 自己的监听端口
```

每接受一次连接就再向自己发一次，**指数扇出**。本机实测：45 秒内 PID 2176 句柄 2,577 → 71,639 → 104,234，
`netstat -ano` 里该 PID 109,062 行、其中 54,524 条落在本地端口 8000，状态成对出现
54,525 `FIN_WAIT_2` + 54,523 `CLOSE_WAIT`（转发端关了、回环端不关）。

处置（管理员）：

```powershell
netsh interface portproxy show v4tov4        # 先看有没有 connectaddress = 本机 IP 的自环
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

删完实测：句柄 104,234 → 2,419，netstat 行 109,062 → 14。要对外暴露只绑 127.0.0.1 的服务，
`connectaddress` 用 **127.0.0.1**（不是本机 LAN IP）。

## Why

- 目标地址就是自己的监听端口 ⇒ 永不自终止，直到句柄表/ephemeral 端口/非分页池耗尽；
- 耗尽期间一切需要分配资源（建窗口、开文件、起进程）的调用一起排队 ⇒ **全系统卡顿**；
- 鼠标光标由 GPU 硬件层绘制、不依赖这些分配，所以"**只有鼠标能动**"；
- 事件日志里查不到 TDR/温度/内存压力这类常规证据，容易被误判成显卡或硬盘问题；
- 半关闭连接（CLOSE_WAIT/FIN_WAIT_2）会一直挂着，即使风暴停了句柄也不会马上回落，可能骗过"现在已经好了"的复查。

## How to apply

症状命中「间歇性全系统卡死、鼠标能动点不动、几十秒后自己恢复」，且系统日志无 TDR/热/内存证据时，
第 0 步先查这个（比查驱动快得多）：

1. `Get-Process | Sort-Object HandleCount -Descending | Select-Object -First 5 Name,Id,HandleCount`
   —— 单个 `svchost` 十万级句柄 = 强信号（正常几千）；
2. 定位端口分布：`netstat -ano | Select-String '\s<pid>\s*$'` 按本地端口分组，看是否集中在某个端口；
3. `netsh interface portproxy show v4tov4`——**connectaddress 等于本机 IP 就是自环**；
4. 删规则后复测句柄数与 netstat 行数，两个数都要掉下来才算修好；
5. 同机其它端口同形状的规则一并清（本机 22、5000 也是自环，只是还没被触发）。

反例提醒：不要因为"风暴自己停了"就认为没事——它是按触发源周期性重来的。
