---
name: kebab-case-slug
description: 一句话摘要（检索靠它）
type: tool | workflow | pitfall
source: 来源项目或事件（如 "GitHub Actions CI 事故"）
date: YYYY-MM-DD
verified: YYYY-MM-DD
---

**经验**：直接说怎么做。

**Why**：（可选）不这样做会怎样。

**How to apply**：（可选）什么场景、如何应用。

> 作用域（P1-2）：若结论**只对某网关 / 模型 / 平台**成立（含具体数值上限、错误码、返回结构、
> 字段名），`description` 必须写 `【作用域=<网关/模型/平台>】`，让读者只读 description 就能看出边界；
> **通用规律不要加**标签。校验器 `hooks/kb_validate.py` 会在写入时拦下「引用了具体版本/模型却未点名作用域」。
