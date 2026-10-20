---
name: no-assertion-without-measurement
description: 对工具/平台/模型的能力与行为，零实测就零断言——别臆测、别想当然、别凭记忆下结论；口头陈述是线索不是定论，先看本机既有先例再搜官方文档，用户纠正后做最小修正
type: pitfall
source: 用户 2026-10-04 两次批评（"你可以上网搜索啊"、"你怎么越做越错，你好像很容易想多，然后还容易想错"）；2026-10-05 起多次复现（模型视觉能力、CNB 步骤超时、workbuddy 机制）
date: 2026-10-16
verified: 2026-10-16
topic: verification
---

**经验**：涉及**工具/平台/模型的能力与行为**时，**零实测零断言**。典型臆测（全部被用户否证过）：

| 臆测 | 实测真相 |
|---|---|
| 「workbuddy 没有 hooks 系统，agent 开工没人提醒扫库」 | 它自带机制 |
| 「workbuddy 不读 ~/.agents」 | 本机 35 个技能全是指向它的链接，官方支持 symlink auto-discover |
| 「模型不支持视觉时就不能调视觉 Agent」 | 恰恰相反——设成"不支持"才**可以**调 |
| 「步骤超时是 48 小时」 | 整个工作流任务才是 48h，单步是另一回事 |

**Why**：凭推测下断言会连带做错决策（改部署、写进 KB、回撤返工），且用户要花额外轮次纠正——2026-10-04 一天内因此被连批两次。

**How to apply**：
1. **顺序固定**：① 看本机既有先例（同目录其它条目什么形态、既有配置怎么写的）→ ② 搜官方文档/源码 → ③ 动手后让工具**实际跑一次**再收工。
2. **用户的口头陈述是线索不是定论**——它值得优先核实，但不能直接当结论写进 KB 或据此改部署。
3. **分档表述**：说"我实测到 X"，不说"它一定是 X"；没实测的场合只能写"可能"，并明说未验证。
4. **被纠正后最小修正**：只改错的那几行，不借机扩大改动面（用户明确要求过）。

**检索症状词**：臆测、想当然、凭记忆、我以为、应该会、肯定是、没测就说。

关联 [[stated-provenance-needs-evidence-and-conditions]]、[[summary-scope-qualifiers-must-be-explicit]]、[[cross-agent-skill-dir-semantics]]、[[defect-localization-methodology]]。 [[config-load-failure-check-file-refs-and-schema]]、[[injected-ui-feature-failure-check-credential-plumbing-first]]、[[run-level-failure-text-is-not-sub-operation-failure]]、[[multi-line-log-attribution-use-baseurl-not-model]]、[[model-capability-verdict-needs-official-docs-not-probes]]。
