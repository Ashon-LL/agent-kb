---
name: zcode-plugin-python-runtime-isolation
description: ZCode 插件（video-agent-kit / video2code）的 MCP server 硬依赖 python `mcp` 1.x（video2code 锁 1.9.0），与本机系统 python 的 mcp 2.x 冲突；解法=建独立 venv 装依赖，再把插件 manifest 与 hooks 里的 python3 重指向该 venv，绝不动系统解释器
type: tool
source: 10年人间 EP01 P0（2026-10-29 本机 Windows + ZCode 3.16 实测）
date: 2026-10-29
verified: 2026-10-29
topic: zcode
---

**经验**：ZCode 的第三方视频插件（`video-agent-kit` 0.4.3 / `video2code` 0.6.1）MCP server 在 manifest 里写死 `"command": "python3"`，而它们的 `requirements.txt` 要 `mcp>=1.0.0,<2.0.0`（video2code 更锁 `mcp==1.9.0`）。本机系统 python 3.13 里装的是 `mcp 2.1.1`（被 pip 的 `browser-use` 库依赖），**2.x 删掉了 `Server.list_tools/call_tool` decorator API ⇒ 插件工具全部起不来**。且 `mcp 1.9.0` 还要求 `pydantic<2.12`（2.14 删了 `pydantic._internal._typing_extra.eval_type_backport`，import 直接炸）。

正确解法是**隔离 + 重指向**，不是降级系统包：

1. 建独立 venv（放项目内，避免污染系统解释器）：`python -m venv .venv-video`
2. 装齐：`mcp==1.9.0` + `"pydantic>=2.7.2,<2.12"` + `requests pillow "opencv-python-headless>=4.8,<5.0" numpy jieba fonttools click platformdirs tqdm`，再 `pip install --no-deps "scenedetect>=0.6"`（**必须 --no-deps**：scenedetect 声明依赖 GUI 版 opencv，直装会把 headless 的 cv2 覆盖掉，两个包一起坏）
3. 改插件缓存里的 `<plugin>/.claude-plugin/plugin.json` → `mcpServers[*].command`：注意 **`command` 是单独的 `"python3"` 字符串**（args 分离），不是 `"python3 xxx"` 整串，替换时要同时处理这两种形态
4. 同一个插件目录的 `hooks/hooks.json` 里所有 `"python3 \"${CLAUDE_PLUGIN_ROOT}/...\""` 也要换成 `"<venv python>" "${CLAUDE_PLUGIN_ROOT}/..."`
5. 验收：`<venv python> <plugin>/skills/env-setup/scripts/env_doctor.py` 报「全部就绪」；再对每个 server 脚本喂一条 `initialize` + `notifications/initialized` + `tools/list` 的 stdio 序列，确认能列出工具（实测 video-agent-kit 37 个、video2code 5 个、soundcraft 23 个）

**Why**：不隔离就得把系统 `mcp` 降级 ⇒ 依赖 mcp 2.x 的其他组件（本机是 pip 的 browser-use）静默失效；只装包不改 manifest ⇒ 插件仍用系统 `python3`，白装。漏改 hooks 则环境体检/守卫钩子仍跑在坏解释器上。另外把 venv 建在项目内而非用户目录，是因为本机约定禁止在用户主目录新建目录。

**How to apply**：凡是「ZCode 插件起不来 / MCP 工具缺一半 / 报 decorator API 不存在」先跑插件的 `env_doctor.py` 看它要求哪个 python 解释器与包版本；命中版本冲突就走上面 5 步。改插件缓存文件属**侵入式**操作：`zcode plugins update` 会还原，必须留一个重指向脚本（本项目是 `script/repoint-plugin-python.js`）并在文档里写明「更新后重跑」。改动插件文件后建议用 `zcode plugins validate <plugin dir>` 确认 manifest 仍合法。相关：[[zcode-platform-verified-facts]]、[[mcp-stdio-install-smoke-test]]、[[delete-hook-script-after-config-invalidated]]。

关联 [[zcode-platform-verified-facts]]、[[mcp-stdio-install-smoke-test]]、[[delete-hook-script-after-config-invalidated]]。
