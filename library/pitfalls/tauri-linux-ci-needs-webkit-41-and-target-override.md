---
name: tauri-linux-ci-needs-webkit-41-and-target-override
description: Tauri 前端加 Linux CI 编译门禁的两个隐性前提：官方 rust 镜像没有 Ubuntu 变体，且仓库里的 [build] target 会骗过本机 cargo check
type: pitfall
source: MH-Agent-Open PR #105（Rust 编译门禁落地）
date: 2026-09-22
verified: 2026-09-22
---

**经验**：给 Tauri 2 前端加「Linux 上 `cargo check`」这类 CI 门禁时，有两层前提
必须**同时**核实，缺一必红。而且两层都不可能在你本机上验证到——本机 `cargo check`
跟着仓库 config 只编 Windows 目标，编译门禁覆盖不到。

**第一层：基镜像的 distro 由 webkit 版本决定，不是随便挑。**

Tauri 2 经 wry 钉死 `webkit2gtk-sys = "=2.0.2"`，其 `Gir.toml` 是
`library = "WebKit2"` / `version = "4.1"`。它的 `build.rs` 用 `system_deps` 探
**`webkit2gtk-4.1`** 的 pkg-config，探不到就是

```rust
if let Err(s) = system_deps::Config::new().probe() {
    println!("cargo:warning={s}");
    process::exit(1);   // ⛔ 是 fatal，别被前面的 "warning" 字样骗了
}
```

Debian 12 (bookworm) 与 Ubuntu 22.04 只有 `webkit2gtk-4.0` ⇒ **必然红**。
Debian 13 (trixie) / Ubuntu 24.04 才有 4.1。

**第二层：官方 `rust` 镜像根本没有 Ubuntu 变体。**

核 `docker-library/official-images` 的 `library/rust` 清单，只发布 Debian 与 Alpine：
`1-bookworm` / `1-trixie` / `1-bookworm-slim` / `1-slim-trixie` / `1-alpine3.2x`。
全文 grep `noble` = **0 命中**。实测 `FROM rust:1-noble` 直接
`docker.io/library/rust:1-noble: not found`，Prepare 阶段即挂。

⇒ 两层交集，**唯一可用的官方路径 = `rust:1-trixie`**（Debian 13 + 官方 rust）。
备选 `ubuntu:24.04` + rustup 能凑出同效环境，但不推荐：多一步联网下载，
且 `sh.rustup.rs` 在国内不稳。

**⚠ Debian 包名没有 Ubuntu 的 `-0`**：`libwebkit2gtk-4.1-dev`（不是 `-4.1-0-dev`）、
`libjavascriptcoregtk-4.1-dev`（不是 `-4.1-0-dev`）。抄 Ubuntu 的包名列表到 Debian
必然失败。逐包用 `packages.debian.org/<release>/<pkg>` 核（HTTP 200 才算存在）。

**Why**：只核包名会选到不存在的镜像 tag；只核镜像会选到缺库的 distro。
两条路都是「本地完全看不出来、CI 上才炸」。

**How to apply**：

1. 写 CI 基镜像前**两个都查**：
   - `webkit2gtk-sys` 的 `Gir.toml` `version` 字段（决定要 4.0 还是 4.1）
   - `docker-library/official-images` 里有没有对应的 distro 变体
2. **本机证不了跨平台**。如果仓库里有 `[build] target = "x86_64-pc-windows-gnu"`
   这类 config（`frontend/src-tauri/.cargo/config.toml`，本机开发便利配置），
   本机 `cargo check` 只编 Windows 目标，**`#[cfg(not(windows))]` 的分支根本不进
   编译图**。这种分支等于死代码：不被测试、不被编译、任何改动都静默腐烂。
   ⇒ CI 里**必须显式 `--target x86_64-unknown-linux-gnu`**（CLI 优先于 config）。
   优先 CLI 覆盖，**别删那个 config 文件**——删了破坏本机开发手感。
3. 注意 `[target.x86_64-pc-windows-gnu]` 段的 linker/rustflags 按 target 限定，
   在 Linux 目标上天然不生效，无需额外处理。
4. 顺带：`cargo check` **不需要 `frontend/dist`** 存在。`tauri-build` 只在目录
   存在时加 `cargo:rerun-if-changed`，缺失不报错（实测 RC=0）⇒
   Rust job 不必装 node，可以独立成 job 与前端构建并行。

**实锤案例**：这套门禁加上后第一个拦下的不是环境问题，而是
`#[cfg(not(windows))]` 启动分支的 `E0716: temporary value dropped while borrowed`
——那个分支**从未被编译过**。症状对照：同函数里 Windows 分支用「先绑 `c`、再以 `c`
作块返回值」的形状（`c` 活到函数结束）能编过；non-windows 分支直接链式调用
`Command::new(&x).args(..).current_dir(..)`，`Command` 是匿名临时值，而
`.args()`/`.current_dir()` 都返回 `&mut Command` ⇒ 借用到语句末就被释放 ⇒ E0716。

相关：[[tauri-remote-url-has-no-ipc]]
