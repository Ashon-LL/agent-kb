---
name: ssh-heredoc-delimiter-must-be-quoted
description: 跨 shell 边界送文本（ssh here-doc / commit -m / 嵌套引号）的转义坑合集——定界符不加引号会提前展开 $VAR；-m 里的反引号会被命令替换吃掉；多层嵌套引号易断链，改「写文件再 scp」
type: pitfall
source: apishow（2026-10-05 astrbot 自动恢复脚本部署；2026-10-17 补三条同族实例）
date: 2026-10-05
verified: 2026-10-17
topic: methodology
---
<!-- hook-reviewed 2026-10-20：已人工确认 INDEX 钩子覆盖本条全部更新内容 -->


**经验**：给 ssh 喂 here-doc 时定界符必须加引号，`$` 才会在远端求值：

```bash
ssh host 'bash -s' <<REMOTE     # 坏：$SRV 在本地 bash 展开
ssh host 'bash -s' <<'REMOTE'   # 好：逐字送到远端，$SRV 由远端 shell 解析
```

实测（部署 `/opt/astrbot/restore_zhiqing_silence.sh`）：脚本里 `[ -f "$SRV" ]` 因 `$SRV` 被本地展开为空，变成 `[ -f "" ]` 判空失败。这次「先检查后写入」的顺序救了一命——若顺序反过来，写入就会落到错误路径上。

**Why:** 未加引号的 here-doc 正文先被本地 shell 处理一遍：远端变量名在本地被当成本地变量求值，本地没有就变空串，远端拿到的是已被替换过的脚本。与「bash 双引号里 `$_`/`$LASTEXITCODE` 被提前展开」同族——变量归哪一侧的 shell，只看引号。

**How to apply:** 凡跨 shell 边界送脚本（ssh / docker exec / nsis / 转义层），定界符一律加引号 `<<'EOF'`。确实需要本地展开的地方，把变量在正文外用 `-e` 或参数注入，别混写在正文里。判据：脚本里出现 `[ -f "$X" ]` 之类断言且 `$X` 定义在远端，就必须在远端求值。

相关：[[windows-scripting-terminal-gotchas]]（引号归属）、[[container-heredoc-needs-stdin-flag]]（stdin 转发）。

## 同族实例（2026-10-17 一日内踩齐三条，同一根因：文本在 shell 层被多解释一次）

1. **`git commit -m` 里的反引号会被命令替换**：`-m "…整表 \`margin:6px auto\` 居中…"` ⇒ 反引号内容被当命令执行
   （stderr 冒 `margin:6px: command not found`），提交信息里那两处**静默变空**，消息与事实不符；
   而因为项目铁律禁止 force push，**改不回来**。
   ⇒ 长提交信息一律 `git commit -F <file>`；`-m` 里**禁用反引号与 `$(`**，需要引号强调就用「」或单引号。
2. **多层嵌套引号（`ssh host '… '"'"'…'` 这类）会断链**：同一段远端 Python 检查脚本，写法一旦错一层，
   远端 bash 就开始执行脚本正文（症状是 `line 2: .env: command not found`、`span: No such file or directory`）。
   ⇒ 判据：**远端要跑的代码超过一行，就写成文件 scp 过去再执行**，别在 ssh 参数里堆引号。
3. **转义串在两层解释器里各吃一次**：用 `'    body = "\\n".join(L)'` 之类的锚点去 patch 文件，
   在 heredoc + Python 两层里 `\\n` 与 `\n` 会错位 ⇒ 锚点找不到（本次改成**按行匹配**才成功）。
   ⇒ patch/校验脚本优先用**行级匹配或行号**，别用含转义的字符串锚点。

关联 [[shell-init-files-are-layered-not-one]]、[[git-bash-ampersand-breaks-gh-auth-login]]、
[[windows-unquoted-path-redirect-accidents]]（同族：本地 shell 先动了一遍文本）、[[pkill-self-match-kills-own-shell]]。