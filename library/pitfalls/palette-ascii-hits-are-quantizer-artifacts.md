---
name: palette-ascii-hits-are-quantizer-artifacts
description: 调色板里零散出现的 FLAG/CTF/key 多为量化色带产物；用干净重编码对照实验判定，别当线索
type: pitfall
topic: security
source: ctf-2026qwb-preheat
date: 2026-10-30
verified: 2026-10-30
---

**经验**：GIF 每帧本地调色板的字节可打印率高（0.6+）、偶尔出现 `FLAG`/`CTF`/`key`，**默认判定为量化色带伪影**，不是隐写。判定方法：把同一批帧用自己的量化器（如 PIL 中位切分 256 色）重新编码，看干净调色板是否也刷出同类命中。

**Why**：本题 818 帧调色板可打印占比 0.621，`FLAG` 出现 1 次（帧 575 偏移 229），看着像线索。但干净重编码照着跑出 8,499 个 ≥6 位字母数字串、1 次 `CTF`、可打印 0.640——和原图（8,212 串、6 次命中、0.621）同量级。原因是量化器输出的调色板是一条平滑色带（矩阵图呈竖条渐变），相邻色阶的 RGB 字节连读天然落进 ASCII 区间。`46 4c 41 47` 就是 G/B/R 通道交界处的相邻取值。

**How to apply**：
1. 先跑对照实验，别只看命中次数。
2. 看命中位置的上下文：色带里的命中前 const 后必是连续数值递进；真文本两侧是随机字节。
3. 检查是否有 `flag{`/`ctf{` 完整包装（含 `{`）；色带产物几乎不会凑出 `{`。
4. 15 种变换（原始/BGR/分通道/排序/差分/秩编码）× 全帧，若 `flag{` 类全 0 而 `FLAG` 零星，就是噪声。
5. 若确实要多看一层，检查"未使用调色板项"——但注意必须先拿到**真实索引掩码**：PIL 对动画 GIF 的 `seek(i).tobytes()` 返回 RGB（W×H×3），不是索引，据此算的未使用项统计是错的。

关联 [[gif-stego-scan-frames-before-format]]、[[ablation-must-self-verify-change-applied]]。
