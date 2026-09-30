---
name: newapi-rc26-channel-crud-shapes
description: New API rc.26 渠道 CRUD 端点形状与静默成功坑——POST /api/channel/ 要 {channel:{...},mode}、DELETE 走路径参数不是 ?id=、channel/test 要 admin Bearer（非免 token，不带一律 401 且与模型是否存在无关）、GET /api/option/ 的 data 是列表不是字典
type: pitfall
source: APIShow/New API rc.26（2026-09-28 修订补渠道 CRUD 端点形状）
date: 2026-09-17
verified: 2026-09-28

---

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

写回用 `PUT /api/option/`，body `{"key": "...", "value": "..."}`，**按 key 更新单个 option**——但 value 是整段 JSON，所以改 GroupRatio/ModelRatio 等映射类 option 必须：GET 原值 → 本地留副本 → normalize → 合并 → PUT 回完整值 → **回读验证全表**（键数 + 关键原键逐一对比备份，**不能只验新增键**——09-29 两次事故都是回读只查新键、原键被清空没发现）。参见 [[newapi-base-url-never-carry-v1]] 同目录的事故记录与记忆 `newapi-modelratio-wipe-20260826`。

## How to apply

- 建渠道：`{"channel": {...}, "mode": "single"}`，别指望 `data` 返回 id，反查。
- 删渠道：`DELETE /api/channel/{id}`，删完查孤儿 abilities。
- 验连通：`GET /api/channel/test/{id}?model=X`，**要 admin Bearer**；401 说明没带认证，与模型是否存在无关。
- 改 option：GET 是列表、**value 类型不稳定（dict/字符串混合）**，必须先 `isinstance` normalize；映射类 option 走 GET→留档→normalize→合并→PUT→**回读全表**（键数+原键 diff，不只看新增）六步。
- **任何写操作后读 `success` 字段，不要只看 HTTP 码**（rc.26 大量「HTTP 200 + success=false + 一个字没改」）。
- **写操作前必留档**（09-29 靠写前备份 30 秒救回全表）。
