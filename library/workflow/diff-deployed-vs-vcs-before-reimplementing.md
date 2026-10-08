---
name: diff-deployed-vs-vcs-before-reimplementing
description: 接手半途任务要「补实现」时，先 diff 部署面（安装目录/运行环境）与版本面（git 仓库）——上一步可能把新实现写在部署处没回流；找到现成实现以它为基底改，别重写
type: workflow
source: agent-kb kb_validate --check-triggers 本机版 18KB 未回流仓库（2026-10-04）
date: 2026-10-04
verified: 2026-10-04
topic: methodology, git
---

**经验**：接手「上一会话没做完」的任务、发现某个声明的机制缺失时，**先找实现副本再动手写**：

1. **diff 部署面与版本面**：`diff 仓库文件 部署目录同名文件` + 比对双方 mtime/大小。半途工作最常见的形态是「新实现已写进部署目录（本机 ~/.xxx/、容器、安装产物），仓库还是旧版」——只看仓库会误判「还没人做」。
2. **以现成实现为基底**：找到副本后做**回流**（部署版 → 仓库 + 按需小改），不要按自己的设计重写——现成版往往已被实跑验证过（本次本机版已实跑 [PASS] 且含踩坑修正：nomatch/missing 混淆的误判教训都在注释里）。
3. **回流时只做两类改动**：适配仓库环境的必要差异 + 可测性/健壮性小改（参数注入、类型归一），其余逐字节保留。

**Why**：重写会丢掉上一轮的踩坑修正（都在代码注释里，不在任何文档里），且引入「实现分叉」——恰是任务本来要消灭的东西。

**How to apply**：接手遗留工作的第一组命令就是 `ls -la` 两边 + `diff` 同名文件 + `git status`（未提交改动也是线索）；确认「实现只在部署面」后再动手。判断依据：文件大小/mtime 差异显著、仓库版缺部署版有的功能段。相关：[[hardlink-unify-shared-scripts-across-tools]]（副本治理）、[[report-what-you-did-not-what-you-meant-to-do]]。
