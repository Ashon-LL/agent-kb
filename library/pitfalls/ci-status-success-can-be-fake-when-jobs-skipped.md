---
name: ci-status-success-can-be-fake-when-jobs-skipped
description: CNB CI status=success 可能两个 job 全 skipped（ifModify 按需触发）——判绿必须看 stages
type: pitfall
topic: ci
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
---

**经验**：CNB Pipeline 加了 `ifModify` 按需触发后，空提交或只改文档的提交不会触发任何 job，但顶层 `status` 仍报 `success`。判 CI 绿必须 `cnb build get-build-status` 看 `stages` 里每个 job 是 `success` 还是 `skipped`，不能只看顶层。不要用空提交/改文档去触发 CI 验证。

**Why**：顶层 success 是 Pipeline 级别的，Prepare/End 空跑（4-5ms）就算成功；真正的 job 全 skip 了也照样 success。拿顶层 success 当绿证会得出"CI 修好了"的假结论。

**How to apply**：判绿时 grep stages 找具体 job 名（如 `backend-unit-tests`），确认 status 是 success 而非 skipped。触发 CI 验证必须动实质文件（backend/tests/scripts 等命中 ifModify 路径的）。
