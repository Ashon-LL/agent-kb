---
name: ssh-heredoc-delimiter-must-be-quoted
description: ssh host '...' <<REMOTE 定界符不加引号会把远端 $VAR 当成本地变量提前展开成空串，远端逻辑静默跑偏
type: pitfall
source: apishow（2026-10-05 astrbot 自动恢复脚本部署）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
---

**经验**：给 ssh 喂 here-doc 时定界符必须加引号，`$` 才会在远端求值：

```bash
ssh host 'bash -s' <<REMOTE     # 坏：$SRV 在本地 bash 展开
ssh host 'bash -s' <<'REMOTE'   # 好：逐字送到远端，$SRV 由远端 shell 解析
```

实测（部署 `/opt/astrbot/restore_zhiqing_silence.sh`）：脚本里 `[ -f "$SRV" ]` 因 `$SRV` 被本地展开为空，变成 `[ -f "" ]` 判空失败。这次「先检查后写入」的顺序救了一命——若顺序反过来，写入就会落到错误路径上。

**Why:** 未加引号的 here-doc 正文先被本地 shell 处理一遍：远端变量名在本地被当成本地变量求值，本地没有就变空串，远端拿到的是已被替换过的脚本。与「bash 双引号里 `$_`/`$LASTEXITCODE` 被提前展开」同族——变量归哪一侧的 shell，只看引号。

**How to apply:** 凡跨 shell 边界送脚本（ssh / docker exec / nsis / 转义层），定界符一律加引号 `<<'EOF'`。确实需要本地展开的地方，把变量在正文外用 `-e` 或参数注入，别混写在正文里。判据：脚本里出现 `[ -f "$X" ]` 之类断言且 `$X` 定义在远端，就必须在远端求值。

相关：[[windows-scripting-terminal-gotchas]]（引号归属）、[[container-heredoc-needs-stdin-flag]]（stdin 转发）。

关联 [[shell-init-files-are-layered-not-one]]、[[git-bash-ampersand-breaks-gh-auth-login]]。