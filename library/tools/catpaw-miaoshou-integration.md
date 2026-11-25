---
name: catpaw-miaoshou-integration
description: 妙手（CatPaw/CatX）设置 API 与 catpaw2api LLM 桥接；含鉴权头、propertyScope、限额与 Windows 落地坑
type: tool
source: 合并自 catpaw-miaoshou-as-llm-provider-via-catpaw2api, meituan-catpaw-miaoshou-settings-api；本机把妙手额度接入 magpie-gateway/ZCode（2026-11-21）：catpaw2api 源码编译到 C:\Software\catpaw2api，经网关 3425 实测 LongCat-2.5 回复 OK; 本机 妙手 2026.1116.1542 实测（2026-11-20）：迁移 ZCode 供应商时摸清 API 与限额，未写入
date: 2026-11-20
verified: 2026-11-21
topic: windows, llm
---
**经验**：妙手（CatPaw/CatX）设置 API 与 catpaw2api LLM 桥接；含鉴权头、propertyScope、限额与 Windows 落地坑

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## 妙手（CatPaw）当 LLM 供应商：catpaw2api 桥接

### 结论

妙手/CatPaw **不暴露 OpenAI 兼容端点**：应用包内没有 `chat/completions`，模型调用走 CatX 会话协议（`/api/gateway/v1/agent/...` + Pike 长连接 + zod RPC），本地监听端口是内部 UI 服务（401）。要把它当供应商，用第三方开源桥 **catpaw2api**（GitHub HITZY2002/catpaw2api，Go；同类还有 catpawai-proxy、catpaw-bridge）。

### 协议要点（catpaw2api 逆向文档）

- 网关 `https://catx.nocode.cn`，鉴权 `X-Auth-Token`（= `~/.meituan-catpaw/auth.json` 的 accessToken）。
- 直连 `https://ai.catpaw.meituan.com`，鉴权 `X-Passport-Token` + Cookie + `user-mis-id`。
- 聊天 `https://nocode.cn/api/chat/create` + `/api/chat/agent-stream`，头 `access-token` + `client-id`（= product.json 的 `2f73f89b68`）。
- **free 计划 SSE 不吐数据**，桥用轮询 `/api/agent/conversation/history`（约 3-6s）拿完整回复。
- token 72h 有效、无 refresh_token；`auths/catpaw-<uid>.json` 字段 `{uid,user_name,access_token,updated_at}`，**updated_at 用秒**。

### 本机落地点（C:\Software\catpaw2api）

`catpaw2api.exe`（127.0.0.1:7867）+ `auths/` + `config.json` + `.env.key`(CP2A_API_KEY) + `sync-token.ps1`（保活+同步登录态）+ 计划任务 `CatPaw2API`（登录+每 6h）。链路：ZCode → magpie-gateway(3425) → catpaw2api(7867) → 妙手云端。

### Windows 落地三坑（都实测踩过）

1. ⭐ **ps1 写 JSON 必须无 BOM**：`Set-Content -Encoding UTF8`（PS5.1）会写 BOM，Go 的 `json.Unmarshal` 直接解析失败 → 桥加载 0 账号。用 `[System.IO.File]::WriteAllText($p,$s,New-Object System.Text.UTF8Encoding($false))`。
2. ⭐ **单位**：auth.json 的 `updatedAt` 是毫秒，catpaw2api 的 `updated_at` 是秒；同步脚本要 `/1000`，否则每次都判为“已更新”并重启。
3. ⭐ **计划任务 Execute 用全路径**：`powershell.exe` 作 Execute 会返回 0x80070002；改 `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` 后 result=0。参数里带引号的路径也可能被截断，路径无空格就别加引号。

### ⚠️ 实测局限（2026-11-21，重要）

提示词注入式 function calling **不可靠**：LongCat-2.5 流式工具调用实测 **1/8** 成功，多数回复是"该工具不在我的可用工具列表"（妙手上游的助手人格压制了注入块）；把工具说明从用户消息末尾移到系统指令段也没有改善。**依赖工具调用的 agent 场景不要用妙手桥接**（只适合纯聊天/单轮问答）。要可靠的 agent 能力，直连厂商官方 API（LongCat 官方 `api.longcat.chat` 支持原生 tools）。

