---
name: token-and-secrets-hygiene
description: 凭据卫生：库级令牌按 protocol+host+path 存 Windows 凭据管理器或 CNB helper；token 不内联命令行、不落仓库；凭据原文不进记忆/kb/日志
type: workflow
source: 合并自 credentials-never-in-memory-or-logs；apishow; ailika + mh-agent-open（用户多次强调）；2026-11-14 CNB leetcode-oz 仓库初始化实操补充；2026-11-23 凭据管理器优先/CNB CLI 卸载
date: 2026-09-14
verified: 2026-11-23
topic: security, git
---
**经验**：凭据卫生：库级令牌按 protocol+host+path 存 Windows 凭据管理器或 CNB helper；token 不内联命令行、不落仓库；凭据原文不进记忆/kb/日志

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## token-and-secrets-hygiene

**经验**：

1. **token 永远不上命令行/URL**（每次工具调用是新 shell，别图省事内联 `TOKEN=xxx`）：一次配置持久存储——工具自带凭据文件（如 `~/.cnb/token` JSON）或系统凭据管理器（`git credential approve` → GCM），之后裸命令直接可用。
2. **安装包/仓库/公开内容零敏感**：不含 .db、真实站点域名、密钥、源项目与逆向表述；Git 历史含敏感必须 `git filter-repo --replace-text` 重写 + force push，不能只删当前文件；发布前检查（安装包内容清单、`git log -S`、文档扫描）。
3. **记忆/文档里的上游域名与 key 前缀一律占位符**（`<上游站点>`、`<key前缀>`），换站只沉淀"协议 × 能力"结论；需复现时从 DB 取真值——注意管理 API 返回的是**掩码 key**，别把掩码导致的"未认证"误判成 key 失效。

关联 [[redaction-three-principles]]。

### 追加：库级令牌按 host+path 存入 Windows 凭据管理器（2026-11-14 CNB 实操）

**经验**：CNB 这类“一仓一令牌”的库级令牌，要按 `protocol + host + path` 三段存储和查询，不能只按 host 存。推荐流程：

```bash
# 在仓库根目录执行：让 credential helper 拿到仓库 path
git config credential.useHttpPath true
git config credential.helper manager

# 令牌从 stdin 进 GCM/Windows 凭据管理器，不回显、不落盘
printf 'protocol=https
host=cnb.cool
path=<owner>/<repo>.git
username=<git-username>
password=%s

' "$TOKEN"   | git credential approve

# 验证：带完整 path 取回；只检查 username 与 password 是否存在
printf 'protocol=https
host=cnb.cool
path=<owner>/<repo>.git
username=<git-username>

'   | git credential fill
```

- remote URL 只写 `https://cnb.cool/<owner>/<repo>.git`，绝不写成 `https://user:token@host/...`；
- 不把 token 写进 `.git/config`、`.env`、README、CI 日志或脚本；
- 仓库级条目通常显示为 `git:https://cnb.cool/<owner>/<repo>.git`；只按 host 查询可能拿到泛用凭据（见 [[git-credential-scope-and-rotation]]）；
- 用户习惯：CNB 统一优先用**库级令牌**；用户级 OAuth 会过期，只在库级权限不足的接口（如 workspace）才回落（见 [[cnb-use-repo-token-before-oauth]]）。

**Why**：按 host 存会让同一主机下不同仓库共享一条泛用凭据，既可能拿不到本仓库的库级权限，也会让轮换一个仓库的令牌时误伤其他仓库。按 path 存才能做到“一仓一令牌”。

**How to apply**：每个新仓库初始化后，先设 `credential.useHttpPath=true`，再用完整 path 执行 `git credential approve`；推送前用带 path 的 `git credential fill` 验证。凭据只进 Windows 凭据管理器，不进仓库。

### 追加：CNB 专用 helper 会覆盖 GCM（2026-11-14 实测）

**现象**：按常规 `git config credential.helper manager` + `git credential approve` 存库级令牌，`git credential fill` 能取回，但 `cmdkey /list` 查不到；approve 输出 `[git-credential]: store ignored`。

**Why**：全局存在 URL 级 helper：

```text
credential.https://cnb.cool.helper=!C:/Users/.../cnb.cmd git-credential
```

