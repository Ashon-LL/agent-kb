---
name: disguised-client-gate-needs-placeholder-tools-merged-not-replaced
description: 免费档「伪装官方客户端」门禁常按模型要求占位工具（bash/read）在场；网关在客户端自带 tools 时整表替换掉占位工具 ⇒ 该族模型全 403/502。修法=合并（去重）而非替换；接入每个新 -free 模型前跑「只带真实工具 / 占位+真实」对照矩阵
type: pitfall
source: APIShow / opencode-adapter（zen 免费车道，2026-10-08 实测）
date: 2026-10-08
verified: 2026-10-08
topic: methodology
---

# 伪装客户端门禁：占位工具必须「在场且合并」，不能替换（2026-10-08）

## 症状与误判

免费档上游（如 opencode.ai/zen）为防纯 API 直调，按「官方客户端形状」放行。形状里除了
规范会话 id、UA 头，还常含**占位工具**（`bash`/`read`，描述写「Reserved for the host runtime」）。
网关/中转常见写法：

    if not body.get("tools"):
        body["tools"] = GATE_TOOLS          # ⛔ 客户端带 tools 时被跳过

⇒ 一旦真实客户端（ZCode / Claude Code 等 agent 模式）发来自己的 `tools`，占位工具被**整表替换掉**，
上游按「形状不合规」拒——错误是 **403 FreeTierError / "can only be used from within X"**，
不是「模型坏了」。典型伪装：纯聊天（无 tools）正常、一进 agent 模式就 502（网关把上游 403 包成 502）。

## 关键事实：门禁是**按模型**的，不是全局一致

实测同一上游四个免费模型：

| 请求形状 | step-5-preview-free | longcat-2.5-preview-free | mimo-v2.6-flash-free | space-bunny-free |
|---|---|---|---|---|
| 只带真实工具（无 bash/read） | 403 | 403 | 403 | **200** |
| 占位工具 + 真实工具合并 | 200 | 200 | 200 | 200 |

⇒ **不能靠「某模型能过」推断整族能过**；宽松模型会掩盖缺陷。必须逐模型对照。

## 修法与纪律

1. **合并而非替换**：`tools = GATE_TOOLS + [t for t in client_tools if not is_gate_tool(t)]`
   （去重；无客户端工具时仍加占位并 `tool_choice:"none"`）。
2. **接入每个新 -free 模型前，先跑对照矩阵**：`{只带真实工具, 占位+真实}` × 新模型，
   判定它是否属强制门禁族——别等线上用户报错。
3. **确认模型不会误调占位工具**：合并后实测 `finish_reason=tool_calls` 且 `tool_calls[].name`
   只出现真实工具名（占位工具描述为保留用途，模型通常不选）。
4. **协议族要单独定**：同一上游不同模型走不同端点（chat vs responses）；
   给错端点会得 `ModelProtocolUnsupported`，别把它当模型故障。
5. **探针别用退化输入**：探测图片能力时用 1×1 退化 PNG 会得 400 `input_invalid` 假阴性——
   换成合法尺寸 PNG 才反映真实能力（本次踩过）。

## 相关

[[gateway-tool-choice-string-only-and-no-cooldown-on-client-errors]]（同族「上游只认一种请求形状，写错全挂」）、
[[model-rename-without-rule-sync-loses-capabilities]]（工具能力声明三处同步）、
[[redacted-get-full-put-wipes-secrets]]（同类「静默整表覆盖」反模式）
