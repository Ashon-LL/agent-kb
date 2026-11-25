---
name: cnb-use-repo-token-before-oauth
description: 调 CNB 写接口先用仓库令牌（CNB_TOKEN 覆盖 OAuth）；⭐库级（域级）令牌不过期，会过期的是用户级 OAuth（~/.cnb/token，~7 天，CLI 默认读它）；Git Bash 下 --asset-path 必须 MSYS_NO_PATHCONV=1，否则 /apigogo/… 被转成 C:/Program Files/Git/… 写坏资产元数据
type: pitfall
source: zcodepro（2026-10-24 发 v20 单包）
date: 2026-10-24
verified: 2026-11-04
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

## 追加：MSYS 路径转换写坏资产元数据（2026-11-04 实测）

**现象**：Git Bash 里跑 `cnb releases post-release-asset-upload-confirmation --asset-path /apigogo/…`，
服务端资产的 `path/url/browser_download_url` 变成 `C:/Program Files/Git/apigogo/…`、
`https://cnb.coolC:/Program Files/Git/…`——下载按钮/API 链接全坏，但 hash/size 正常。

**Why**：MSYS 把以 `/` 开头的参数当 POSIX 路径自动转换为 Windows 路径；CLI 原样把转换后的值写进服务端。
同一次 list-releases 里正常条目与污染条目并存，可排除显示层问题。

**How to apply**：
1. Git Bash 下所有带 `--asset-path`（及任何 `/开头` 参数）的 cnb 命令前缀 `MSYS_NO_PATHCONV=1`，或改在 cmd/PowerShell 执行；
2. 取仓库令牌也可用 `printf 'protocol=https
host=cnb.cool
path=<owner>/<repo>.git

' | git credential fill` 的 password（即凭据管理器那条），`CNB_TOKEN=<令牌>` 注入，不回显不落盘；
3. 已污染的修复：本地原文件走 upload-url（--overwrite）→ PUT → confirmation（正确 path）同名覆盖，hash 不变；
4. 验证修复用 list-releases -v 看 path 字段 + 对规范 URL 做 HEAD（不下载正文）。

**检索症状词**：asset-path、C:/Program Files/Git、browser_download_url 坏、MSYS_NO_PATHCONV、10023、repo-release:rw。

关联 [[windows-unquoted-path-redirect-accidents]]

## 追加：令牌类型与过期（2026-11-08 用户澄清）

- **库级（域级）令牌不过期**；用户一直要求/使用的就是库级令牌（git 推送与仓库 API 共用，取用方式见上）。
- **会过期的是用户级 OAuth token**（`~/.cnb/token`，`cnb login` 设备流的产物，约 7 天）：cnb CLI **默认读它** ⇒ 于是 CLI 会报「Token 已过期，刷新失败」。
- ⛔ 别把两者混为一谈：CLI 报 token 过期时，**改用库级令牌**（`CNB_TOKEN` 注入，见上）即可，**不要**让用户重新 `cnb login`。
- ⛔ 但**不是所有 CNB 接口都收库级令牌**：云开发的 workspace 接口（`cnb workspace *`）用库级令牌会 **403**（2026-11-08 实测），它只认**用户级 OAuth** ⇒ 那种情况只能让用户重新 `cnb login`。
- 注意另一处同名的 `CNB_TOKEN`（云开发工作区 serve 进程注入的那份）过期是**另一回事**，见 [[cnb-workspace-agent-direct-channel]]；两者不是同一个令牌。

## 追加：为什么还是会看到用户级（2026-11-08）

- **cnb CLI 默认读 `~/.cnb/token`（用户级 OAuth）** ⇒ 不调 `CNB_TOKEN` 时走的就是用户级。
- **库级令牌不是所有接口都能用**：如 workspace（`account-engage:r`）库级令牌会报
  `errcode 10023 Missing required scopes: account-engage:r`；而 registry 写/删
  （`registry-package:rw` / `registry-package-delete`）反而**只有库级令牌有权**。
- ⇒ 正确姿势 = **优先库级、权限不足自动回落用户级**。已做成 wrapper：
  `C:\Users\MECHREVO\bin\cnb-repo`（先 `git credential fill` 取库级注入 `CNB_TOKEN`，
  命中 `Missing required scopes/10023/403` 则回落 CLI 默认）。已加入 `~/.bashrc` 的 PATH。
