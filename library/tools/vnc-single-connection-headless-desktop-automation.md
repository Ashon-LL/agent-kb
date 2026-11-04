---
name: vnc-single-connection-headless-desktop-automation
description: 单次连接 VNC 靶机的无头操作法：先开机等待、只连一次并保持（Xvfb+vncviewer），用 import 截图、xdotool 注入；端口探测/短连接会烧掉唯一会话；远程批量写文件用 base64 防丢字符
type: tool
source: 2026 强网杯 0perator（VNC kiosk 靶机，x11vnc -once 场景）
date: 2026-10-31
verified: 2026-10-31
topic: security
---

# VNC 单次连接的无头桌面自动化

## 经验

CTF/靶机的 VNC 常常是**一条连接用完即死**（x11vnc `-once`，或平台端口映射只放行一次）。正确做法：

1. **别用 TCP 探测端口**。`/dev/tcp`、nc、nmap 的成功连接会被服务端当成一次真实客户端，客户端一断开 x11vnc 就退出，后续全部 `Connection refused`。拿到地址后按下发时间等 90–150 秒（容器启动+桌面就绪），再直接连。
2. **只连一次并保持**：无头环境用 `Xvfb :99 -screen 0 <远端分辨率>x24` 起虚拟屏，`setsid nohup vncviewer -passwd <pwfile> -shared host::port &` 常驻。TightVNC/TigerVNC 的 `vncviewer` 会一直握着这条连接。
3. **截图**：`DISPLAY=:99 import -window root shot.png`（ImageMagick）。注意 Xvfb 屏幕要等于/大于远端分辨率，否则截图只有左上角一块；远端窗口画在 vncviewer 窗口内部，X 根窗口只有它一个。
4. **输入**：`DISPLAY=:99 xdotool windowfocus <viewer窗口id>` 后 `xdotool key super+e` / `xdotool type --delay 8 "..."`。viewer 窗口 id 用 `xwininfo -root -tree` 找（`TightVNC: ...`）。
5. **远程写脚本**：xdotool 长串输入会偶发丢字符（实测丢 `(` `)`），把文件内容本地生成后 base64，再 `xdotool type "echo <b64> | base64 -d > /path/file"`，最稳。
6. 若 VNC 带 `-noclipboard`，别指望剪贴板回传；输出靠 screenshot 读，或让远端把结果写到屏幕上半部分（窗口底部可能被裁）。

## Why

- 端口探测/调试性短连接 = 消耗一次性会话。实测：nmap/`/dev/tcp` 检查后，真正要用的客户端连上时走完 RFB 握手却永远收不到 framebuffer update（`vncdotool captureScreen` / `pause` 全部 timeout），随后端口拒绝，容器只能重发。
- Python `vncdotool` 的 `api.connect` 在服务端半就绪时会成功返回但 `factory.deferred` 不触发，命令排队后 60–90 秒超时；CLI `vncdo` 则是连接→执行全部命令→断开，天然不适合交互式探索。
- xdotool 经 XTEST 注入、跨 VNC 传输时按键有丢失概率；括号/引号丢失会造成 payload 语法错误而难以察觉（本次就写坏过一次 face.py，registry 报 `load-error` 才发现）。

## How to apply

- 任何「VNC 密码 + 靶机地址」的 CTF 题、或需要 GUI 操作但没有图形界面的环境。
- 现象是「第一次能截到图、之后端口 refused」「连上但截图超时」时，先怀疑一次性会话已被烧掉：重发容器，然后严格按上面 1→2 顺序，中间不要探测端口。
- 需要在远端执行多步命令时，先开终端（kiosk 场景常靠 Super+E → Thunar → Ctrl+L 输入 `/usr/bin/xfce4-terminal`），之后所有文件写入走 base64。
