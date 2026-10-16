---
name: collected-data-must-be-persisted-before-analysis
description: 昂贵采集出来的原始件必须"先落盘再分析"；先统计后 dump 会把数据困在内存，环境回收/超时即全丢（2026-10-13 云环境论文实弹：1.26M tokens 采集随进程 kill 归零）
type: pitfall
source: mh-agent-open AI 论文全流程实弹（2026-10-13~14，CNB 云环境）
date: 2026-10-14
verified: 2026-10-14
topic: cnb, methodology
---

**经验**：跑"先采集 → 后统计"的批量实验时，**采集一结束就立刻把 raw（原始轨迹/响应）落盘并 push**，
然后才允许进入分析/统计阶段。绝不能写成 `collect(); stats(); dump()`——
统计若卡顿/超时/被 kill，**数据就困在内存里**，随进程终止全部消失。

**Why**：2026-10-13 云环境论文实弹的 E3d 轮：60 题 × K=4 全量采集**已完成**（701 调用 / **1,258,680 tokens** / 10296s ≈ 2.9h），
但脚本把 `json.dump(e3d_raw.json)` 写在 bootstrap **之后**；bootstrap 因"每次重采样都重扫全长轨迹的 7 个正则"
估时需 **≈7h**（单线程 CPU 100%），撞上环境回收线；执行者 kill 进程 ⇒ **1.26M tokens 的采集数据一次性归零**，
论文第四档被迫重跑。同一晚更早还有一次：`_tmp/e3b/*.py` 被引擎在回填链步骤间**清空 `_tmp`** 而丢失（脚本未归档进仓）。

**How to apply**（四条，逐条都是这次用钱买来的）：
1. **顺序铁律**：`collect() → dump_raw() → push() → stats()`。统计再慢也不影响数据已在手。
2. **跑器归档进仓**（`docs/harness-evidence/<主题>/`），⛔ 不要留在工作区 `_tmp/`——
   本仓引擎会在步骤间清空它；工作区本身也不随漫游恢复（100MB 上限，实测论文工作区未恢复）。
3. **长任务分批 + 增量落盘**：按 batch（如 5 题）即时 dump 并 push，别末尾统一落盘；
   统计阶段同理：数字一到手先 push，再做回填/装饰性步骤（旧环境就死在"攒着一起交"）。
4. **统计复杂度要预计算**：与反事实交换无关的特征（quality/terminal/budget）只算一次；
   bootstrap 只重采样"题"并累加预计算值 ⇒ O(items) 而非 O(items × 轨迹长度)。这是把 7h 压到秒级的关键。

**相关判据**：判"进程还在干活"不能只看 CPU（I/O 绑定型 CPU≈0 属正常，看 socket 数 + 进度行）；
判"数据会不会丢"只看一件事——**raw 是否已经落盘并 push**。
相关：[[log-text-is-not-spec-read-emitting-code]]、[[cnb-workspace-agent-direct-channel]]
