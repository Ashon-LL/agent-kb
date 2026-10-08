---
name: newapi-multikey-size-must-track-key-count
description: New API 多密钥渠道的 channel_info.multi_key_size 必须与 key 实际段数一致；只追加 key 文本不改 size 会把新钥当成上一把的后缀产生 401；10-08 起加钥首选原生 PUT（GET 掩码→回填真钥→禁带 status→自动重建 size/BLOB→免重启）
type: pitfall
source: APIShow 商汤三账户钥纳入 ch29/ch167 多钥池；ch29 加 wym0918（2026-10-08）
date: 2026-09-17
verified: 2026-10-08
topic: api-gateway, security
---

## 经验

New API 的多密钥渠道有两处状态必须一致：`channels.key` 是 `\n` 分隔的多钥文本，`channels.channel_info`（JSON）里的 `multi_key_size` 记录段数，另有 `is_multi_key`、`multi_key_mode`、`multi_key_polling_index`、`multi_key_status_list`。给渠道追加一把 key，**必须同时把 `multi_key_size` 从 N 改成 N+1**，并重启容器刷缓存。

写之前先断言现状自洽，写之后断言新状态自洽：

```python
segs = old_key.rstrip("\n").split("\n")
assert len(segs) == ci["multi_key_size"]          # 旧状态自洽，否则先别写
new_key = old_key.rstrip("\n") + "\n" + new_one
assert len(new_key.split("\n")) == len(segs) + 1  # 新状态自洽
ci["multi_key_size"] = len(segs) + 1
json.dumps(ci, ensure_ascii=False)                # 必须能被解析回来
```

## 2026-10-08 反转：加钥首选原生 API PUT（免 SQL、免手工 size、免重启）

实测（APIShow ch29 加 wym0918，5→6 钥）：**一次原生 PUT 即可加钥并自动重建一切**，老路「SQL 直改 + 手工同步 multi_key_size + 重启」不再需要：

1. ⛔ `GET /api/channel/{id}` 返回的 `key` 是**掩码（空串）**——直接全量 PUT 会把多把真钥抹空。正解＝**SQL 只读**取 `channels.key` 真值回填进 PUT 载荷（只读取数，不算写库）。
2. ⛔ PUT 载荷**不能带 `status` 字段**：一旦带就回 `{"message":"Invalid parameters"}`；省略＝部分更新，`status` 保持原值（实测仍 1）。
3. 载荷最小集＝`{id, name, type, models, model_mapping, group, base_url, key}`（`key`＝旧钥全部 `\n` 拼接后追加新钥；`name` 一并生效——**「PUT 不落 name」旧结论作废**）。
4. Handler 会**按新 key 自动重算** `channel_info`（`is_multi_key`/`multi_key_size`）并以 **BLOB(bytes)** 写回——手工 size 同步与 `json.dumps().encode()` 都不再需要。
5. PUT 后**无需重启**：原生 API 路径自动 `InitChannelCache()`。回读断言：key 段数==N+1、`multi_key_size`==N+1、`status` 未变、容器日志零 Scan error。

（上述信息为 2026-10-08 在 rc.26 实测；据 AGENTS.md 的源码定谳，原生 API 改渠道会触发 abilities 重建与缓存刷新，本次 key 变更未改模型故 abilities 原封。）

## Why

网关按 `multi_key_size` 切分 `key` 文本。只追加文本不改 size，网关按旧的 N 切，多出的一把会被并进最后一把的后缀里，生成一个长度错误、永远 401 的"伪 key"；`multi_key_status_list` 的长度也对不上，健康状态随之失真。这类损坏不会报错，只会静默表现为"随机 1/N 概率失败"，排查时极易误判成上游限流或某一把 key 过期。

同源事故：直改 `channel_info` 后出现 `unexpected end of JSON input`，New API 渠道扫描失败，整个渠道不可用——**`channel_info` 是自由 JSON 字段，拼一半写进去就把渠道搞挂**。

## How to apply

1. **给正在服务流量的多钥渠道加钥，先直连验证新钥**。`multi_key_mode=random` 时每把钥被选中的概率是 1/N；若渠道 `auto_ban=1`，N=3 时有 1/3 概率命中一把坏钥并被网关自动禁用——**整个渠道会被废掉**，而不是只跳过那一把。顺序固定为：直连验证 → 写库 → 重启 → 回读 → 走站 E2E。
2. 加钥**首选原生 API PUT**（见上文「2026-10-08 反转」节：GET 掩码 → SQL 只读回填 → 载荷禁带 `status` → handler 自动重建 size/BLOB → 免重启）。确需 SQL 直改时才走老路：同步 `multi_key_size` + `docker restart <newapi 容器>`（网关有渠道配置缓存）。
3. 回读校验三件事：`len(key.split("\n")) == multi_key_size`、每段长度符合该上游的 key 长度（商汤 35、OpenRouter 51 之类）、`channel_info` 能被 `json.loads`。
4. 验收要打到走站层：用真实 token 发 chat completion，看 logs 是否全落目标渠道、`type=2` 成功、渠道 status 没被 auto_ban 翻转。
5. 凭据库里有某把 key 的记录 **不等于** 线上在用——核对"是否已纳入"必须查 `channels.key` 的实际段数，不能只看凭据配置文件。
