---
name: newapi-base-url-never-carry-v1
description: New API 渠道 base_url 只写 host，/v1 由网关自动拼；带 /v1 会拼成 /v1/v1 报 404，且 /v1/models 显示正常也证明不了 base_url 对
type: pitfall
source: APIShow unoRouter 8 路漏斗接入（ch168-175）
date: 2026-09-17
---

## 经验

New API（one-api 衍生）建渠道时 `base_url` 只写到 host[:port] 或上游 API 前缀（如 `https://openrouter.ai/api`），**绝不要再带 `/v1`**。网关会自动拼 `/v1/chat/completions`，写成 `https://xxx.com/v1` 后实际请求变成 `https://xxx.com/v1/v1/chat/completions`，返回 `404 Invalid URL (POST /v1/v1/chat/completions)`。

## Why

用户给的上游地址通常就是完整可打的路径（`https://host/v1/chat/completions`），直觉照抄即错。错误只在**首包实打**时暴露，而常规验收是先看渠道列表与模型列表——两者都不向上游发包，全是绿的。`/v1/models` 只查 abilities 路由索引，base_url 写错它照样 200 且模型在列。

## How to apply

1. 建渠道前先拿一条**已验证在跑**的同类渠道对照 base_url（同上游类型、同网关版本），抄它的路径深度，不要从上游文档抄完整 URL。
2. 验收必须**实打一次 chat completion**：HTTP 200 且有可见 content 才算接上。绝不用 `/v1/models` 或渠道列表页当验收证据。
3. 判据一句话：404 且错误信息里出现重复路径段（`/v1/v1/`），就是 base_url 多带了前缀，把尾部的 `/v1` 去掉。
4. 修：`UPDATE channels SET base_url=? WHERE id=?;` 之后必须 `docker restart <newapi 容器>`——New API 有渠道配置缓存，不重启不生效。
5. 多上游漏斗（一个售卖名映射 N 条渠道）时，实打要打 N 次以上才能覆盖到全部分支，单次 200 不代表 8 条都对。
