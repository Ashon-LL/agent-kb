---
name: mcp-stdio-install-smoke-test
description: stdio MCP 安装前必须实测 initialize+tools/list 握手；uvx/npx 默认解析最新大版本会压垮 1.x 时代 server，官方包本身也可能带 bug
type: tool
source: ZCode 联网搜索双源接入（Tavily + 博查），2026-09-15
date: 2026-09-15
verified: 2026-09-15
---

**经验**：
1. **装 stdio MCP 前先管道实测，不写完配置就交付**。python subprocess 起服务器，依次喂 `initialize` → `notifications/initialized` → `tools/list` 三行 JSON-RPC（newline-delimited），看到 serverInfo 和工具名单才算装成；无 key 时也要至少做到握手+tools/list，把"能起"与"能用"分开验收。
2. **uvx/npx 的大版本漂移是头号杀手**：`uvx some-mcp` 默认解析最新 `mcp` 2.x，而 2.x 把 `FastMCP` 改名成 `MCPServer`，1.x 时代写的 server 直接 `ModuleNotFoundError`。修法：`uv run --with "mcp[cli]<2"`（或 npm 同理钉版本）；pyproject 里 `>=1.6.0` 这种只设下限的依赖声明在包发布几年后就是定时炸弹。
3. **官方包也可能出厂即坏**：博查官方 `bocha-search-mcp`（0.0.1，仓库与 PyPI 同一份代码）用 `FastMCP(name, prompt=...)` 构造——`prompt` 参数在任何 mcp 版本都不存在，钉老版本也起不来。处置：clone 本地 + 最小补丁（`prompt=`→`instructions=`，语义等价）+ 钉版本，补丁位置记进项目记忆。
4. **连通性探测别拿根路径说事**：`curl https://api.tavily.com` 返回 000 只是根路径不应答，**带 key POST 真实端点**（`/search`）才通——差点因此把"直连不通"写进结论、要求用户挂代理。判"不可达"前用真实业务请求验证。
5. **Windows 上把 server 起进客户端的 spawn 坑**（裸 npx ENOENT / .cmd EINVAL / shell=True 僵尸进程 / bash 吞 `$`——全文已沉淀到 [[windows-scripting-terminal-gotchas]] "进程 spawn"节，此处只留客户端侧动作）：server 起不来先看**客户端自己的日志**（如 kimi-code 在 `~/.kimi-code/logs/kimi-code.log` 搜 `mcp server unavailable`），别只听模型说"没有这个工具"。

**Why**：MCP 服务器秒退在客户端侧只表现为 timeout/未连接，不实测握手就会把"包坏了"误诊成"网络坏了"再误诊成"要挂代理"。

**How to apply**：任何新装/升级 stdio MCP（ZCode/Claude/Cursor 均同）；排查"面板显示未连接"。相关：[[env-claims-must-be-reverified]]、[[github-china-network-workarounds]]、[[zcode-platform-verified-facts]]、[[windows-scripting-terminal-gotchas]]。
