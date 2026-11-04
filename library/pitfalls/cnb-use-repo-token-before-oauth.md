---
name: cnb-use-repo-token-before-oauth
description: 调 CNB 写接口（release/附件等）先用仓库令牌（Windows 凭据里的 git 凭据），别用 cnb login 的 OAuth token——后者常缺 repo-release:rw
type: pitfall
source: zcodepro（2026-10-24 发 v20 单包）
date: 2026-10-24
verified: 2026-10-24
topic: cnb, delivery
---

**现象**：`cnb releases post-release` 返回 `403 / errcode 10023 · Missing required scopes: repo-release:rw`，
但用户确认令牌权限里明明有 `repo-release:rw`。

**Why**：`cnb` CLI 默认读 `~/.cnb/token`（`cnb login` 的设备流 OAuth 产物，字段形如 `cnb_at_…/cnb_rt_…`），
它的 scope 来自那次授权，**与仓库里配的 repo token 不是同一个**；写接口按 OAuth token 校验就缺权限。
CLI 支持用环境变量 `CNB_TOKEN` 覆盖（源码里读 `process.env.CNB_TOKEN`）。

**How to apply**（顺序固定：先库凭据，后 OAuth）：
1. 取**仓库令牌**：Windows 凭据管理器里 `git:https://cnb.cool/<owner>/<repo>`（git 推送用的那条），
   PowerShell `CredRead` 读出 password 字段；
2. `$env:CNB_TOKEN = <该令牌>` 后调用 cnb（同进程内，别落盘、别打印）；
3. 仍失败再查 scope / 换 OAuth token。

**配套细节**（本次实测）：
- `post-release` 必须带 `--target-commitish <sha|branch>`，否则 `errcode 2000001 target_commitish is required`；
- 附件三步：`post-release-asset-upload-url` → `curl -X PUT --data-binary @file <upload_url>` →
  `post-release-asset-upload-confirmation --upload-token <verify_url 里那段> --asset-path <解码后的路径> --ttl 0`；
- 203MiB 的包上传约 1-2 分钟，建议后台跑（`run_in_background`），别在前台等；
- 读令牌的 ps1 **不要含中文**（中文路径在无 BOM 的 ps1 里会乱码）。

关联 [[windows-unquoted-path-redirect-accidents]]
