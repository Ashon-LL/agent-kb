---
name: verification-script-ua-can-fake-a-config-failure
description: 用自制脚本验证外部模型源时，脚本自身的默认 UA 会被 Cloudflare 1010 拦截，造成"配置不可用"的假失败；判失败前必须先排除探针自身
type: pitfall
source: MH-Agent-Open 切换执行器上游至新源的实测（2026-09-19 01:00）
date: 2026-09-19
---

**陷阱**：拿着新配置去验证，脚本报 HTTP 403 —— 很容易直接下结论「key 无效 / 源不可用 / 用户配错了」。真因常常在**探针自己身上**。

## 实测对照（同一端点、同一 key、同一模型，只改 UA）

| 探针 | UA | 结果 |
|---|---|---|
| Python `urllib.request`（默认 `Python-urllib/3.13`） | 无 UA | **403** `Cloudflare error 1010` |
| Python urllib + 浏览器 UA | Chrome 串 | **200** |
| Python urllib + `curl/8.4.0` | curl 串 | **200** |
| Node fetch / **undici 8.x（完全不带 UA）** | 无 UA | **200** |
| Node fetch + `UA=undici` | undici | **200** |
| Python **`http.client.HTTPSConnection`（headers 只有 Authorization/Content-Type，无 UA）** | 无 UA | **200** |

⇒ **Cloudflare 拦的是「像 python urllib」的那一种指纹，不是「没有 UA」**。undici 不带 UA 反而放行，`http.client` 裸连也放行。

⛔ **同一个服务里不同角色可能走完全不同的 HTTP 客户端**，别拿一条路径的结论去覆盖另一条。本仓实测三条：`reviewer` = `http.client`（无 UA）/ `editor_ai` = `httpx`(`direct_api.py` 已覆写 UA) / 执行器 = Node `undici`。判连通前先 grep 出**那条路径自己的底层客户端**。

## 三条可操作规则

1. **探针报 4xx 时，先做 header 对照再改结论。** 最少测三组：裸默认 UA / 浏览器 UA / 目标组件真实用的客户端（Node 就用 Node 跑，别用 Python 代跑 Node 的链路）。
2. **用谁家的客户端就用什么验证。** 目标链路是 Node/undici，就用 `node xxx.mjs`（用安装区自带的那个 node，别用系统 PATH 里的）；拿 Python 去代跑 Node 的链路，等于用一个不同的客户端做结论。
3. **先读目标代码里已有的防御。** 本仓在 `backend/routers/proxy.py:156` 与 `backend/llm/direct_api.py:11` 早写了注释「httpx 默认 UA(python-httpx) 被 1010 拦截」，并统一覆写了浏览器 UA —— 真实链路早就处理了，只有我的临时探针没跟上。**读到这类注释就别再怀疑配置本身。**

## 顺带的卫生要求

含密钥的一次性脚本**用完即删**（`rm -f`），别让 `sk-...` 残留在 `/tmp`；也不要把密钥拼进 bash argv（会进 shell history）—— 走「Python 读库 → 写临时 json → Node 读 → 删 json」这种闭环。

## 相关

- `newapi-base-url-never-carry-v1.md` —— 同为"配上去看着对但就是用不了"类
- `verify-with-real-pipeline-and-readonly-probes.md` —— 探针与真实链路的差距
