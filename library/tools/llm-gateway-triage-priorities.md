---
name: llm-gateway-triage-priorities
description: LLM 网关缓存命中率/计费异常排障优先级：429 切渠道、system 前缀增长、cache_creation 恒 0 是协议、A/B 要挑稳定期
type: tool
source: mh-agent-open + apishow（2026-09 实测链）
date: 2026-09-14
---

**经验**（排查按此优先级）：

1. **缓存命中率忽高忽低**（0% 与 97% 交替）→ 先查站点是否在 429 切渠道：各渠道 KV 缓存独立，切换即全量 miss。**同一不变前缀也 miss = 站点噪声**，不是我方请求形态问题。
2. **system 前缀每轮增长**（如 CLI 每轮追加 task 提醒/notification 动态段）→ 对"完整单元匹配"的缓存（DeepSeek）整个前缀作废；解法 `CLAUDE_CODE_DISABLE_ATTACHMENTS=1` + reminder off；诊断开 prefix-hash trace，sys 哈希变=必失效。
3. **`cache_creation_input_tokens` 恒 0 不是 bug**：OpenAI 协议无"缓存写入"字段，映射填 0 是正确的，先确认 api_type 再决定查不查。
4. **账单/模型名异常** → 查上游端点的模型别名自动映射，钉死 `ANTHROPIC_DEFAULT_*` 类环境变量别名。
5. **A/B 实验**必须在无 429 的稳定期做，单轮 40 样本会从"+12pp"反转到"-3pp"；测试流量必须 `stream:true` + `include_usage` 对齐真实路径。
6. 流式 chunk 不重写 model 字段可致客户端校验失败；非流式经网关 >60s 必 504、流式无限。
7. **优化上下文时：改历史内容 = 毁掉前缀缓存，成本反而上升**（2026-09-18 AstrBot/DeepSeek 实测）。想把"历史里的图片/大块内容"剥离、压缩、换成摘要来省 token 时，先想清楚：只要改写后的历史**与上一轮不同**，前缀缓存整段失效，每轮都按全价 miss 计费。实测反直觉点：**base64 文本本身不计 token**——同一张 1024×1024 图，base64 从 1MB 涨到 4MB，prompt_tokens 恒为 686（其中约 653 是**视觉 token**，只与图像分辨率有关，与 base64 长度无关）。⇒ ①"图片换成文字描述"是唯一真省 token 的路，但只要模型还需要看原图就不划算；②想省体积而不动语义，用平台侧 file_id/URL 引用（请求体小、历史字节不变、缓存稳定）；③**结论：宁可保持历史一字不动 + 请求体引用化，也不要为了省 token 去改写历史**。
8. **判断"缓存友好"的通用判据**：问自己"这一轮请求的前缀，与上一轮逐字节相同吗"。任何在历史中插入/删除/改写内容的优化（图片剥离、消息摘要、动态提醒、工具结果裁剪）都会破坏它；稳定前缀 + 只追加 = 缓存命中。
