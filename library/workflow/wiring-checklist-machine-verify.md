---
name: wiring-checklist-machine-verify
description: 接线清单机器校验 + 死字段审计；新增一家要改 8-10 处，漏一处全静默；「写了不读的字段」可能就是主路径
type: workflow
source: APIShow docs/分析/20261026_其他源与通用机制_参考要点.md（2026-10-26 精读参考工程 6 份 provider 笔记）
date: 2026-11-10
verified: 2026-11-10
topic: methodology
---

**经验**：多源接线的「改 8-10 处」清单要**机器校验**，别靠人记。
同时定期做**死字段审计**：配置里写了但代码从不读的字段，往往就是主路径上被漏接的那一个。

**Why**：2026-10-26 参考工程审计：新增一家 provider 要同步改模型清单/映射/分组/台账/文档等
8-10 处，任何一处漏改都是**静默**的（不报错，只是功能不生效）；
「写了不读的字段」在配置里看起来正常，实际是主路径断链。

**How to apply**：把接线清单做成脚本/测试（缺一项就 fail）；
每季度对配置键做一次「写入方 vs 读取方」对照，删除或接上无人读的键。

相关：[[ledger-audit-must-be-bidirectional]]、[[model-rename-without-rule-sync-loses-capabilities]]
