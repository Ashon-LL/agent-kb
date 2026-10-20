---
name: success-status-is-not-no-abort-evidence
description: `status=success` 只说明收割时有东西可汇报，不说明过程没被强杀；同一个 exit 137 有两种结局（临死前推完=success、没推完=error）；判据必须读到原始日志里的 `exit code: 137` 与时长；用反面案例证伪假设时要挖到机制层；两次独立事件被杀时刻相差几秒是「硬边界」的强证据
type: pitfall
source: MH-Agent-Open cnb-sdo / cnb-eke 全量构建日志逐行对照（用户 20260918 指出 success 可能是巧合）
date: 2026-09-18
verified: 2026-09-18
topic: verification, cnb
---

**教训**：平台返回的 `success` 不是「过程没被中止」的证据。它只表示**收割时容器里还有可汇报的产物**。

## 实证

两单都跑到 2h 边界被 SIGKILL，结局不同：

| 单 | 实跑 | 结束状态 | 最后一分钟 |
|---|---|---|---|
| `cnb-sdo` | 121.67 min | **success** | `[02:01:03] exit 137` → 容器销毁；临死前产物已推送完 |
| `cnb-eke` | 121.12 min | error | `[02:01:05] exit 137` → 容器销毁；产物没推完 |

**同一个 137、相差 2 秒**，一单绿一单红。绿的那单不是「跑完了」，只是「死前把成果发出去了」。

## 判据

- 看原始日志的 `exit code: 137`（128+9=SIGKILL）、该命令耗时、以及被杀后是否
  `No such container`（容器已销毁 ⇒ 级联中止）。
- ⛔ 不要只看 `status` / 最终错误文案 / 「没有 error 关键字」。
- ⛔ 用「success 反例」证伪某个上限时，必须读它**最后一分钟**的日志：
  只看「status=success + 121min」就宣布证伪，是把巧合当反例。
- **时刻证据**：两次独立事件都落在 `02:01:0x` ⇒ 硬边界，不是随机波动。这种「巧合」是强证据。

**How to apply**：任何「超时/被杀/中断」争议，先拉全量构建记录做横向对照（`get-build-logs` 自带对照组），
逐条读失败前后的原始日志；状态码只作辅助。

关联 [[cnb-pipeline-2h-hard-cap]]、[[binary-error-text-needs-branch-evidence]]、
[[log-full-read-not-just-errors]]、[[no-assertion-without-measurement]]。
