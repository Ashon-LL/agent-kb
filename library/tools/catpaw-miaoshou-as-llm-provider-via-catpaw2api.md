---
name: catpaw-miaoshou-as-llm-provider-via-catpaw2api
description: 妙手/CatPaw 无 OpenAI 兼容端点（模型走 CatX 会话协议），要当 LLM 供应商须用第三方 catpaw2api 桥接；含协议端点、free 计划轮询 history、Windows 落地三坑（ps1 写 JSON 带 BOM 让 Go 解析失败、auth.json 毫秒 vs auths 秒、计划任务 Execute 必须全路径）
type: tool
source: 本机把妙手额度接入 magpie-gateway/ZCode（2026-11-21）：catpaw2api 源码编译到 C:\Software\catpaw2api，经网关 3425 实测 LongCat-2.5 回复 OK
date: 2026-11-21
verified: 2026-11-21
topic: windows, llm
---

# 妙手（CatPaw）当 LLM 供应商：catpaw2api 桥接

## 结论

妙手/CatPaw **不暴露 OpenAI 兼容端点**：应用包内没有 `chat/completions`，模型调用走 CatX 会话协议（`/api/gateway/v1/agent/...` + Pike 长连接 + zod RPC），本地监听端口是内部 UI 服务（401）。要把它当供应商，用第三方开源桥 **catpaw2api**（GitHub HITZY2002/catpaw2api，Go；同类还有 catpawai-proxy、catpaw-bridge）。

## 协议要点（catpaw2api 逆向文档）

- 网关 `https://catx.nocode.cn`，鉴权 `X-Auth-Token`（= `~/.meituan-catpaw/auth.json` 的 accessToken）。
- 直连 `https://ai.catpaw.meituan.com`，鉴权 `X-Passport-Token` + Cookie + `user-mis-id`。
- 聊天 `https://nocode.cn/api/chat/create` + `/api/chat/agent-stream`，头 `access-token` + `client-id`（= product.json 的 `2f73f89b68`）。
- **free 计划 SSE 不吐数据**，桥用轮询 `/api/agent/conversation/history`（约 3-6s）拿完整回复。
- token 72h 有效、无 refresh_token；`auths/catpaw-<uid>.json` 字段 `{uid,user_name,access_token,updated_at}`，**updated_at 用秒**。

## 本机落地点（C:\Software\catpaw2api）

`catpaw2api.exe`（127.0.0.1:7867）+ `auths/` + `config.json` + `.env.key`(CP2A_API_KEY) + `sync-token.ps1`（保活+同步登录态）+ 计划任务 `CatPaw2API`（登录+每 6h）。链路：ZCode → magpie-gateway(3425) → catpaw2api(7867) → 妙手云端。

## Windows 落地三坑（都实测踩过）

1. ⭐ **ps1 写 JSON 必须无 BOM**：`Set-Content -Encoding UTF8`（PS5.1）会写 BOM，Go 的 `json.Unmarshal` 直接解析失败 → 桥加载 0 账号。用 `[System.IO.File]::WriteAllText($p,$s,New-Object System.Text.UTF8Encoding($false))`。
2. ⭐ **单位**：auth.json 的 `updatedAt` 是毫秒，catpaw2api 的 `updated_at` 是秒；同步脚本要 `/1000`，否则每次都判为“已更新”并重启。
3. ⭐ **计划任务 Execute 用全路径**：`powershell.exe` 作 Execute 会返回 0x80070002；改 `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` 后 result=0。参数里带引号的路径也可能被截断，路径无空格就别加引号。

## ⚠️ 实测局限（2026-11-21，重要）

提示词注入式 function calling **不可靠**：LongCat-2.5 流式工具调用实测 **1/8** 成功，多数回复是"该工具不在我的可用工具列表"（妙手上游的助手人格压制了注入块）；把工具说明从用户消息末尾移到系统指令段也没有改善。**依赖工具调用的 agent 场景不要用妙手桥接**（只适合纯聊天/单轮问答）。要可靠的 agent 能力，直连厂商官方 API（LongCat 官方 `api.longcat.chat` 支持原生 tools）。

## How to apply

1. 有现成项目优先：搜 GitHub `catpaw2api` / `catpawai-proxy` / `catpaw-bridge`，别自己逆向。
2. 凭证只落本地（auths 0600、.env.key），勿入库/外发；第三方二进制本地源码编译。
3. token 到期且妙手客户端也掉登录时，用 `catpaw2api-login.exe` 重新 OAuth，再跑一次 `sync-token.ps1`。
4. 只监听 127.0.0.1，别暴露公网。

相关 [[meituan-catpaw-miaoshou-settings-api]]。
