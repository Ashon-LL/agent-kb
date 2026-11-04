---
name: trae-remote-query-500kb-bytes-silent-close
description: Trae remote 上游对初次打平的 query 有 ~500KB(UTF-8 字节) 硬顶，超了静默关流无 done；Max 档是真的（model_name 变 xxx__max、max_tokens=1M），但字节墙先撞，1M 用不上；按字符裁剪的网关在中文场景必挂
type: pitfall
source: APIShow Trae 上下文实测（2026-10-30）：model_config/token_usage 事件 + 逐档载荷对照 + relay 补丁验证
date: 2026-10-30
verified: 2026-10-30
topic: llm
---

# Trae remote：真正的墙是 query 的 ~500KB UTF-8 字节，不是 chars、不是 token、也不是 1M 窗口

## 结论（2026-10-30 实测定谳）

1. **Max 档真实存在**：同一账号开 Max 时上游 `model_config` 事件返回 `model_name=glm-5.3__max`、
   `max_tokens=1000000`；关 Max 返回 `glm-5.3__dev`、`max_tokens=200000`。`edition=cn` 免费号也能拿到 `__max`。
2. **可用载荷的硬顶是 `initial_message.query` 的 UTF-8 字节 ≈ 500KB**，与 token 数无关：

   | 载荷 | 字符 | UTF-8 字节 | 结果 |
   |---|---|---|---|
   | 英文 | 497,700 | 497,700 | 200 + done |
   | 英文 | 514,950 | 514,950 | 200 + done |
   | 英文 | 534,975 | 534,975 | 静默断流（无 done） |
   | 中文 | 149,996 | 449,988 | 200 + done |
   | 中文 | 174,988 | 524,964 | 静默断流（无 done） |
   | 中文 | 199,980 | 599,940 | 静默断流（无 done） |

   ⇒ 社区流传的「~50 万 chars」只是**英文场景**的经验值（1 char≈1 byte）；中文按 3 字节/字，字符数要除以 3。
3. **按字符裁剪的网关在中文场景必挂**：`_bounded_remote_query` 若以 `len(query)` 比 480,000 chars，
   中文 480K 字 = 1.44MB，预检放行 → create_session 之后上游静默关流 → 502「ended without a done event」，
   且会逐账号重放成整池 502。
4. **上限精确到 512KiB（524,288 B），且是应用层 body 限制**：514,950 B 过、524,964 B 挂。
   实测三条绕过全部无效：`Transfer-Encoding: chunked`（540KB 仍静默断流）、把长文本放进
   `initial_message.content` 数组（agent 档忽略，暗号读不到、ptok 仅 20K）、回传 `chat_session_id`
   续会话（上游仍新建 session）。桌面端能用到 1M 是因为它按轮次增量提交、上下文留在服务端会话里。
5. **Max 档要在 relay 里真正启用，必须放宽 descriptor 判据**：上游 `descriptor_supports_max_mode()`
   要求 descriptor 同时带 `prompt_max_tokens` + `max_tokens`，而 web 目录只给
   `context_window_tokens.{dev,max}` ⇒ 永远 false、面板「1M 上下文」开关空转。
   改成「`max_mode=true` 且 `max>=1M`」即可生效（实测返回 `<model>__max` / `max_tokens=1000000`）；
   Max 只在 512KiB 载荷范围内提升窗口，不会突破 body 上限。

## Why

- 失败形态是**静默断流**（无错误帧、无 done），不是 413/400，极易误判为上游故障或账号问题；
- 判据混用「chars / tokens / 声明窗口」都会得出错误边界：英文过、中文挂，看起来像"模型窗口不同"，
  实际是同一条 500KB 字节线；
- 上游项目的 `descriptor_supports_max_mode` 要求 descriptor 同时给 `prompt_max_tokens` + `max_tokens`，
  而 web 目录只给 `context_window_tokens.{dev,max}` ⇒ 面板「1M 上下文」开关永远走不到下发（空转）。

## How to apply

- 网关裁剪一律按 **UTF-8 字节**（`len(s.encode("utf-8"))`），预算取 **470~480KB**；别用 `len(str)`。
- 客户端 contextWindow 换算：110K tokens ≈ 中文 150K 字（450KB）/ 英文 470K 字；再大就会撞墙。
- 想让 Max 生效：把 `descriptor_supports_max_mode` 的判据放宽到 `max_mode=true && max>=1M`，
  然后看 `model_config.model_name` 是否带 `__max` 验证。
- 排障口诀：先算**字节**，再看 token；「ended without a done event」先怀疑载荷超 512KiB。

## 破解路线（2026-10-30 已验证）

1. **增量发消息而非全量重发**：桌面端连续对话用的是
   `POST /api/remote/v1/chat_sessions/{id}/messages`，历史留在服务端会话里。
2. **body 形状是关键**（发裸文本一律 500/409）：`query` 必须是
   `flatten_query_parts` 产出的 **JSON 数组字符串**，同时带
   `chat_session_id / content:[] / model_name / agent_type=solo_agent_remote /
   agent_id / model_selection_strategy / custom_model / common_params / origin:"web"`。
3. **会话状态**：`create_session` 后正常读完首轮；之后 `send_message` 返回新
   `message_id`，继续订阅 `chat_sessions/{id}/events?reply_to_message_id=<new>` 即可；
   回答里能复述首轮埋的数字 ⇒ 上下文确实在服务端保留。
4. **落地**：relay 记 (model, 账号, 首条 user 文本) → 会话映射，命中只发增量；
   实测两轮总历史 657KB（>512KiB）仍 200，104K prompt tokens。失败即回落全量 create。
5. **env**：`remote`（云端沙箱，每次新会话）与 `local`（正常模式）都支持增量；
   站主要求用 `local`。
6. **别走 IDE 原生通道**：magpie 插件的 `/api/agent/v3/llm_utils_chat` 需要登录时
   注册过的 device_id/machine_id，自造设备会被 4011 限流拒。
