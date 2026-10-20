---
name: rustup-update-fails-when-stale-msvc-std-component-missing
description: rustup update 因已装 stable 工具链里注册了 x86_64-pc-windows-msvc 的 rust-std 组件但文件已缺失而失败并回滚（failure removing component ... directory does not exist）；解法＝装一个干净版本号工具链→default→验证→卸载旧 stable，绕开坏状态而不是反复重试
type: tool
source: 2026-10-08 default 会话升级 Rust 1.95→1.99 实测
date: 2026-10-08
verified: 2026-10-08
topic: rust, toolchain
---

`rustup update` 失败并自动回滚的典型现场：主机是 gnu（`stable-x86_64-pc-windows-gnu`），日志却在删 **`x86_64-pc-windows-msvc`** 的 rust-std，报 `error: failure removing component 'rust-std-x86_64-pc-windows-msvc', directory does not exist: 'lib\rustlib\x86_64-pc-windows-msvc\lib\std-<hash>.dll'`。含义：工具链的组件清单里注册了一个 **msvc 目标 std 组件，但它的文件已在盘上不存在**（被外部清理删过，或工具链目录曾被改名/跨 host 复制），rustup 更新前要先删旧组件，删不掉就整笔回滚——**重试多少次都一样，旧工具链仍可用但永远升不动**。

绕过办法（实测 1.95.0 → 1.99.0 成功）：

1. `rustup toolchain install <版本>-x86_64-pc-windows-gnu`（新版本号 = 全新目录，不含坏清单）
2. `rustup default <新工具链全名>` → 验证 `rustc -V` / `cargo -V` / `rustup toolchain list` 显示 active
3. `rustup toolchain uninstall stable-x86_64-pc-windows-gnu`（删掉升不动的旧件；rustup 顺便完成 1.29.0→1.29.1 自更新）

**Why**：不知道根因时容易误判成"网络问题/磁盘满/新版本有 bug"，反复重试浪费十几分钟还以为是 rustup 的 bug。报错文本里的**目标三元组（msvc）与主机不符**就是指纹。

**How to apply**：看到 `failure removing component` 就直接走"新工具链旁路"，别修 rustup 本身；删旧件前务必先验证新工具链 active。关联 [[windows-home-cleanup-safe-vs-traps]]。 [[no-new-artifacts-in-c-root]]、[[nvidia-driver-update-denied-by-service-key-lock]]、[[windows-hardware-reserved-memory-attribution]]、[[windows-memory-hogs-ui-hosts-and-everything]]。