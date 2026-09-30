---
name: config-field-name-is-not-spec-read-consuming-code
description: 第三方软件配置字段名不是规格：名字极像的字段各管一件事、声明式列表的"缺项"会静默清掉不相关的能力、默认值常在代码不在配置；改前 grep 消费点读判定分支，改后必做请求体捕获实打，别拿启动日志当验收
type: pitfall
source: APIShow/AstrBot v4.27.4 上下文与工具调用事故（2026-09-17 至 09-18，工具调用静默消失一整天）
date: 2026-09-18
verified: 2026-09-17
---

**经验**：第三方软件的配置字段名是给运维看的提示，不是行为规格。三类典型错位，且**三类都零报错、零警告**：

1. **名字极像、各管一件事**——改错那个毫无提示，你以为改了 A 其实改了 B。
2. **声明式列表的"缺项"有副作用**——不是"没启用某能力"，而是**主动清掉一件你不相关的事**。这是最隐蔽的一类。
3. **默认值在代码里不在配置里**——你把配置里的键删掉，它会回落到代码里的硬编码默认，而不是变成"关闭"。

**Why**：AstrBot 上四条实测实例，全部零报错——

- ⭐ **`provider[N].modalities` 缺项清工具**：本意是开读图，把 `[]` 改成 `["text","image"]`。而 `tool_loop_agent_runner.py:_func_tool_for_provider` 的判定是
  `if isinstance(modalities, list) and modalities and "tool_use" not in modalities: return None`
  ——**非空列表里缺 `tool_use` 就把整个请求的工具集清空**。结果工具调用静默死了整整一天：模型想调 `get_zhiqing_chat` 却发不出 `tool_calls`，只能输出思考文字。反向印证更讽刺：`modalities: []` 时条件是假的、工具是通的。改 `[]→["text","image"]` 看起来是"增加能力"，实际是"关闭工具"。
- **`sanitize_context_by_modalities` 是"按声明裁剪"不是"无条件清理"**：只剥掉模态声明里**没有**的能力（缺 image 才把图片块换成 `[Image]`，缺 `tool_use` 才把 `tool` 消息转成 user 占位并 pop assistant 的 `tool_calls`）。声明含 image 时开它，对图片**毫无作用**——我据此把它当根治 base64 内联的手段，实测无效。它和 `modalities` 是配套生效的：先补齐 `tool_use`，开它才安全。
- **`fallback_chat_models` 收 provider id 不收模型名**：填模型名只打一行 warning 就静默跳过，兜底等于不存在。
- **`max_context_length` 是回合数上限不是 token**：设 49152 等于把对话压到 49 轮。而 `fallback_max_context_tokens` 默认 128000 写在 `internal.py` 里，配置里删掉它不会变成"无上限"、而是回落到 128000。
- **相邻类——参数名不代表时效性**：`trusted_token_usage` 听起来是"权威的当前总 token"，实际是 `tool_loop_agent_runner.py:805` 读的**上一轮**响应的 total_tokens（本轮 `:859` 才写回），而 `token_counter.py:49` 是 `if trusted_token_usage > 0: return trusted_token_usage` 直接短路返回。上下文暴涨那一轮的闸门看到的还是上一轮的小值——**该压缩的那一轮必然漏判**，且没有任何日志告诉你。
- ⭐ **第四类：宿主写了配置键，插件却把自己的策略硬编码在消费代码里 ⇒ 该键没有消费者**（2026-09-28，openclaw 社区渠道插件 `openclaw-weixin`）：我在宿主的 `channels.<id>` 里写 `dmPolicy` / `allowFrom`（并据此做了一整套「白名单 / 配对」设置页），而插件在 `dist/src/messaging/process-message.js` 里**写死** `dmPolicy: "pairing"` + `configuredAllowFrom: []`，放行判定走它自己的 `<credDir>/<channel>-<accountId>-allowFrom.json`，为空则回退用**登录账号自己的 userId**（`loadWeixinAccount()`）⇒ 用户「扫一下就行」是对的，我那个输入框是**让用户填一个不生效的字段**。同类信号：插件里 `registerUserInFrameworkStore()` 被 **export 但全 dist 无人调用**（`grep -rn` 只有定义处）。⚠️ 与第 3 类同源：默认值/判定在代码里，配置只是宿主的一厢情愿。

**How to apply**：

1. **改任何配置字段前**，先 `grep -rn '<字段名>' <安装目录>` 找全部消费点，读判定分支——重点看 `if not X`、`X not in Y`、`isinstance(...) and ...` 这类**隐式副作用**分支，它们才是字段名的反话。
2. **给用户的 UI 字段必须先证明它有消费者**：`grep` 到「只有定义/只有导出、无调用点」就等于没消费者——那就别做输入框（用户会填、填了不生效、还以为配错了）。判断链：配置键 → 消费点 → 判定分支 → 实弹一次。
   ⭐ **同族的第五类：UI 提示的单位 ≠ 引擎认的单位（2026-09-29 实锤，用户当场踩到）**——预设表单的输入框写着「Compact 阈值（可选，**0~1**）」，用户照填 `0.95`；而引擎的唯一判定是 `thr_raw.isdigit() and 20 <= int(thr_raw) <= 95`，`"0.95".isdigit()` 为假 ⇒ **静默回退 80**。界面上看着「我填了 95%」，实际按 80% 跑，**零报错**；而且同一个量在另一张卡片上的提示是「默认 80（用到上限的 80% 即开始压缩）」——**两个提示本身就自相矛盾**。⇒ 判据：任何带单位的输入框，提示语必须与**消费方解析代码**逐字对齐（范围 + 类型，如「20~95 的整数」）；`grep` 出解析函数读它的 `isdigit()/isinstance()` 才算数。**别信 placeholder**——它是文案，不是规格。反向守卫：给这个输入框写一条「placeholder 必须含真实范围、不得含旧单位」的源码契约用例（只判**该输入框的 placeholder**，别判全文——解释性注释可能正当地提到旧单位，按全文判会误伤）。
3. **改声明式列表字段的值时，逐项检查"缺某项"会触发什么**，而不是只看"加了某项"的效果。补一项可能同时关掉另一项。
4. **改完必须做一次「请求体捕获」实打，启动日志通过不算验收**——启动日志几乎永远不报错。做法：monkeypatch 出站 `client.chat.completions.create` 记录 `kwargs`，用软件**自己的类**在进程内跑一次，断言目标键真的上线路。本次实测 `extra_body = {"max_tokens": 32768, "reasoning_effort": "high"}` 才算数。
5. **验证"某能力是否真的没在跑"时，反向验证**：用一个已知应该触发的输入（比如超大上下文 + 已知的 trusted 值），确认它触发了；再用一个已知不应该触发的输入确认它没触发。只测单向会漏掉"恒假"类缺陷。
6. **别拿缓存值当"没坏"的证据**：任何"上一轮写入、本轮读取"的值都可能已过期，先确认它的写入点在读点之后。
7. 汇报时严格区分**"改了配置"**和**"实测上了线"**——前者是动作，后者才是结果。

**相邻教训**：字面语义同样不是规格，见 [[log-text-is-not-spec-read-emitting-code]]（日志文案）；改了旋钮却不生效的取值类见 [[reasoning-model-max-tokens-shares-budget]]（`max_tokens` 被思考吃满后 `content` 键直接消失）。
