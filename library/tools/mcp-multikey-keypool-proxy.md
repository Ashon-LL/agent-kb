---
name: mcp-multikey-keypool-proxy
description: 官方 MCP server 只认单 key 时的多密钥正解=逐 key 一个官方子进程+本地 stdio 代理（单命名空间+自动故障转移+冷却自愈）；附带 npx 缓存残缺（zod v3/v4 缺失）导致 server 秒退且客户端日志零痕迹的取证法
type: tool
source: ZCode tavily MCP 双密钥改造（tavily-mcp@0.2.22，实测双 key+故障转移全通过）
date: 2026-10-17
verified: 2026-10-17
topic: mcp
---

**经验**：
1. **多密钥的正解不是 fork 上游，而是"子进程池 + 透传代理"**：给每个 key 各起一个**官方** server 子进程（`TAVILY_API_KEY=key_i`），自写一个 ~300 行、零依赖的 stdio 代理对外只暴露**一套**工具（名字与官方完全一致，如 `tavily_search`）。代理自己应答 `initialize`（协议版本借用子进程协商结果），`tools/call` 按"第一个健康 key"投递，失败自动换 key 重试同一调用。好处：官方工具面全保留、升级只跟 `@latest` 走、宿主侧零感知。
2. **故障转移判定与冷却要分层**：任何 `isError` 都换 key 重试（不依赖错误文案匹配才稳）；但**只有**配额类（`usage limit|quota|429`）和鉴权类（`invalid api key|401`）才把 key 拉进冷却，其余错误 30s 短冷却——否则把参数错误误判成 key 坏了。配额冷却指数退避 1m→2m→4m…上限 6h（月配额报废的 key 只按小时探活），鉴权 6h；**冷却到期自动回归候选**，默认永远优先第一个 key（主 key 恢复后自动复位）。
3. **Windows spawn 两条硬规则**（代理内起子进程）：① `npx` 是 .cmd shim，**必须 `cmd.exe /d /c npx ...`** 或钉 `npx.cmd` 全名（与 [[cnb-cli-needs-cmd-suffix-when-spawned-from-python]] 同源）；② 杀子进程要 `taskkill /pid <pid> /T /F` 整棵树，`proc.kill()` 只杀 cmd.exe 会留孤儿 node。
4. **协议细节**：代理 stdout 只准走 JSON-RPC（newline-delimited），所有日志走 stderr（宿主会收进日志）；给子进程发请求时**自己分配 request id**，别透传宿主 id（避免多子进程/重试时响应串台）；`tools/list` 等其余请求原样透传给健康子进程即可。
5. **npx 缓存残缺是新发现的静默杀手**：`%LOCALAPPDATA%\npm-cache\_npx\<hash>\` 里包可能装残——实测 `@modelcontextprotocol/sdk` 嵌套的 `zod` 缺 `v3/`、`v4/` 两个子目录，server 启动即 `ERR_MODULE_NOT_FOUND` 秒退。**特征：宿主日志里连 server 名字都查不到**（不是 failed 状态，是零痕迹）。取证：手动跑一次 `npx -y <包>@latest < /dev/null` 看 stderr；修法：**删掉整个 `_npx\<hash>` 目录**，下次 npx 自动重装（重装后 zod 会提升到顶层，布局可能与旧目录不同，属正常）。
6. **自测姿势**：写一个 `smoke-test.cjs` 驱动脚本（起代理→握手→tools/list→真调一次工具），另跑一轮 `TEST_KEYS="坏key,好key"` 验证故障转移路径——比只测正常路径值钱得多；再跑一轮"全坏"验证错误能如实回传不挂死。实测数字：tavily 双 key 全链 12.8s（含 npx 冷启动），故障转移轮 11.5s 且第二次调用直接走冷备零浪费。

**Why**：官方 server 单 key 无轮换是常态（源码级确认：只读 `process.env.TAVILY_API_KEY`，无任何 rotate/fallback 逻辑）；fork 上游要维护、改 npx 缓存会被重装覆盖，只有代理层是既通用又不侵入的实现点。

**How to apply**：任何"MCP server 只支持单 key 而我有多个 key/多个账号配额"的场合（搜索类、API 类皆同）；产物参考 `~/.zcode/mcp-servers/tavily-key-pool/`（index.js 代理 + smoke-test.cjs + README）。相关：[[mcp-stdio-install-smoke-test]]、[[cnb-cli-needs-cmd-suffix-when-spawned-from-python]]、[[windows-scripting-terminal-gotchas]]、[[zcode-platform-verified-facts]]。
