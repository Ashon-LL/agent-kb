---
name: newapi-rc26-token-crud-shapes
description: New API rc.26 令牌 CRUD 三坑——POST /api/token/ 成功但 data 为 null 拿不到 key、列表接口返回掩码 key、DELETE /api/token/{id} 读错参数恒假失败；真值只在 tokens.key
type: pitfall
source: APIShow/New API rc.26（2026-09-28 令牌 CRUD 三坑）
date: 2026-09-28
verified: 2026-09-28
topic: api-gateway

---

# New API rc.26：令牌 CRUD 端点形状

rc.26 实测（apigogo 生产库 `/opt/apishow/data/one-api.db`）。同族条目：[[newapi-rc26-channel-crud-shapes]]、[[newapi-disable-must-sync-abilities]]、[[newapi-multikey-size-must-track-key-count]]。

## POST /api/token/ —— 成功但 `data` 为 null，**响应里拿不到 key**

```
POST /api/token/
{
  "name": "codearts-group",
  "remain_quota": 5000000000,
  "expired_time": -1,
  "unlimited_quota": true,
  "model_limits_enabled": false,
  "group": "codearts"
}
-> {"message": "", "success": true, "data": null}
```

body 是**扁平结构**（不像 channel 需要包一层 `{"channel": {...}}`）。`success=true` 但 `data` 是 null，**key 不在响应里**。

## GET /api/token/ —— 列表返回的是**掩码 key**

```
GET /api/token/?p=0&page_size=100
-> data.items[]  每项的 key 形如 "MVEN**********q6wu"（18 字符）
```

这是掩码，**不是真 key**。别拿它当返回值用，也别据此判定「创建失败」。真值只在库里：

```sql
SELECT id, name, "group", status, unlimited_quota, remain_quota,
       model_limits_enabled, expired_time, deleted_at, key
FROM tokens WHERE id = ?;
```

库里 `key` 是**裸 48 位**、**不带 `sk-` 前缀**（客户端拼 `sk-`）。

**幂等脚本的正确写法**：先 `GET` 列表按 `name` 查是否已存在 → 已存在就复用并从 DB 取真值 → 不存在才 `POST`；`POST` 后再 `GET` 列表反查 id、再从 DB 取 key。断言只断形态（长度、前缀字符集），**不要写 `assert key.startswith("sk-")`** —— 库里就是没有前缀，这一步会让你整脚本 abort 在已成功的写操作之后。

## DELETE /api/token/{id} —— 读错参数，恒假失败

```
DELETE /api/token/65  ->  {"success": false, "message": "record not found"}
```

该端点从 `Authorization` 读 token_id 而**不是**路径参数，所以永远找不到。真删只能 SQL 软删 + 重启刷缓存：

```sql
UPDATE tokens SET deleted_at = <now> WHERE id = ?;
```

⚠️ 重启可能不可行（生产有其他用户在用），所以删除令牌前要先确认有别的途径。

## GET /api/option/ 与 UserUsableGroups 的一个漏判坑

改 `UserUsableGroups` 时**别按 key 查模型名**：它是「组名 → 描述串」映射，模型名在 **value** 里。

```python
v = json.loads(snap["UserUsableGroups"])
if "deepseek-v4-pro" not in v:      # ❌ 查的是 key，永远 False，静默跳过不写
    ...
assert v["deepseek"] == "deepseek-v4-flash, deepseek-v4-pro"   # ✅ 查 value
```

`ModelRatio`/`CompletionRatio`/`CacheRatio`/`ModelPrice` 才是「模型名 → 数值」，按 key 查才对。另：`GET /api/option/` 返回**全表**，很多项的 value 是纯字符串，不能一律 `json.loads`（会 `JSONDecodeError`）。

## How to apply

- 建令牌：body 扁平；`data` 为 null 是正常成功，别当失败。
- 取 key：只从 `tokens.key` 读，列表接口是掩码；库里无前缀，别断言 `sk-`。
- 删令牌：API 端点不可用，走 SQL 软删 + 重启；重启不可行时先想别的。
- 改 option：`UserUsableGroups` 查 value 不查 key；非映射类 option 的 value 不是 JSON。
- **写操作后读 `success` 字段，不要只看 HTTP 码**（rc.26 大量「HTTP 200 + success=false + 一个字没改」）。
- 复用名前先确认软删记录：`name` 可能被 2026-08-11 那批用户手动软删的令牌占用，重建属越界。
