---
name: log-full-read-not-just-errors
description: 看日志要全量通读最近日志而非只筛 error——显示假象与产品缺陷都藏在非 error 行
type: workflow
source: mh-agent-open（2026-09-06 用户教导，两例实战佐证）
date: 2026-09-14
verified: 2026-09-06
topic: methodology
---

**经验**：诊断"看日志"类任务时拉最近约 300 条**全量**通读，按类型归类构成（心跳/工具/结果/模型输出/错误），找非 error 行的异常模式。按 error 过滤会漏两类问题：①显示假象（如工具摘要把权限参数拼进命令显示，看似命令被污染）②产品层缺陷（真实产物被海量噪声条目淹没）。心跳行单独跳过但保留计数（是活跃度证据）。
