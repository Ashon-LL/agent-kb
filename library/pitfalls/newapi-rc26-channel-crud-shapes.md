---
name: newapi-rc26-channel-crud-shapes
description: New API rc.26 渠道 CRUD 端点形状与静默成功坑——POST 要 {channel:{...},mode}、DELETE 走路径参数且是硬删（channels 无 deleted_at）、channel/test 要 admin Bearer、GET /api/option/ 的 data 是列表不是字典
type: pitfall
source: APIShow/New API rc.26（2026-09-28 修订补渠道 CRUD 端点形状）
date: 2026-09-17
verified: 2026-10-12
topic: api-gateway

---
<!-- hook-reviewed 2026-10-20：已人工确认 INDEX 钩子覆盖本条全部更新内容 -->


# New API rc.26：渠道 CRUD 端点形状

rc.26 实测（apigogo 生产库 `/opt/apishow/data/one-api.db`）。同族条目：[[newapi-base-url-never-carry-v1]]、[[newapi-disable-must-sync-abilities]]、[[newapi-multikey-size-must-track-key-count]]。

## POST /api/channel/ —— 必须包一层 + 必须给 mode

```
# 错误：channel cannot be empty
POST /api/channel/   body = {"name": "...", "models": "..."}

# 错误：不支持的添加模式
POST /api/channel/   body = {"channel": {...}}

# 正确
POST /api/channel/   body = {"channel": {...}, "mode": "single"}
```

**坑**：成功响应是 `{"success": true, "data": null}` —— **`data` 为 null，拿不到新建 id**。必须再用 `GET /api/channel/` 按 `name` 反查 id。

## DELETE /api/channel/{id} —— 路径参数，不是查询串

```
# 错误：HTTP 404（路由不存在）
DELETE /api/channel/?id=4

# 正确
DELETE /api/channel/4
```

删除后 `abilities` 由 rc.26 自动重建（`InitChannelCache` 一族），**孤儿行需回读确认**：

```sql
SELECT COUNT(*) FROM abilities a
LEFT JOIN channels c ON c.id = a.channel_id WHERE c.id IS NULL;
```

### ⛔ 渠道删除是**硬删除**，与 token 的软删语义相反

```
DELETE /api/channel/177   ->  {"message":"","success":true}
SELECT COUNT(*) FROM channels WHERE id=177;   -- 0，真的没了
```

**`channels` 表没有 `deleted_at` 列**（只有 `tokens` 有），所以渠道删除是**物理删除、不可恢复**——
别被 `success=true` 误导成「可回滚的软删」。2026-10-02 删 ch177 实测：
渠道行 0、abilities 0，但 `logs` 里 `channel_id=177` 的 **79 条历史日志完整保留**（日志表不级联）。

对比：`tokens` 有 `deleted_at`，且 rc.26 的 `DELETE /api/token/{id}` 读错参数恒假失败
（见 [[newapi-rc26-token-crud-shapes]]），真删只能 SQL 软删。**两张表的删除语义完全不同，别互相类比。**

删前必做三查：① `abilities WHERE channel_id=?` 应已零行 ② 该渠道所属 `group` 的其他模型是否另有供给
（否则断供）③ 名字双确认（`id` + `name` 都对得上，防 id 复用误删）。

渠道 `status` 语义见 [[newapi-disable-must-sync-abilities]]：`1`=Enabled、`2`=ManuallyDisabled、`0`=Unknown（API 只收 1/2，传 0 是**假成功**）。

## GET /api/channel/test/{id}?model=X —— **必须 admin 认证**，连通性验证首选

**需要 admin Bearer token**，不是免 token：

```
POST /api/user/login  body={"username":..,"password":..}  -> data.access_token
GET /api/channel/test/{id}?model=X
    Authorization: Bearer <access_token>
    New-Api-User: <admin username>
```

不带认证一律返回 **401 `AUTH_UNAUTHORIZED`**，而且**有效模型与非法模型返回完全一样** —— 这是纯认证墙，不是模型信号，别拿它当探测结论（本轮就是被这个坑了一次：以为 401 代表模型不存在）。

模型确实被拒时返回 HTTP **200** + `error_code: bad_response_status_code`，上游/adapter 的真实报错在 `message` 里。

注意它**会真的发上游**（计费/计次），别拿来做批量探测。

## GET /api/option/ —— `data` 是列表不是字典（曾清空全站 ModelRatio）

```json
{"success": true, "data": [{"key": "ModelRatio", "value": "{...}"}, ...]}
```

`data` 是 **`[{key, value}, ...]` 列表**（约 235 项），**不是** `{"ModelRatio": ...}` 字典。把列表当字典解析会得到空值 → 空 PUT → 整表覆盖清空。

⚠️ **value 类型不稳定（两次事故的根）**：实测 `GET /api/option/` 里**部分键 value 返回已是 dict 对象**（`UserUsableGroups` / `ModelRatio` / `CompletionRatio`），**部分键是 JSON 字符串**（`GroupRatio`）。**必须先 normalize 再合并**：

```python
def norm(v):
    if isinstance(v, str):
        try: return json.loads(v)
        except Exception: return v
    return v   # dict/list 直接返回，绝不对对象再 json.loads
```