### How to apply

1. 有现成项目优先：搜 GitHub `catpaw2api` / `catpawai-proxy` / `catpaw-bridge`，别自己逆向。
2. 凭证只落本地（auths 0600、.env.key），勿入库/外发；第三方二进制本地源码编译。
3. token 到期且妙手客户端也掉登录时，用 `catpaw2api-login.exe` 重新 OAuth，再跑一次 `sync-token.ps1`。
4. 只监听 127.0.0.1，别暴露公网。

相关 [[catpaw-miaoshou-integration]]。

## 妙手（CatPaw）设置与自定义模型落点

**身份**：妙手 = 美团 CatPaw（CatX），`resources/product.json` 里 applicationName=`catpaw-moon`、appId=`com.catx.catpaw`、CLI 名 `paw`。
**目录**：Electron 用户数据 `%APPDATA%\catpaw-moon`；主数据 `~/.meituan-catpaw`（内含 `<uid>/`、auth.json、skills、runtimes）。本机 uid=3947928063。
**CLI**：`~/.meituan-catpaw/bin/paw.cmd` = 妙手.exe + `resources/cli/catpaw-cli.js`（`ELECTRON_RUN_AS_NODE=1`），**必须 GUI 在运行**才能用；`paw settings list` 只有 67 个 UI 设置，**不含供应商**。

### 账号设置 API（实测）

- 凭证：`~/.meituan-catpaw/auth.json` → `auth.accessToken`（passport token）。
- 读：`GET https://catx.nocode.cn/api/gateway/user/setting/list`，请求头 **`x-auth-token: <token>`**。`Authorization: Bearer` 会 401（`4010 Authentication token is required`）。
- 写：`PUT /api/gateway/user/setting`，JSON body `{propertyKey, propertyValue, propertyScope}`。
  - `propertyScope` 只收 **LOCAL / CLOUD**；本地桌面=`LOCAL`；传 `COMMON`（列表接口的展示值）报 400 `4002`。
  - `propertyValue` 传数组或字符串 JSON 都可。
- ⭐ **单键值上限约 70KB**：自定义模型 `model.customModels` 实测 31 条（70,030 B）200、32 条（72,267 B）500 `Internal server error`。完整四档参数每条约 2.2KB；仅保留 context 参数 62 条约 62KB 可写。
- 本地 `%APPDATA%\catpaw-moon\catpaw-moon-unified-<uid>.json` 为**加密缓存**（高熵二进制），不能直接改；真值是服务端设置。

### 自定义模型条目结构（USER_CUSTOM）

```json
{"id":"<uuid4>","provider":"USER_CUSTOM","modelTypeName":"<上游模型ID>",
 "description":"<显示名>","supportImage":false,"modelTypeId":<负整数>,
 "catPawModelType":"<同 modelTypeId 字符串>","apiKey":"sk-...",
 "apiBaseUrl":"https://.../v1","enableImageInput":true,
 "extendedInfo":{"iconLight":"...","iconDark":"...","source":"custom","provider":"USER_CUSTOM"},
 "parameterDefinitions":[...thinking/effort/context/maxOutputTokens...],
 "parameterConstraints":[...]}
```

- `modelTypeName` 是**发给上游的 model 字段**，必须保持原样（不能加供应商前缀）。
- `modelTypeId` 由 UI 分配：`min(现有值)-1`，首条 `-1000000000`（源码 `reduce(...,-1e9)`）。
- 参数定义可裁剪（空数组也合法），但 UI 就不再显示对应控件。

### How to apply

1. 读设置前先确认 GUI 登录态；`settings list` 无供应商，别在那找。
2. 迁移/批量改自定义模型：GET 备份原值 → 本地合并 → PUT（LOCAL）→ GET 读回校验条数与 id 唯一性。
3. 超过 ~70KB 就裁参数或减模型，别硬塞。
4. 改前关闭妙手，改完重启；本地缓存是加密文件，别手改。

相关 [[zcode-provider-config-no-reasoning-enabled-schema]]。
