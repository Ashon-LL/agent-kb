---
name: negative-prompt-is-also-moderated
description: negative_prompt 不是审核避风港——MiniMax H3 会把负面提示词当输入文本扫描；apishow-video 任务因负面词含未成年/比基尼/露点等触发 1026，去掉 negative_prompt、正向不变后成功
type: pitfall
source: 2026-11-07 APIShow MiniMax H3 四季蒙太奇 12 秒视频
date: 2026-11-07
verified: 2026-11-07
topic: llm, mcp
---

**经验**：`negative_prompt` 只控制「画面不要出现什么」，**不等于审核豁免区**。上游内容审核通常把正向提示词和负面提示词一起当输入文本扫描；把敏感词从正面挪到负面，仍可能触发同类拒绝。真正要规避审核，必须把敏感语义从**所有**文本字段里删掉，而不是换字段。

**Why**：2026-11-07 同一版四季蒙太奇正向提示词（包含「成年东亚女性、连体泳衣、露背、贴身、健康曲线」等描述）提交后，任务 `vt_2df91268196f07db487c595e059902ef` 在约 6 秒后终态失败：

```json
{"status":"failed","error":"upstream video task failed: 1026: input new_sensitive, input text sensitive","credit_actual":0,"files":[]}
```

失败版本的 `negative_prompt` 包含「未成年、儿童、校服、比基尼、透明泳衣、露点、裸体、性行为、生殖器、身体特写、低俗」等词。按用户要求**正向提示词完全不变、只删除 negative_prompt** 重建草稿后，任务 `vt_cd48e71deb6f32f3d8e28b4f75b0b468` 成功完成，`credit_actual=173.14`，产出 12.25 秒、1344×768 的 MP4。两次唯一的实质差异就是 negative_prompt 的存在；没有逐词隔离，因此不能断言哪一个词是唯一触发点，但可以确认：**负面字段里的敏感词没有躲过审核**。

**How to apply**：
1. 遇到 `1026 / input text sensitive`，先列出**正向 + 负向 + 参考素材**所有输入，而不是只改正向。
2. 不要用 negative_prompt 写「未成年、儿童、性行为、裸体、露点、比基尼、透明」等敏感词来“排除”；这些词本身会参与审核。改为正向写安全、具体的服装与镜头约束，或直接不传 negative_prompt。
3. 负面提示词只保留低风险画质/连续性项：模糊、低清晰度、过曝、欠曝、水印、字幕、logo、换脸、肢体变形、多余手指、镜头抖动等。
4. 要做对照，保持正向与其他参数不变，只删 negative_prompt；若成功，即证明至少有一个负面词参与了拒绝。不要把单次对照写成“所有模型都如此”的通用规律。
5. 高额度/涉真人素材的任务失败时先查 `credit_actual`；本次 1026 失败为 0，未扣费。

> ⏰ 时效状态（2026-11-07 记录，**已实测一次对照**）：本机 `apishow-video` → MiniMax H3 端点上，含敏感词的 negative_prompt 触发 1026；删除 negative_prompt、正向不变后成功。具体触发词未逐词隔离。
> ⚠️ 用前必须实测：对失败 task 调 `apishow_watch_video(task_id)` 读取 error；再用同正向、无 negative_prompt 的免费草稿做对照，确认是否仍报 1026。

关联 [[video-terminal-failure-needs-upstream-error-before-retry]]、[[mcp-instructions-may-name-undeclared-tool-fields]]、[[no-assertion-without-measurement]]。
