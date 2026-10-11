---
name: fail-open-except-swallows-caller-type-errors
description: fail-open 的宽 except 会把调用方的类型错误（AttributeError/TypeError）吞成「环境读不出」，把真故障伪装成静默跳过；入口先做类型归一（如 Path()），except 只接预期异常
type: pitfall
source: agent-kb kb_validate.py 的 _read_trigger_from_source 传 str 报 unreadable（2026-10-04）
date: 2026-10-04
verified: 2026-10-04
topic: python, diagnosis
---

**经验**：写「绝不抛异常、失败就降级」的 fail-open 代码时，`except Exception` 会把**调用方 bug**（传了 str 给期望 Path 的参数 → `AttributeError: 'NoneType'/'str' object has no attribute ...`）一起吞掉，归到「文件读不出/环境异常」分支——真故障变成静默跳过，且三态返回值（missing/unreadable/ok）里的 unreadable 会让排障方向整个跑偏。两个动作堵住它：

1. **入口类型归一**：函数第一行 `path = Path(path)`，把调用方的 str/Path 都变成合法输入；
2. **except 收窄到预期异常**：只接 `FileNotFoundError` / `OSError` / 编解码错误这类环境问题；`AttributeError/TypeError` 让它炸出来，那不是环境问题。

**Why**：fail-open 的本意是「环境坏了也别拖挂主流程」，但宽 except 分不清「环境坏了」和「代码写错了」——后者被吞后表现为 PASS/跳过，比崩溃更难查（本次：验证脚本传 str，被吞成 `unreadable`，一度误判为「文件读不出」）。

**How to apply**：任何带 `except Exception` + 静默降级路径的函数（hook、校验器、守护进程），写完自问两个问题：①这个 except 想吞的异常清单是什么，能收窄吗；②调用方传错类型会落到哪个分支。注入一个类型错误的实参跑一遍，确认它炸出来而不是被吞——炸出来才是对的。相关：[[hardlink-unify-shared-scripts-across-tools]]（同库「静默失败须可检测」家族）。

关联 [[toml-double-quote-nesting]]、[[ssh-heredoc-delimiter-must-be-quoted]]。