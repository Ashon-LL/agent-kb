---
name: mcp-prompt-template-servers-add-no-capability
description: 判断一个 MCP 对模型有没有用，看 handler 到底返回什么，不要看它宣称能干什么；sequential-thinking 这类"纯提示词/记账型"MCP 传进去的 thought 一个字都不回传，是单向通道，零信息量；新 MCP 先读 dist/index.js 的 handler 再决定留不留
type: tool
source: 2026-09-30 用户问「这个 MCP 对你有用吗」（@modelcontextprotocol/server-sequential-thinking），读源码后判定可删
date: 2026-09-30
verified: 2026-09-30
---

**经验**：评估一个 MCP 值不值得留，读它的 handler 源码，**看它返回什么**，而不是读它 `registerTool` 的 `description` 宣称能干什么。判「提示词/记账型」的四条特征：

1. handler 里没有网络请求、文件读写、子进程——不接触外部世界；
2. **返回值与入参无关**：你传进去的东西它不还给你；
3. `description` 里大段「When to use… / You should… / How to apply…」的祈使句——那是在给我写提示词模板；
4. 副作用只写给**人类**看（打到 stderr 的彩色输出），我收不到。

`@modelcontextprotocol/server-sequential-thinking` 四条全中，实测 `dist/lib.js` 只有 78 行：handler 做三件事——入参 push 进数组、彩色方框 `console.error` 到 stderr、返回四个计数器（`thoughtNumber` / `totalThoughts` / `nextThoughtNeeded` / `branches` / `thoughtHistoryLength`）。**我传进去的 `thought` 全文不回传**，每次调用都是单向通道。更亏的是那 55 行注册描述跟着工具 schema **常驻系统提示，每轮对话烧一次 token**，比我偶尔用一次的成本还大。

**Why**：它的"能力"是把我的推理变成只进不出的——写进去的只有我自己读得见，换回来的四个数字我本来就知道，等于每一步白付一次完整往返。更根本的问题是**结构化思考 ≠ 更准**：2026-09-30 我在 DSH 迁移里把 AstrBot tdp 网关专用教训套到 StepFun 上，那次失败的根因是**没回去读条目的 `source:` 作用域**，不是思考步骤不够编号；强制走五步编号照样拦不住，真拦住的只是回去看一眼。另外它的 `thoughtHistory` 只活在 MCP 进程内存，服务重启/上下文压缩即清空，比我自己上下文还不可靠。

**How to apply**：
- 新 MCP 先 `Read` 它 `dist/index.js` 的 `registerTool(..., async (args) => {...})` 和它引用的 lib 文件，看 handler 的 `return`。四条特征中三条以上命中 ⇒ 删。
- 反例对照：`js-reverse` / `chrome-devtools` 这类返回真实数据（代码、DOM、响应体）的才是真能力。判据不是"MCP 好不好"，是"它给我的东西是不是我自己没有的"。
- 要跟踪多步任务用 `TodoWrite`（真状态、可跨轮次），不要拿 thoughtHistory 当台账。
- 别被小模型语境下的"结构化思考提升推理质量"说服——那条针对小模型，不适用于已有原生深度思考配额的主模型。
- 删除落点：`~/.zcode/cli/config.json` 的 `mcp.servers`（⚠️ 该文件里只要有 server 就整体覆盖 `.agents/mcp.json`，改前先 Read）。

关联 [[config-field-name-is-not-spec-read-consuming-code]]、[[log-text-is-not-spec-read-emitting-code]]、[[kb-entry-source-scope-is-the-boundary]]、[[mcp-stdio-install-smoke-test]]。
