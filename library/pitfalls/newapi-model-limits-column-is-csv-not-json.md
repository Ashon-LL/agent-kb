---
name: newapi-model-limits-column-is-csv-not-json
description: New API tokens.model_limits 列存逗号分隔字符串，写 JSON 数组会让该令牌所有模型 403（解析出字面量 '["glm-5.2"'）；SQL 直改后必须重启刷缓存
type: pitfall
source: APIShow（2026-10-02 token 68 astron-group 全模型 403 实测）
date: 2026-10-02
verified: 2026-10-02
topic: api-gateway
---

# New API `tokens.model_limits` 是 CSV 字符串，不是 JSON 数组

同族条目：[[newapi-rc26-token-crud-shapes]]、[[newapi-disable-must-sync-abilities]]、[[third-party-db-columns-typed-by-reading-code]]。

## 症状：用 JSON 数组写进去 → 该令牌**所有**模型 403

```
{"error":{"message":"This token has no access to model deepseek-v4-pro
 (request id: ...)","type":"new_api_error"}}   HTTP 403
```

排查时容易误判为路由/abilities 问题——abilities 里 `enabled=1` 且指向正确渠道，
`channels.models` 也对，唯独这个令牌就是全挂。**先看 `model_limits` 的字面值**。

## 根因：列里存的是 `a,b,c`，不是 `["a","b","c"]`

```sql
-- ✅ 线上真实值（token 69 就是这个形态）
SELECT model_limits FROM tokens WHERE id = 69;  -- 'deepseek-v4.1-flash'
-- ❌ 我写进去的
'["glm-5.2", "deepseek-v4-pro", "spark-x2.5"]'
```

New API 按 CSV 切分，后者被切出的第一个元素是字面量 `["glm-5.2"`（带方括号和引号），
对不上任何模型名，于是该令牌的每个请求都在令牌鉴权层被判死。

**注意 JSON 形态在库里完全合法**（SQLite 弱类型收得下），所以**写入不报错、回读看着也对**，
只有真实请求才暴露。符合 [[third-party-db-columns-typed-by-reading-code]] 的规律：
一行的类型不符可以拖垮整列的读取。

## How to apply

- 写 `model_limits` 一律 `','.join(models)`，绝不用 `json.dumps`。
- 本地配置文件里存**逻辑列表**，生成线上 SQL 时才 join；单测断言本地值里不含 `[` / `"`。
- **`model_limits_enabled=0` 时该列内容完全不生效**，改它只为清理误导性残留。
- SQL 直改 tokens/abilities/options 之后**必须重启容器**（`docker restart apishow-new-api`），
  进程内有缓存；不重启会误判成「改了没用」。
- 容器无 Redis 时缓存只在进程内，重启是有效的；先 `docker exec ... env | grep -i redis`
  确认，别默认有 Redis。

关联 [[newapi-rc26-token-crud-shapes]]（该条目讲端点形状，本条讲列格式）。
