---
name: project-hygiene-continuous
description: 项目卫生是常驻动作不是收尾补课——一次性文件验证通过当场删、决策与来源文档随手同步、目录有真实内容就删掉 .gitkeep、交付前跑 check（lint+格式化）、产物只落工程内、体积有数、不擅自 commit
type: workflow
source: 用户常驻要求「随时做好项目卫生」（2026-10-29，10年人间 EP01 项目落地）
date: 2026-10-29
verified: 2026-10-29
topic: preference
---

**经验**：用户明确要求「随时做好项目卫生」，即卫生贯穿每个阶段，而不是攒到收尾或交付前补。可执行清单（每条都有明确判据）：

1. **一次性文件当场删**：调试脚本、探针、抽帧图、一次性产物，验证通过后立刻删；只有长期复用的才留在 `script/` 一类工具目录。
2. **文档同步是交付的一部分**：决策写 `docs/decisions.md`（决策 + 复现命令），新增素材/依赖写 `docs/sources.md`（授权台账），阶段结论回写交接文档的决策日志。
3. **不留冗余占位**：目录里已有真实内容就删掉它的 `.gitkeep`；整体被 gitignore 的输出目录（如 `out/`）不需要占位文件。
4. **交付前跑 check**：给出 `lint`（eslint + tsc）与 `format`（prettier）脚本，再补一个 `check` 把两者串起来；有报错先修再交。
5. **不写工程外**：产物只落工程内；需要在用户目录或别处落盘先征得同意。工具产物（venv、插件状态目录）写进 `.gitignore`。
6. **体积有数**：`node_modules` / venv / 输出目录的体积心里有数，大文件不进仓；渲染产物只留最新一版。
7. **不擅自提交**：commit / push 等用户发话；改动留工作区。

**Why**：卫生欠账是复利式的——一次性文件混进仓库后没人敢删（分不清是不是还在用）、文档不同步会让下一轮会话重复决策、`.gitkeep` 与真实文件并存会让人误判目录状态、check 脚本缺位会让格式/lint 债越滚越多。user 的诉求本质是「任何时刻看仓库都应该是干净且自洽的」。

**How to apply**：把这条写进项目的 `AGENTS.md`（工程级规则），每次阶段收尾与交付前按 1–7 过一遍；新建工程时就把 `format` / `check` 脚本和 `.gitignore` 一起建好，别等需要时再补。相关：[[cross-agent-skill-dir-semantics]]。

关联 [[cross-agent-skill-dir-semantics]]。
