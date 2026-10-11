---
name: esp32-arduino-cli-flash-workflow
description: 本机（Windows）ESP32 编译烧录链路——arduino-cli 装在 ~/arduino-cli-tools、FQBN 必须带 huge_app 分区、sketch 目录名必须与 .ino 同名、ELF 体积分析法，另附 GFX/ST7789 三坑
type: tool
source: ESP32-C3 固件项目（2026-09 沉淀）
date: 2026-10-06
verified: 2026-10-06
topic: windows
---

**经验**：本机跑 ESP32 不需要装 Arduino IDE，全走命令行。

**工具链落点**
- `arduino-cli.exe` 在 `~/arduino-cli-tools/`（直接下的二进制，v1.5.1）
- ESP32 core（3.3.11）与库在 `~/AppData/Local/Arduino15/`（`packages/esp32` 约 6 GB，含 riscv32 工具链）；用户库目录 `~/Documents/Arduino/libraries`
- 板卡索引/大包下载受网络影响时换 jsdelivr 镜像 + 断点续传，见 [[github-china-network-workarounds]]

**两条硬约束（踩过才知道）**
1. **sketch 目录名必须与 .ino 同名**：仓库根目录名不匹配就编不过，要拷贝到同名目录再编（例：`~/clawd_sketch/clawd_mochi/`，示例仅示意命名规则）。
2. **FQBN 必须加大分区**：`esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=huge_app`。一旦引入 WiFi/HTTPClient，默认 1.31 MB app 分区直接溢出；huge_app = 3 MB。

```
arduino-cli compile --fqbn <上面那串> <同名sketch目录>
arduino-cli upload  -p COM3 --fqbn <上面那串> <同名sketch目录>
```

**ELF 体积分析法**（省 flash/RAM 时）
`compile --build-path <dir>` 产出 ELF，再用 `~/AppData/Local/Arduino15/packages/esp32/tools/esp-rv32/<ver>/bin/` 下的 `riscv32-esp-elf-size -A` / `nm --size-sort`。实测结论：core 3.x 已默认 `-flto`（显式再开 = 0 收益）；flash 大户是 vfprintf/scanf 家族（~20 KB，String/printf 带进来）和 mbedtls（~15 KB，WPA 必需）；未被引用的 `#include` 是 0 字节（链接器会丢）。

**ESP32 + Adafruit_GFX + ST7789 三坑（同类小屏通用）**
1. 该 Adafruit_GFX 构建**没有 `textWidth()`**——居中得自己按 `len*6*size` 算。
2. **ST7789 无 framebuffer**：每帧 `fillScreen` 会看到明显闪屏；进视图时画一次框，之后只重绘变化区域。
3. `WiFi.scanNetworks()` 在 STA 正在连接时返回 0——扫描前先 `WiFi.disconnect()`。

**屏上美术**：用户给参考图时**别手绘近似**（手画线条图被明确否决）——转 1-bit 位图（PIL 阈值化 → `PROGMEM` 数组 → `drawBitmap`）原样显示，文字图层叠加在上面。

**用户偏好**：嵌入式/烧录类任务由我直接走 CLI 完成，不让用户装 IDE；**烧录会覆盖板子，动手前先确认**。

关联 [[windows-update-resume-and-no-auto-reboot-playbook]]、[[windows-home-cleanup-safe-vs-traps]]。