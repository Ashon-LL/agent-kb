---
name: git-remote-ownership-check
description: 本机并存 GitHub/Gitee/CNB 多套 git 平台，任何 git 读写前先核对仓库归属与目标 remote
type: workflow
source: ailika/agent-guard 会话（2026-09-14 用户立规）
date: 2026-09-14
verified: 2026-09-14
topic: git, cnb, methodology
---

**经验**：执行任何 git 操作（fetch/pull/push/ls-remote/建 PR/MR）前，先 `git remote -v` 核对三件事：① 该仓库在哪些平台有分身（GitHub、Gitee、CNB 可能同名不同仓）；② 本次操作的目标 remote 扮演什么角色（上游 / fork / 开发主线）；③ 本地跟踪引用（origin/main 等）可能过期——跨平台比对一律 `git ls-remote <remote> <ref>` 或平台 API 实测，不信本地缓存。

**Why**：同一项目在三个平台并存时，推错平台、或拿过期跟踪引用当现状，都会造成误判。实例：agent-guard 本地 origin/main 停在旧提交，三点 diff 虚报 25 个文件；GitHub compare API 实测真实差异只有 2 提交 5 文件。

**How to apply**：push/PR 前额外核对身份归属：提交邮箱用哪个平台的认可格式（GitHub noreply 与 CNB noreply 不同）、PR/MR 建在哪个平台的哪个仓。跨平台搬运（发布）先向用户确认目标平台再动手。

---

## 「默认分支」的权威判据只有一条（2026-09-26 实测补）

上面第③点「本地跟踪引用可能过期」有一个**专属高频形态**，值得单独钉死，因为它长得太像权威判据：

⛔ **`git symbolic-ref refs/remotes/origin/HEAD` 不是查远端默认分支的命令。**

它读的是本地 clone 时写入的 `refs/remotes/origin/HEAD` 符号引用 —— **平台侧改了默认分支，本地不会自动更新**。它回答的是「我 clone 的时候默认分支是谁」，不是「现在是谁」。

唯一权威判据（直连远端，不读本地缓存）：

```bash
git ls-remote --symref origin HEAD
```

输出第一行的 `ref:` 才是真实值；第二行的 sha 可与 `git ls-remote --heads origin` 各分支 sha 交叉验证。

**实测案例**（MH-Agent-Open 2026-09-26，起草 AGENTS.md 时踩到）：

| 命令 | 输出 | 真值？ |
|---|---|---|
| `git symbolic-ref refs/remotes/origin/HEAD` | `refs/remotes/origin/master` | ❌ 本地过期缓存 |
| `git ls-remote --symref origin HEAD` | `ref: refs/heads/feat` | ✅ 远端真值 |

交叉验证：远端 HEAD sha `7e5dba5` == `refs/heads/feat` 的 sha，而 `master` 是 `23ced6e` —— 两个分支已分叉，缓存值不只是"旧"，是**另一个分支**。

后果不是无害的：据此把「默认分支 = master」写进了交付文档的权限条款与变更日志，还把仓库 README 里的正确表述判成了"与远端冲突、需修正"。**用户当场纠正**才翻案。同族错法：把正确的既有约定当成过时需要改（与 [[config-field-name-is-not-spec-read-consuming-code]] 同源 —— 误判来自我的取数方式，不来自被判对象）。

**How to apply**：问「远端默认分支 / 远端某 ref 现在是什么」一律 `git ls-remote --symref`（或 `--heads`）；`refs/remotes/*` 系列一律视为**可能过期的本地快照**。写进交付物时把权威命令一并写上，防止后来者用错命令复验出相反结论。

### 把过期缓存也修掉（2026-09-27 补）

上面只讲了「别信它」，但**没讲可以清掉它**——留着污染值，换会话还会再踩一次。

```bash
git remote set-head origin feat        # 指向某个已知正确的分支
git remote set-head origin --auto      # 或从远端重新探测写入
git remote set-head origin --delete    # 仅删除该符号引用
```

`git remote set-head` 只改本地 `refs/remotes/origin/HEAD` 这一个符号引用：
**不碰远端、不改任何提交、不动工作区、不影响 HEAD 或本地分支**。属于安全操作。

动手前值得花 10 秒做的检查：`grep -rn "origin/HEAD" --include="*.py" --include="*.ps1" --include="*.yml" --include="*.sh" .`
——确认没有脚本依赖它（有则那条脚本本身也在用过期判据，要一并改成 `--symref`）。

修复后三条应当一致，用这组命令一次验完：

```bash
git symbolic-ref refs/remotes/origin/HEAD   # refs/remotes/origin/feat
git ls-remote --symref origin HEAD          # ref: refs/heads/feat
git rev-parse --abbrev-ref origin/HEAD      # origin/feat
```

并跟 `git ls-remote --heads origin` 各分支 sha 交叉验证（sha 能对上才是真对齐，
只看名字会漏掉"名字改了但指错 sha"的情况）。

**MH-Agent-Open 实例**：本机 `refs/remotes/origin/HEAD` 停在 `master`，远端真值是 `feat`。
`git remote set-head origin feat` 修完后 `origin/HEAD` sha `0aa45e7` == 远端 HEAD sha，
两条命令输出首次一致。⇒ **同一件事要做两次**：①.protocol 里写死正确命令；②把本机污染值清掉。
只做①，下个会话用顺手的 `symbolic-ref` 一查还是假答案。
