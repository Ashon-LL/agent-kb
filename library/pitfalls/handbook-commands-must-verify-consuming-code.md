---
name: handbook-commands-must-verify-consuming-code
description: 手册/文档里的 API 调用命令写之前必须核到返回结构与参数契约键，凭记忆写会静默出错
type: pitfall
topic: methodology
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：写操作手册/文档里的 API 调用时，每个调用必须核两处——返回结构（取哪个 key）和参数契约键（传哪个字段名），并把出处行号写进注释。最容易漂的就是这两处，不是 URL 本身。

**Why**：凭记忆写 API 用法会出三类错：① 返回 key 猜错直接 KeyError（如返回 `{"workflow_id":...}` 却取 `['id']`）；② 参数键名猜错被静默忽略（如传 `topic` 实际要 `template_params.input_text`，不报错但功能失效）；③ 调试脚本打印凭据前 32 字符进了构建日志。

**How to apply**：手册里每个 API 调用先 grep 消费代码确认返回结构和参数键。不确定的键名宁可留空让人问，也别写"看起来对"的键。会打印值的调试脚本默认按"会不会进 git/日志/截图"判断。
