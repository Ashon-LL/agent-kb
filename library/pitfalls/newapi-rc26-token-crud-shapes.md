---
name: newapi-rc26-token-crud-shapes
description: New API rc.26 令牌 CRUD 形状——POST /api/token/ 成功但 data 为 null 拿不到 key、列表接口返回掩码 key、DELETE /api/token/{id} 可用且软删立即生效（旧「恒假失败」结论已证伪）；真值只在 tokens.key
type: pitfall
source: APIShow/New API rc.26（2026-09-28 令牌 CRUD 三坑；2026-10-09 修正 DELETE 结论）
date: 2026-09-28
verified: 2026-10-09
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

## DELETE /api/token/{id} —— **可用**（2026-10-09 源码+实测双重证伪旧结论）

⚠️ **本条曾记为「读错参数、恒假失败」，是错的，已推翻。** 旧结论的成因：对一个**已软删**的 token 重试，`First()` 因 soft-delete 作用域查不到 → 误判为「端点坏了」。

rc.26 源码（`controller/token.go:354`）读的**就是路径参数**：

```go
func DeleteToken(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))   // ← 路径参数，没有读错
	userId := c.GetInt("id")
	err := model.DeleteTokenById(id, userId)
```

`model.DeleteTokenById` 用 `Token{Id: id, UserId: userId}` 做 `First()` 再 `token.Delete()` ⇒ **是带 user 作用域的软删**（GORM `deleted_at`）。

**实测（2026-10-09，token id=80）**：

```
DELETE /api/token/80        -> 200 {"message":"", "success":true}      # 首次：真的删掉了
DB: deleted_at 被写上，随后用该 key 请求 -> 401 Invalid token          # 立即失效，无需重启
DELETE /api/token/80        -> 200 {"message":"record not found","success":false}   # 对已删的重试
DELETE /api/token/999999    -> 200 {"message":"record not found","success":false}   # 不存在的 id
```

⇒ **`record not found` 的含义 = 「该 id 在（未软删的）记录里找不到」**，可能是已经删过了、或不属于当前 user、或 id 不存在 —— **不代表端点坏了**。
⇒ 软删**立即生效**（缓存自动失效，用旧 key 请求即 401），**不需要重启**刷缓存。旧条目里「只能 SQL 软删 + 重启」的说法作废。

区分三个信号：`success:true` = 本次真的删了；`record not found` = 这次没删（因为本来就不在）；**别把「第二次调用」的结果当成「端点不可用」的证据**。

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
- 删令牌：`DELETE /api/token/{id}` **可用**，走 user 作用域软删、**立即生效无需重启**；`record not found` 只说明「这次没删（本来就不在）」，**不能据此判定端点坏了**（复测已删对象必得此结果）。
- 改 option：`UserUsableGroups` 查 value 不查 key；非映射类 option 的 value 不是 JSON。
- **写操作后读 `success` 字段，不要只看 HTTP 码**（rc.26 大量「HTTP 200 + success=false + 一个字没改」）。
- 复用名前先确认软删记录：`name` 可能被 2026-08-11 那批用户手动软删的令牌占用，重建属越界。

关联 [[rotating-refresh-token-needs-single-writer]]。