对已是 dict 的 value 直接 `json.loads(obj)` 会抛 `TypeError`；若脚本用 `except: return {}` 吞掉 → 合并后只剩新增键 → PUT 整表覆盖 → **清空全表**。此坑 2026-08-26（ch118 清空全站 ModelRatio）与 **2026-09-29（ch178：ModelRatio 312→5、CompletionRatio 94→5、UserUsableGroups 5→1，症状=所有非 default 组 token 403「无权访问 X 分组」）各犯一次**，均为 kb 原文「value 是 JSON 字符串」误导所致——现更正为「类型不稳定，须 isinstance 判断」。

写回用 `PUT /api/option/`，body `{"key": "...", "value": "..."}`，**按 key 更新单个 option**——但 value 是整段 JSON，所以改 GroupRatio/ModelRatio 等映射类 option 必须：GET 原值 → 本地留副本 → normalize → 合并 → PUT 回完整值 → **回读验证全表**（键数 + 关键原键逐一对比备份，**不能只验新增键**——09-29 两次事故都是回读只查新键、原键被清空没发现）。同族全景（四类静默事故 + 标准六步）见 [[redacted-get-full-put-wipes-secrets]]；另参见 [[newapi-base-url-never-carry-v1]] 与记忆 `newapi-modelratio-wipe-20260826`。


## PUT /api/channel/ —— **是 PATCH + GORM 非零字段更新**（2026-10-12 读源码定谳，推翻 2026-10-01 旧结论）

```go
// controller/channel.go
channel := PatchChannel{}          // PATCH 语义：未提供的字段保持零值
...
if _, ok := requestData["status"]; ok { /* 显式拒绝改状态 */ }
originChannel, _ := model.GetChannelById(channel.Id, true)
channel.ChannelInfo = originChannel.ChannelInfo   // ChannelInfo 强制沿用原值
// model/channel.go
err = DB.Model(channel).Updates(channel).Error    // ← GORM：只写非零字段
channel.UpdateAbilities(nil)                      // ← 保存后无条件重建 abilities
```

**结论（三件事，全都反直觉）**：

1. **稀疏 body 是安全的**：`{"id":176,"name":"..."}` 这种只带少数字段的 PUT **不会**把
   `key`/`base_url`/`group` 清零——GORM 的 struct `Updates` 跳过零值。实测：6 条渠道 PUT 后
   DB 回读 `key` 长度 / `status` / `group` 一字未变。
2. **反过来也成立：无法用这个端点把字段清空**（空字符串/空对象是零值，会被静默跳过）——
   想清空 `model_mapping` 只能给非空值或走 SQL。
3. **`status` 被控制器显式拒绝**（body 里带 `status` → `MsgInvalidParams`），改状态用
   `PUT /api/channel/{id}/status`（body `{"status":1|2}`，只收这两个值）。

**⛔ 2026-10-01 旧结论「PUT 不落 models，必须 SQL + 重建 abilities + 重启」已被推翻**：
当时用的是 `{"channel": {...}, "id":.., "mode":"update"}` 包裹形状（POST 的形状套在 PUT 上），
字段没绑进 `PatchChannel` ⇒ 看起来「success=true 但什么都没改」。**正确形状是扁平 body**：
`PUT /api/channel/` body `{"id": N, "models": "a,b", "model_mapping": "<json 字符串>"}`
（`models` 与 `model_mapping` 都必须是**字符串**，数组/对象直接 unmarshal 报错）。
走这个形状：models 落盘、abilities 自动重建（`UpdateAbilities` + `InitChannelCache`）、
**无需重启**。2026-10-02 与 2026-10-12 两轮共 11 条渠道实测一致。

**PUT 响应里 `key` 显示为 `''` 是回显脱敏，不是把 key 写空了** —— 但仍要回读 DB 核对 `key` 与预期真值一致。

**摘除模型时的收尾动作**（少一步就是「视图摘除」）：渠道 `models` 删名 → **同批删该模型的
`model_mapping` 死键**（键不在本渠道白名单内即永不路由，留着会让已摘模型看起来仍在供）→
渠道 `name` 里的模型计数 → `UserUsableGroups` 分组描述里逐模型列名的字符串 → 本地目录条目降级为
**墓碑**（groups/adapters 皆空，保留沿革）。

**token 的 PUT 更危险**，见 [[newapi-rc26-token-crud-shapes]] 与 [[redacted-get-full-put-wipes-secrets]]：改 token **只能 `POST` 删旧建新**，绝不 PUT。


## How to apply

- 建渠道：`{"channel": {...}, "mode": "single"}`，别指望 `data` 返回 id，反查；`channel_info` 传对象、`model_mapping` 传 JSON 字符串。
- **改渠道模型清单：`PUT /api/channel/` 扁平 body `{id, models, model_mapping}` 即可落盘并自动重建 abilities（免重启）**；`models`/`model_mapping` 传字符串、别带 `status`；写后回读 DB 核对 key 长度/status/group。
- 删渠道：`DELETE /api/channel/{id}`，删完查孤儿 abilities。
- 验连通：`GET /api/channel/test/{id}?model=X`，**要 admin Bearer**；401 说明没带认证，与模型是否存在无关。
- 改 option：GET 是列表、**value 类型不稳定（dict/字符串混合）**，必须先 `isinstance` normalize；映射类 option 走 GET→留档→normalize→合并→PUT→**回读全表**（键数+原键 diff，不只看新增）六步。
- **任何写操作后读 `success` 字段，不要只看 HTTP 码**（rc.26 大量「HTTP 200 + success=false + 一个字没改」）。
- **写操作前必留档**（09-29 靠写前备份 30 秒救回全表）。
