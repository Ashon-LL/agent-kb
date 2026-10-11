---
name: zcode-workflow-cwd-drift-and-amend-same-name
description: CreateWorkflow 提交时主会话 cwd 漂移会把 run 的 workspace 根带歪；AmendWorkflow 给同名 agent 追加任务必须复用引用而非再调 agent()
type: pitfall
source: SRC挖洞项目（dwfrun 三轮实战，2026-10-07）
date: 2026-10-07
verified: 2026-10-07
topic: zcode
---

**经验**：CreateWorkflow/AmendWorkflow 的两条运行时陷阱：

1. **提交前主会话的 cwd 就是 run 的 workspace 根**：提交 CreateWorkflow 前若 Bash 曾 `cd` 进子目录（如 tmp-scan），draft 脚本会落 `<子目录>/.zcode/workflow-drafts/`，且 `artifact.file` 等 workspace 相对解析全部基于该根——脚本里写 `tmp-scan/wf2/x.md` 会被解析成 `<子目录>/tmp-scan/wf2/x.md`，报 "does not exist or is not a regular file"，即使文件真实在项目根下。防御三件套：① 提交前 `pwd` 回项目根；② 脚本内发布 artifact 只用脚本常量路径，不信任 agent 返回的路径字符串；③ 发布前 `files.read(path)` 校验真实存在，失败走抢救分支而不是让发布异常炸掉整个 run。

2. **给已存在的 named agent 追加任务必须复用同一 Agent 引用**：amend 后第二轮若再写 `agent("x", persona).ask(...)` 是**新建同名身份**，run 直接 errored（"Subagent name X is used twice"）。要复用第一轮上下文，创建时即赋引用：`const v = agent("x", persona); v.ask(A); ...后续 v.ask(B);`——同一身份多次 ask 串行合法，且 amend 缓存按「名+ask 文本」命中，第一轮结果零成本导入。

**Why**：实测一轮三跑：第一次因 cwd 漂移在简报发布阶段 errored（文件其实好好在盘上）；第二次因重名在验证执行前 errored，各浪费一个完整 amend 周期；第三次修复后才闭环。

**How to apply**：写 workflow 脚本时把「发布路径常量化 + files.read 预检 + catch 内不裸抛」作为模板默认；任何预期后续轮次复用的 fan-out agent，创建时一律赋引用变量。

关联 [[kb-accident-three-layer-lessons]]、[[zcode-provider-config-group-enum-standard-personal]]、[[zcode-platform-verified-facts]]。
