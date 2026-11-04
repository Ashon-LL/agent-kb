---
name: scaffold-assets-trim-to-delivered-platforms
description: 脚手架生成的多平台资产只留真实交付平台并加守卫；生成器的 update/regenerate 命令会把删掉的平台模板整体回灌
type: pitfall
source: MH-Agent-Open desktop-wails（2026-10-29 项目卫生）
date: 2026-10-29
verified: 2026-10-29
topic: delivery
---

**经验**：`wails3`/`create-tauri-app` 一类脚手架会一次性生成 macOS / iOS / Android / Linux / server 全套构建资产。若产品只交付其中一个平台，把这些目录删掉，并**同批删除**引用它们的 Taskfile include 与死任务；随后加一条守卫用例（断言平台目录不存在、`Taskfile` 只 include 保留平台、版本元数据与主版本同源），防止下一次 `update build-assets` / 重新初始化时静默回灌。

**Why**：MH-Agent-Open 的 `desktop-wails/` 86 个跟踪文件里只有 20 个是 Windows 实际要用的；其余 66 个是模板噪音，还会让“这项目到底发布什么”变得不可读。更隐蔽的是生成器的 `update build-assets` 默认重写全部平台目录——删完不设守卫，下一次有人按 README 跑一遍就复活。反过来，删平台目录必须同批改 Taskfile，否则 `wails3 build` 会在 `generate:icons` 引用 `darwin/icons.icns` 这类路径上炸。

**How to apply**：接手/初始化脚手架后先问“我们交付哪个平台”，按平台裁剪资产与 include，跑一次真实构建（不是只跑 lint），再加范围守卫。裁剪后若原本的 `update build-assets` 任务已删除，就要在配置注释里写明“版本/元数据文件改为手工维护”，否则版本号会漂。相关：[[local-sync-must-reach-user-visible-layer]]（交付链要对齐用户实际拿到的那层）。

**补充（2026-10-30，同一工程的资源生成器）**：裁剪平台资产后，构建仍可能残留模板的**资源生成器**问题。
Wails v3 的 `wails3 generate syso` 生成的 VERSIONINFO 能被 `pefile` / `strings -el` 读出完整字符串，
但 .NET `FileVersionInfo`（Windows 资源管理器属性页同源）读不到 `ProductVersion`/`CompanyName`——
即“看起来有版本信息、实际属性页空白”。对照实验：同一 exe、同一图标与 manifest，改用
`goversioninfo`（`go run github.com/josephspurrier/goversioninfo/cmd/goversioninfo@v1.7.0`）
生成的资源可被 .NET 正常读取。⇒ 验收版本资源不能只看 `strings`，要用 `FileVersionInfo` 读一次；
`versioninfo.json` 里 `FileFlagsMask`/`FileOS` 等字段必须是**十进制字符串**（`"63"` 可用，`"0x3f"` 会解析失败）。
