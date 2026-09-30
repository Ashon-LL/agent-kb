---
name: newapi-multikey-size-must-track-key-count
description: New API 多密钥渠道的 channel_info.multi_key_size 必须与 key 实际段数一致；只追加 key 文本不改 size 会把新钥当成上一把的后缀产生 401
type: pitfall
source: APIShow 商汤三账户钥纳入 ch29/ch167 多钥池
date: 2026-09-17
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

## Why

网关按 `multi_key_size` 切分 `key` 文本。只追加文本不改 size，网关按旧的 N 切，多出的一把会被并进最后一把的后缀里，生成一个长度错误、永远 401 的"伪 key"；`multi_key_status_list` 的长度也对不上，健康状态随之失真。这类损坏不会报错，只会静默表现为"随机 1/N 概率失败"，排查时极易误判成上游限流或某一把 key 过期。

同源事故：直改 `channel_info` 后出现 `unexpected end of JSON input`，New API 渠道扫描失败，整个渠道不可用——**`channel_info` 是自由 JSON 字段，拼一半写进去就把渠道搞挂**。

## How to apply

1. **给正在服务流量的多钥渠道加钥，先直连验证新钥**。`multi_key_mode=random` 时每把钥被选中的概率是 1/N；若渠道 `auto_ban=1`，N=3 时有 1/3 概率命中一把坏钥并被网关自动禁用——**整个渠道会被废掉**，而不是只跳过那一把。顺序固定为：直连验证 → 写库 → 重启 → 回读 → 走站 E2E。
2. 加钥必须走 SQL 直改（`admin` 面板的 key 编辑不会替你改 `multi_key_size`），写后 `docker restart <newapi 容器>`——网关有渠道配置缓存。
3. 回读校验三件事：`len(key.split("\n")) == multi_key_size`、每段长度符合该上游的 key 长度（商汤 35、OpenRouter 51 之类）、`channel_info` 能被 `json.loads`。
4. 验收要打到走站层：用真实 token 发 chat completion，看 logs 是否全落目标渠道、`type=2` 成功、渠道 status 没被 auto_ban 翻转。
5. 凭据库里有某把 key 的记录 **不等于** 线上在用——核对"是否已纳入"必须查 `channels.key` 的实际段数，不能只看凭据配置文件。
