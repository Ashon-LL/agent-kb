---
name: leak-probe-false-positive-three-guards
description: 安全探针报 LEAK 前必须看原文+设对照组+复现一次——关键词命中拒绝话术不是泄露
type: pitfall
topic: security
source: apishow
date: 2026-10-03
verified: 2026-10-03
---

**经验**：报任何 LEAK 之前三步：① 先打印 content/channel 原文再判，别只看正则结果；② 设对照组（system 里不放 canary 再跑一次）；③ 复现一次，单次命中不作为证据。判定式要区分语义而非子串。

**Why**：探针 24 项报 2 处 LEAK，复核后全是假阳性。一是模型拒绝调用时提到工具名被正则捞到（"模型讨论工具"≠"工具内容泄露"）；二是 canary 单次命中是采样波动。假阴性风险来自枚举面太窄，假阳性风险来自判定式太糙，两类都要靠原文+对照组落地。

**How to apply**：判定式区分"调用参数出现在本该为空的 content 通道"（真泄露）与"content 非空说明模型在走自然语言路线"（上游没走结构化通道，不是参数泄露）。不可复现的异常要明说"不可复现"，不能写成 LEAK。
