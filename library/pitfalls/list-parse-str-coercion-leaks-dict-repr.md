---
name: list-parse-str-coercion-leaks-dict-repr
description: 解析上游模态数组时 str(x) 强转会把 dict 元素变成 repr 字符串泄漏进配置；对象数组必须按 type 字段提取
type: pitfall
source: OpenCode 供应商配置 GUI（provider_gui.py）拉取书生 discovery-api 模型（2026-11-25）
date: 2026-11-25
verified: 2026-11-25
topic: python, verification
---

**经验**：把上游 `/models` 响应归一化成内部记录时，模态数组（`input_modalities`）在不同网关形态不同：
OpenAI 风格是字符串数组 `["text","image"]`；书生 discovery-api 是**对象数组**
`[{"type":"text","supported_inputs":{...}},{"type":"image",...}]`。
用 `[str(x) for x in v]` 这类强转处理对象元素，会把整个 dict 变成 Python repr 字符串
（`"{'type': 'text', 'supported_inputs': {'max_context_length': ...}}"`）写进配置——
能力项整列变脏，且 `attachment = any(x in ins ...)` 判定全错（字符串子串匹配不上）。

**Why**：str() 对 dict 是 repr 泄漏，不是取值；下游 OpenCode 按字符串数组解析模态，
拿到 repr 垃圾后多模态声明静默失效。2026-11-25 实测：8 处脏数据（4 个数组的 text+image
两行）已写进 opencode.jsonc。

**How to apply**：
- 解析这类数组统一做双形态：`isinstance(x, dict)` → 取 `x.get("type") or x.get("id") or x.get("name")`；字符串照旧
- 写完配置必须回读断言：模态数组元素必须全在受控词表（["text","image","audio","video","pdf"]）内，出现 `{` 即脏
- 上游没给的字段保持 None，别用默认值冒充（输出长度上游没给就是没给，打「?」不编造）
