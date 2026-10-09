---
name: subagent-absence-and-security-claims-need-selfcheck
description: 子代理/子探针汇报里"已关闭""已不存在""最新版是X"三类断言必须主-agent 亲自抽查一次命令输出再写进方案；2026-10-08 体检中 UAC 路径读错、NoAutoUpdate 不存在、注册表路径带引号导致 Test-Path 假孤儿，三处都是转述即出错
type: workflow
source: 2026-10-08 default 会话全机体检（三路子代理 + 主-agent 抽查）
date: 2026-10-08
verified: 2026-10-08
topic: methodology, agent-orchestration
---

派子代理做全机盘点省时间，但它们的结果是**转述**，以下三类断言在写进方案/报告前必须自己跑一条命令抽查：

1. **安全策略类**（UAC 关闭、Defender 关闭、更新被屏蔽）——读错注册表位置就会反向，见 [[windows-uac-and-windows-update-policy-real-paths]]。
2. **"不存在/已卸载"类**——`Test-Path` 对带引号的 `InstallLocation`（如 `"C:\Program Files\Tencent\Weixin"`，注册表里就带引号）会返回 False，凭它判"孤儿注册表记录"是**假孤儿**；实测三个"文件早没了"的应用其实都在（用户当场纠正"这三项还存在"）。判孤儿要交叉验证：目录内容枚举 + 卸载器文件是否存在 + 进程路径，不能只看一个 Test-Path。
3. **"最新版/可升级到 X"类**——winget 报的是源里有的版本，"源里没有驱动项"≠"没有新版"；驱动只能标"需厂商渠道核对"，不许据 winget absence 编版本号。

**Why**：三条误报方向不同但代价相同——方案里写错根因，用户照着做会改错东西（删不存在的策略值、清理还在用的软件）。子代理的输出是**线索**，不是证据。

**How to apply**：
- 盘点类子代理的 brief 里直接写死："任何'已关闭/不存在/最新版'的结论必须附**它自己跑的命令与原始输出片段**"，便于主-agent 复核。
- 主-agent 合并前，对**要写进用户可见结论**的每条高影响断言抽查一次；抽查到错的要在报告里明写"子代理误报、已纠正"，别悄悄改掉。
- 子代理跑太久（>1h）且被慢步骤拖住时：停掉它，自己跑精简版顶上，别让整份交付卡在一个子代理上（2026-10-08 第三个代理满盘扫描 85 分钟未完成，精简扫描 1 分钟覆盖了核心）。

关联 [[windows-uac-and-windows-update-policy-real-paths]]、[[powershell-substring-match-bulk-delete-hazard]]、[[bulk-delete-requires-reverse-dep-check]]。