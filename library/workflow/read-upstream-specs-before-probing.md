---
name: read-upstream-specs-before-probing
description: 需要的上游参数规格（上下文/输出上限/推理档位/能力标记）先读上游源码、release notes、PR 与目录元数据端点，别一上来就发探针——盲探是额外消耗；实测只作验收，且要有判别力
type: workflow
source: APIShow LobsterAI 纳号（2026-10-15 用户纠正）：上下文/输出上限的多轮盲探被指"平添不必要的消耗"
date: 2026-10-15
verified: 2026-10-15
topic: methodology
---

**经验**：取上游参数规格按固定顺序——1) 读上游项目：`gh release view <tag>` / `gh api repos/.../pulls/<n>`
（变更全文最省时间）→ 源码 grep；2) 上游 API 的元数据端点（一次拉全胜过逐项探，如模型目录自带
contextWindow / thinkingConfig / maxTokens）；3) **只有前两步没有的缺口才实测**，且探针必须有判别力
（例：判推理档位是否真生效，用 `reasoning_effort=off` vs `high` 对比 `reasoning_content` 长度，
而不是比响应体积）。

**Why**：盲探既花额度又慢。本次为 lobsterai 打多轮探针取输出上限，而上游 models 目录一次就
拿全了上下文与档位——用户原话「不需要实测上下文和最大输出，只需要看原项目是怎么搞的，
不然都是在平添不必要的消耗」。探针无判别力时还会得出假结论（同批测试因 max_tokens 过小
把"截断"误读成"不解析"）。

**How to apply**：
- 实测的定位是**验收**（证明已落地行为），不是**发现规格**；探针一次批量并行发完，同一目标不反复试错。
- 上游限流/不可达时，别拿"未实测"当"未验证"：改用**代码级证据链**——AST 抽取纯函数做形状断言、
  静态通路核对、二进制符号检查、服务端静态资源取回比对；并如实声明"行为证据未取到"。

相关：[[research-upstream-before-fixing]]、[[upstream-merge-crlf-noise-and-anchor-patches]]。
