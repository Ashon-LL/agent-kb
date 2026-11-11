---
name: ssh-hardening-blocks-client-tunnels
description: "SSH 加固把 AllowTcpForwarding 设 no 后，依赖 -L 隧道的客户端（dsh web/远程 IDE/数据库工具）报远端端口连不上；改成 local 即可，不必开 yes"
type: pitfall
source: APIShow 多服务器管理（2026-11-10，qiniumei 上 dsh web 隧道）
date: 2026-11-10
verified: 2026-11-10
topic: security
---

# SSH 加固会挡掉客户端隧道

## 经验

- 症状：客户端提示「远端端口连不上」（例如 dsh 客户端的 `127.0.0.1:39189`），但服务器上**进程在、端口也在听**：

  ```bash
  ps -eo pid,args | grep dsh        # 进程存在
  ss -tlnp | grep 39189             # 127.0.0.1:39189 有监听
  ```

- 查开关：`sshd -T | grep -i allowtcpforwarding`。值为 `no` 时，客户端所有 `-L`/`-R` 转发请求都会被 sshd 拒绝，隧道根本建不起来。
- 修：sshd drop-in 里改成 `AllowTcpForwarding local`（只允许客户端本地转发，仍禁止 `-R` 反向转发），然后：

  ```bash
  cp -a /etc/ssh/sshd_config.d/00-xxx.conf /etc/ssh/sshd_config.d/00-xxx.conf.bak-YYYYMMDD
  sed -i 's/^AllowTcpForwarding no$/AllowTcpForwarding local/' /etc/ssh/sshd_config.d/00-xxx.conf
  sshd -t && systemctl reload ssh     # reload 不断现有连接
  sshd -T | grep -i allowtcpforwarding
  ```

- 端到端验证（本地跑，别只看配置）：

  ```bash
  ssh -N -L 29189:127.0.0.1:39189 <host> &
  curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:29189/
  ```

  返回任何 HTTP 码（哪怕是 401/404）都说明链路通了；`000` 才是没通。

## Why

- 加固模板常把转发一刀切关掉。服务在服务器上自测正常（`curl 127.0.0.1:port` 通），只有**经过 SSH 隧道**的客户端失败，极易误判成服务故障。
- `PermitTunnel no` 管的是 tun 设备，**不是**端口转发的开关，别拿它当替身。
- 直接开 `AllowTcpForwarding yes` 会连 `-R` 一起放开；只做客户端 `-L` 的场景用 `local` 足够，攻击面更小。
- 本地测试端口别超过 65535（写成 `139189` 会得到 `Bad local forwarding specification`，看起来像语法问题，其实是端口越界）。

## How to apply

- 新机做完 SSH 加固后，若计划用远程 IDE、dsh web、数据库客户端隧道，先确认 `AllowTcpForwarding` 不是 `no`。
- 改任何 sshd 配置：先备份 drop-in → `sshd -t` 通过 → `reload`，不要 `restart`。
- 需要更严可再加 `PermitOpen 127.0.0.1:*`，把可转发目标限制在本机回环。
