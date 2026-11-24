---
name: platform-native-keepalive-over-local-cron
description: 长期保活优先用平台侧 cron（CNB .cnb.yml main crontab），本机/单机 systemd timer 只做兜底；启用后必须 sync crontab 并用 build log 验证
type: workflow
source: APIShow CNB 官方源（2026-11-23）
date: 2026-11-23
verified: 2026-11-23
topic: cnb, delivery
---

**经验**：依赖云 workspace 的服务，保活要放在平台自己的调度里，而不是只放在本机或单台服务器的 systemd timer。CNB 的做法是 `.cnb.yml` 的 `main:` 分支下 `"crontab: */5 * * * *"`：流水线用每次构建自动签发的短时 `CNB_TOKEN` 调 `GET /workspace/list?slug=$CNB_REPO_SLUG`，没有 running 就 `POST /{repo}/-/workspace/start`；不存长期令牌。改完先 `POST /{repo}/-/build/crontab/sync/{branch}` 同步平台 crontab，再等下一次 cron 或看 `/build/logs` 的 `event`/`sha`，最后读 `/build/runner/download/log/{pipelineId}` 确认脚本真的执行到 `running sn=...`。

**Why**：本机会休眠/断网/关机，单台服务器也是单点；只靠它们会在最需要保活时失效。平台 cron 与业务机器解耦，且短时 token 不需要长期密钥。注意平台可能在仓库长期无提交时暂停 cron（dormancy），所以保留外部/服务器 watchdog 作为兜底，但不要把它当唯一。

**How to apply**：新增长期保活先在平台侧找原生 cron/定时任务；有现成 `.cnb.yml` 块就启用并 sync，不要先写本机 timer。验证要看构建日志的事件名、commit sha、`list http=200` 与 `running sn=...`，不是只看 build 状态 success。关联 [[token-and-secrets-hygiene]]、[[cnb-use-repo-token-before-oauth]]。
