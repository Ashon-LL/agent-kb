---
name: model-capability-verdict-needs-official-docs-not-probes
description: 判定模型能力（视觉/多模态等）必须查官方文档/模型卡/issue，本地探针会给出假阳性——"模型答对了"不等于"模型看得见"；本次 GLM-5.3/5.2 被「数黑点」图骗过（官方口径=纯文本），Kimi K3 才真有多模态
type: pitfall
source: APIShow 2026-10-17（给中转组配 25 模型规格 / WorkBuddy 源接入三个高消耗模型）
date: 2026-10-17
verified: 2026-10-17
topic: llm
---

**经验**：给模型声明「图片/视频/思考档」这类能力时，**判据必须是官方口径**（官方模型概览、模型卡、
官方帮助中心、上游仓库 issue）。**本地探针只能做验收，不能做发现**——单张图/单次问答**会给出假阳性**：
「模型答对了」≠「模型看得见」。

**Why**（2026-10-17 实测，用户当场提示「先在 tavily 上搜搜」才纠正）：

- 探针现场：8×8 纯色图问颜色 + 96×96「数黑点」图问个数。`GLM-5.3`/`GLM-5.2` **两题都答对**
  （蓝/红 + 「3」）⇒ 我据此判「两者有视觉」，准备在站点与客户端声明 `supportsImage=true`。
- 检索后**全部推翻**：智谱官方模型概览里 `GLM-5.3` 无多模态描述（多模态的是 **GLM-5.3-Flash** /
  GLM-5V-Turbo）；`GLM-5.2` 的官方文档路径直接就是 `/models/text/glm-5.2`；
  上游仓库 issue（`zai-org/feedback`)里明写「**GLM-5.3（非视觉）**」。而 `Kimi K3` 官方帮助中心
  明确「原生多模态：图片 + 视频 + 文档」——与各家网关的既有声明一致。
- 假阳性的成因不止一种：模型可能**猜**（纯色/计数是低熵问题）、**网关可能注入图片描述**、
  也可能是**上游把图静默丢弃后模型顺着 context 编**。同一批探针里就有反例：
  `GLM-5.3` 对红色图回过「the image didn't load properly」——同模型同一格式，结论自相矛盾，
  这本身就是「探针不可作判据」的信号。
- ⇒ 代价：若不查官方，会把「纯文本模型」对客户声明成支持图片（客户端 UI 放开图片入口 →
  用户贴图得到看似正常实则瞎编的回答，比直接报错更难发现）。

**How to apply**：

1. 顺序固定：**官方文档/模型卡/帮助中心 → 上游仓库 issue & release notes → 才轮到探针**。
   能检索就检索（Tavily 等），别拿探针当第一手段。
2. **探针只用于验收**已按官方声明落地的配置（证明「我们这条链路真的转发了图片/真的生效了」），
   且设计成**有判别力**的实验（例如 `reasoning_effort=off` vs `high` 比 `reasoning_tokens`：
   本次 kimi-k3 得 12 vs 42 = 生效；glm-5.3 无差异 = 参数被接受但不改变行为，据此不宣称生效）。
3. **高熵问题才有一点判别力**；纯色/计数/「这是什么颜色」这类低熵问题**一律不算证据**。
4. **同一模型跨源声明要交叉验证**：多家网关对同一模型都声明 `supportsImage=false` 时，
   你的单次探针说「true」，先怀疑探针（本次正是如此）。
5. 冲突时的优先级：**官方口径 > 多家独立网关的既有声明 > 自己的单次探针**。
6. 记入文档时写明**证据来源与日期**（官方文档/issue 链接），别只写结论——下次换人复查才有抓手。

**相邻**：字段名/注释不是规格见 [[config-field-name-is-not-spec-read-consuming-code]]；
自建端点能力默认 false 见 [[custom-llm-endpoint-capabilities-default-false]]；
关联 [[custom-llm-endpoint-capabilities-default-false]]、[[config-field-name-is-not-spec-read-consuming-code]]。