URL 级 helper 与通用 helper 一起参与；CNB helper 对 store 返回 ignored，导致 GCM 的写入不确定，而 `fill` 仍可能从 CNB 自己的存储或已有条目取到，看起来“成功”。

**How to apply**：

1. 先看 `git config --show-origin --get-all credential.https://cnb.cool.helper` 和 `git config --get-urlmatch credential.helper https://cnb.cool/<owner>/<repo>.git`。
2. 只想用 Windows 凭据管理器：给本仓库加 path 级 helper：
   `git config --local credential.https://cnb.cool/<owner>/<repo>.git.helper manager`
   `git config --local credential.https://cnb.cool/<owner>/<repo>.git.useHttpPath true`
   或直接 `cmdkey /generic:"git:https://cnb.cool/<owner>/<repo>.git" /user:<user> /pass:<token>`，再用 `cmdkey /list:"..."` 验证。
3. 不要求某个存储时，保留 CNB 专用 helper 也可以；关键是**一仓一令牌、按 path 存**，不要同一仓库同时散落多份不同令牌。
4. 无论用哪条，remote URL 不含 token；push 前用带 path 的 `git credential fill` 验证。

关联 [[git-credential-scope-and-rotation]]、[[cnb-use-repo-token-before-oauth]]。

### 追加：凭据管理器优先，`.local_secrets` 只作兜底（2026-11-23）

**经验**：取 CNB/Git 凭据先查 Windows 凭据管理器（`git credential fill` 带完整 path，或 `cmdkey /list`），不要只读 `.local_secrets/credentials.toml`；后者可能残留过期令牌，典型表现是 OpenAPI 401「credential expired」或 Git `Repository Not Found`。CNB 两把令牌分工：仓库令牌（带 `repo-code:rw`）用于 Git/仓库 API，但缺 `account-engage:r`，`/workspace/list` 会 403；全局令牌用于 workspace/账号级接口。把仓库令牌按 `git:https://cnb.cool/<owner>/<repo>.git` 存 GCM，把全局令牌存 generic 条目（如 `cnb2apigogo-all`）；迁移后删掉 `.gitconfig` 里的 `cnb.cmd git-credential` helper，改用系统 GCM，才能安全卸载 CNB CLI。

**Why**：只改 `.local_secrets` 会让脚本/人拿到旧值；CNB CLI 的 helper 还会抢在 GCM 前面，`store ignored` 让人误以为已写入。令牌权限是分层的，用错层会 403，不是「令牌没权限」。

**How to apply**：

1. 先按完整 path 取凭据，只检查 username/password 是否存在，不 echo：

```bash
printf 'protocol=https
host=cnb.cool
path=<owner>/<repo>.git

' | git credential fill
```

2. 仓库令牌用 GCM 存到 path 级条目；全局令牌存 generic 条目（`cmdkey /generic:<name> /user:cnb`，密码走凭据管理器输入，不放命令行）。
3. 设置 `credential.https://cnb.cool.useHttpPath=true`，删除 `.gitconfig` 的 CNB CLI helper 后，用 `git ls-remote` 对每个仓库复测；再卸载 `@cnbcool/cnb-cli`。
4. `.local_secrets` 只保留为服务器/无凭据管理器环境的兜底，不作为本机唯一来源。

关联 [[cnb-use-repo-token-before-oauth]]、[[git-credential-scope-and-rotation]]。

## credentials-never-in-memory-or-logs

**经验**：凭据原文不进记忆文件/kb 条目/会话内新建的任何文件/任何被跟踪文件。真值只允许落在两处：① 平台凭据库（Windows 凭据管理器/keyring）② `.local_secrets/`（仓库内已 gitignore）。需要"记住凭据相关事实"时写脱敏占位符+取值指针。

**Why**：把完整 PAT 明文写进记忆文件，用户要求"从上下文删除"时才发现。记忆/日志里的凭据副本既不会被 gitignore 覆盖也不会随凭据轮换自动清理。脱敏时用前缀正则整体替换（如 `github_pat_[A-Za-z0-9_]+`），别只遮尾巴。

**How to apply**：装凭据走管道不 echo（`printf '%s\n' '<token>' | gh auth login --with-token`），日志/exec/artifacts 天然零明文。任何"把这个凭据记下来"的冲动出现时先问：我记的是取值位置还是取值本身？位置才是持久信息，真值不是。
