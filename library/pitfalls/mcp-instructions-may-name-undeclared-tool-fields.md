---
name: mcp-instructions-may-name-undeclared-tool-fields
description: MCP initialize instructions 提到的参数不等于工具真实入参；apishow-video 曾出现 instructions 要求 negative_prompt 但 tools/list 未声明，2026-11-07 部署 2026.11.7.1100 已补齐，调用前仍须按当前 inputSchema 复核
type: pitfall
source: 2026-11-07 用户要求先核对视频 MCP 配置、暂不生成视频
date: 2026-11-07
verified: 2026-11-07
topic: mcp
---

**经验**：配置 MCP 视频工具时，`initialize.instructions` 是工作流说明，不是参数规格；**真正可传的字段以 `tools/list` 返回的 `inputSchema.properties` 为准**。字段名只在说明里出现、却没有在 schema 里声明时，不要硬塞进本次工具调用。

**Why**：2026-11-07 对 `https://api.apigogo.cyou/mcp` 做只读探测：`apishow_prepare_video` 的 description 与服务端 instructions 都明确要求传 final prompt / `negative_prompt`，但 `tools/list` 暴露的 `apishow_prepare_video` 参数只有 `aspect_ratio`、`conversation_id`、`enable_audio`、`image`、`last_image`、`model`、`prompt`、`reference_audios`、`reference_images`、`reference_videos`、`resolution`、`seconds`，**没有 `negative_prompt`**；反过来 `apishow_confirm_video` 才有 `negative_prompt`。若照说明在 prepare 阶段硬传，可能被 JSON Schema 拒绝、被客户端丢弃或静默忽略，导致「以为负面提示词已入草稿，其实没有」。

**How to apply**：
1. 使用新 MCP 前，先读 `~/.zcode/cli/config.json` 的 `mcp.servers`，再用 `initialize` + `tools/list` 只读查询，脱敏保存服务端说明与 `inputSchema`。
2. 把说明要求与 schema 字段做差集；差异字段只在真正声明它的工具调用里使用。若确需试探额外字段，用免费且不落任务的动作验证，并明确记录是被拒绝、忽略还是接受。
3. 文案里的「服务端会优化提示词」与 description 里「服务端不调用 LLM、要求客户端先优化」冲突时，也不要替服务端判定行为；以工具实测返回为准，提示词先由客户端写完整。
4. 该结论是特定服务端 2026-11-07 的快照，换版本/换端点必须重新查 `tools/list`；不要把当时的字段表当永久规格。

> ⏰ 时效状态（2026-11-07 记录，**已于部署 2026.11.7.1100 后复核**）：本机 `apishow-video` 当前端点为 `https://api.apigogo.cyou/mcp`。修复前 `apishow_prepare_video` 未声明 `negative_prompt`；修复后 `tools/list` 实测 `apishow_prepare_video`、`apishow_generate_video`、`apishow_confirm_video` 均含 `negative_prompt`，且 `prepare_video.prompt` 文案已改为「Final prompt you (the client model) already wrote/optimized; the server does NOT call an LLM.」。
> ⚠️ 用前必须实测：用 MCP initialize + `tools/list` 检查当前 `apishow_prepare_video.inputSchema.properties` 是否含 `negative_prompt`，不要把修复前快照或修复结论当永久规格。

**2026-11-07 服务端修复补记**：用户部署版本 `2026.11.7.1100` 后，反馈容器 healthy、45 账号、近 5 分钟 0 panic/fatal；`apishow_prepare_video` 带 `negative_prompt="blur, low quality, watermark"` 实测草稿原样落库，随后取消并清理 drafts；`hy4-free` 聊天 HTTP 200。本机独立 `tools/list` 复核确认上述三个工具的字段均存在。该修复只改变工具声明，不改变 `/video/drafts`、`/video/generations` 原本就接收 `negative_prompt` 的服务端逻辑；旧视频任务的 `upstream video task failed` 是另一个问题，不能据此归因到字段缺失。

关联 [[mcp-prompt-template-servers-add-no-capability]]、[[config-field-name-is-not-spec-read-consuming-code]]、[[config-load-failure-check-file-refs-and-schema]]。
