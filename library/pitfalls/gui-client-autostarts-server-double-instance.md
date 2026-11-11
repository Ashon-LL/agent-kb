---
name: gui-client-autostarts-server-double-instance
description: "桌面/GUI 客户端连远端时会自己拉起 dsh web 之类的 server；若同时用 systemd 固定端口守护，会双实例（端口/token/日志都不同、各吃几百 MB），必须二选一"
type: pitfall
source: APIShow 多服务器管理（2026-11-10，qiniumei / apishow-prod 的 dsh web）
date: 2026-11-10
verified: 2026-11-10
topic: toolchain
---

# 客户端自动拉起的 server 不要再用 systemd 守一遍

## 经验

- 现象：远端已经用 systemd 起了 `dsh web --host 127.0.0.1 --port 39189`，客户端一重连又拉起一个 `dsh web --port 0`，两个实例并存：

  ```
  # systemd 实例（固定端口）
  dsh web --host 127.0.0.1 --port 39189   → 127.0.0.1:39189
  # 平台客户端实例（动态端口）
  dsh web --host 127.0.0.1 --port 0       → 127.0.0.1:44831（另开 9231 devtools）
  ```

  实测各占 ~300–380 MB（1.9 GB 内存的机器上很致命）。

- 判断谁在跑：

  ```bash
  pgrep -af 'dsh web'
  ss -tlnp | grep MainThread
  systemctl is-active dsh-web; systemctl is-enabled dsh-web
  ```

- 二选一：
  - **交给客户端**（推荐，客户端每次重连都会自己拉起）：`systemctl disable --now dsh-web`，保留 unit 文件作兜底，需要时 `enable --now`。
  - **交给 systemd**：固定端口，并确认客户端不会自动拉起（多数客户端做不到，故不推荐）。

- 客户端实例的地址/token 在它自己写的日志里（dsh 为 `~/.dsh-app-remote/web.log` 的 `dsh web: http://…` 行），token 每次启动都变，不要缓存旧 URL。

## Why

- 双实例不只是浪费内存：两个实例的 **token 不同**、会话/凭据目录可能互相争用，客户端连的永远是它自己拉起的那个，systemd 实例白跑。
- systemd 的 `Restart=always` 会让「手动 kill 掉多余实例」在下次开机/崩溃后复活，问题反复。
- 只看 `systemctl status` 会误判「服务没起」——其实客户端实例在跑，端口也对，只是不归 systemd 管。

## How to apply

- 接入任何「客户端会自动拉起远端 server」的工具（dsh web、VS Code Server、Jupyter、各类 GUI agent）前，先决定由谁托管，别两边都开。
- 已有双实例时：先确认客户端实例的监听端口与日志落点，再 `disable --now` 掉 systemd 单元，最后 `pgrep` 复核只剩一个。
- 兜底单元保留但保持 `disabled`，并把「为什么 disabled」写进本机运维备注（`/root/SERVER-OPS.md` 之类），避免下一个人又 `enable` 回来。
