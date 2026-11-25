---
name: video-agent-kit-qc-writes-to-cwd
description: video-agent-kit 的 QC/抽帧/分析工具按当前工作目录写 out/ 与 .video_agent/ 边车；在工作区根调用会在根目录留下空 out/、.v2c/，应在具体工程目录内调用，并把 .video_agent/、.v2c/ 纳入 gitignore 与收尾清理
type: pitfall
source: 10years-humanity（2026-11，video-agent-kit 0.4.3 实测）
date: 2026-11-10
verified: 2026-11-09
topic: toolchain
---

## 经验

video-agent-kit 的 QC / 抽帧 / 分析类工具把输出目录解析成**当前工作目录**下的
`out/` 与 `.video_agent/`（部分工具还会建 `.v2c/`），而不是工程参数里的路径。
在会话工作区根调用，根目录就会多出空 `out/`、`.video_agent/`、`.v2c/`。

做法：
- 在具体集目录（如 `10years-humanity/`）内调用，别在工作区根调用；
- 输出能显式传路径就显式传；
- `.gitignore` 加 `.video_agent/`、`.v2c/`、`out/`；
- 每次用完检查根目录，空的边车目录当场删。

## Why

这些边车目录不报错、不显眼，容易在 `git status`/打包/备份时混进去；工作区根不是项目目录，
留下的空目录会被误认为新工程结构。2026-11 在 `%USERPROFILE%\Videos\Bili` 根调用时
实际留下过空 `out/` 与 `.v2c/`。

## How to apply

- 调 video-agent-kit 的 MCP 工具前先确认 CWD 是工程目录。
- 工具跑完 `ls` 一下 CWD；发现 `out/`/`.video_agent/`/`.v2c/` 且为空，删掉。
- 相关：[[zcode-plugin-python-runtime-isolation]]、[[no-new-artifacts-in-c-root]]。
