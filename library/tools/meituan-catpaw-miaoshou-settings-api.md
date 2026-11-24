---
name: meituan-catpaw-miaoshou-settings-api
description: 妙手（美团 CatPaw/CatX）账号设置走网关照；读写用 x-auth-token 头（Authorization: Bearer 会 401）；propertyScope 只收 LOCAL/CLOUD（COMMON 报 400）；单键值约 70KB 上限（31 条完整自定义模型 200、32 条 500）；自定义模型存 model.customModels，本地 unified json 是加密缓存
type: tool
source: 本机 妙手 2026.1116.1542 实测（2026-11-20）：迁移 ZCode 供应商时摸清 API 与限额，未写入
date: 2026-11-20
verified: 2026-11-20
topic: windows, llm
---

# 妙手（CatPaw）设置与自定义模型落点

**身份**：妙手 = 美团 CatPaw（CatX），`resources/product.json` 里 applicationName=`catpaw-moon`、appId=`com.catx.catpaw`、CLI 名 `paw`。
**目录**：Electron 用户数据 `%APPDATA%\catpaw-moon`；主数据 `~/.meituan-catpaw`（内含 `<uid>/`、auth.json、skills、runtimes）。本机 uid=3947928063。
**CLI**：`~/.meituan-catpaw/bin/paw.cmd` = 妙手.exe + `resources/cli/catpaw-cli.js`（`ELECTRON_RUN_AS_NODE=1`），**必须 GUI 在运行**才能用；`paw settings list` 只有 67 个 UI 设置，**不含供应商**。

## 账号设置 API（实测）

- 凭证：`~/.meituan-catpaw/auth.json` → `auth.accessToken`（passport token）。
- 读：`GET https://catx.nocode.cn/api/gateway/user/setting/list`，请求头 **`x-auth-token: <token>`**。`Authorization: Bearer` 会 401（`4010 Authentication token is required`）。
- 写：`PUT /api/gateway/user/setting`，JSON body `{propertyKey, propertyValue, propertyScope}`。
  - `propertyScope` 只收 **LOCAL / CLOUD**；本地桌面=`LOCAL`；传 `COMMON`（列表接口的展示值）报 400 `4002`。
  - `propertyValue` 传数组或字符串 JSON 都可。
- ⭐ **单键值上限约 70KB**：自定义模型 `model.customModels` 实测 31 条（70,030 B）200、32 条（72,267 B）500 `Internal server error`。完整四档参数每条约 2.2KB；仅保留 context 参数 62 条约 62KB 可写。
- 本地 `%APPDATA%\catpaw-moon\catpaw-moon-unified-<uid>.json` 为**加密缓存**（高熵二进制），不能直接改；真值是服务端设置。

## 自定义模型条目结构（USER_CUSTOM）

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

## How to apply

1. 读设置前先确认 GUI 登录态；`settings list` 无供应商，别在那找。
2. 迁移/批量改自定义模型：GET 备份原值 → 本地合并 → PUT（LOCAL）→ GET 读回校验条数与 id 唯一性。
3. 超过 ~70KB 就裁参数或减模型，别硬塞。
4. 改前关闭妙手，改完重启；本地缓存是加密文件，别手改。

相关 [[zcode-provider-config-no-reasoning-enabled-schema]]。
