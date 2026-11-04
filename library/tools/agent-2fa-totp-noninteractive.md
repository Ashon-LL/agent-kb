---
name: agent-2fa-totp-noninteractive
description: 网页登录被 2FA 卡住时给 Agent 一条能出码的命令：主密码存 Windows 凭据管理器（cmdkey / CredRead）+ keepassxc-cli show -t；并记下 keepassxc-cli 2.8 写不了 TOTP 属性、pykeepass 保存会写坏 KeePassXC 库两个硬坑
type: tool
source: 2026-10-24 default 会话（GitHub 2FA 启用 + Agent 自动化链路恢复）
date: 2026-10-24
verified: 2026-10-24
topic: security
---

**经验**：

1. **卡点特征**：账号开了 2FA 之后，`gh` CLI 用 PAT **完全不受影响**，但**走网页 UI 的自动化**会停在「输入 6 位验证码」，Agent 拿不到第二因子 → 整条流程死锁。判断是"用户此前能自动化、现在不行"时，先分清是 CLI 通道还是网页通道。

2. **可用的解法（本机已验证）**：密码库主密码存进 **Windows 凭据管理器**（`cmdkey /generic:<target> /user:<user> /pass:<pw>`），helper 用 `CredRead`（advapi32，type=1 CRED_TYPE_GENERIC）取回明文，管道喂给 `keepassxc-cli show -t <db> <entry>`，从 stdout 抓 `^\d{6}$` 那一行。落地为 `C:\Software\AgentTools\get-totp.ps1` + `get-totp.cmd`。
   - **作用域是"每个条目"不是"所有网站"**：默认条目只指向一个站点（本机是 GitHub），别的站点必须 `-Entry "<条目名>"`，且该条目得先在 GUI 里配好 TOTP；把工具写成"任何网站都能出码"是过度声明。
   - **找不到条目时要能自解释**：条目不存在时脚本用 `keepassxc-cli ls -R` 列出库里全部可用条目再退出（exit 4），这样 Agent 能自己挑，不用反问用户。
   - 退出码分离：`2`=凭据管理器没这条、`3`=keepassxc-cli 不存在、`4`=条目没有可用 TOTP；错误一律走 `[Console]::Error.WriteLine`（用 `Write-Error` 会带出 PowerShell 堆栈噪音且把退出码变成 1）。

3. **⛔ keepassxc-cli 2.8 写不了 TOTP**：`add` 与 `edit` 都没有 `--totp` 或属性写入参数，CLI 只能读（`show -t`）不能写。写只能走 GUI「条目 → TOTP → 设置 TOTP」——**直接输入 base32 密钥即可**（GitHub 那种 16 位字母数字），不必拼 `otpauth://` URI；配好后 CLI 立刻就能读到码（实测通过）。

4. **⛔ 别用 pykeepass 写 KeePassXC 的库**（pykeepass 4.2.0 实测）：CLI 建的库 → CLI 读 OK → pykeepass 打开并 `save()` → CLI 报「标头与哈希不匹配」退出码 1；再 save 一次也救不回。隔离实验可稳定复现（保存前 CLI OK、保存后 CLI FAIL）。要写库只用 keepassxc-cli，TOTP 属性走 GUI。

5. **PowerShell 调原生命令的坑**：`$ErrorActionPreference='Stop'` 会把原生程序的 stderr 变成 `NativeCommandError` 终止错误——而 keepassxc-cli 的「输入密码以解锁…」提示恰好走 stderr。调用前后临时切 `'SilentlyContinue'` 并还原，同时用变量保存 `$LASTEXITCODE`（`2>$null` 单独用不够）。

6. **`.cmd` 包装要 CRLF + `title`**：Write 工具产出是 LF，须用 `[IO.File]::WriteAllText` 转换；⚠️ 转换脚本里若替换失败导致 `$t` 为 null，`WriteAllText` 会把文件**清空**（本次真实踩到），转换后要校验字节数与 CRLF 对数。

**Why**：2FA 的设计前提是「第二因子只能由人提供」。一旦要求 Agent 自动操作网页，就必须给机器一条可编程的取码路径，否则每个需要登录的网页流程都会在验证码这一步死锁——而这类死锁表现为"页面卡住"，很容易被误判成网络或选择器问题。

**How to apply**：任何「Agent 需要登录带 2FA 的网站」的场景。换账号/换库只改凭据目标名与条目名，helper 不动。⚠️ 代价必须在交付时说清：凭据管理器里的条目**对该用户下任何进程都可读**，所以这套配置下 2FA 退化为「多一步」而不是隔离边界，只在「自动化优先于防本机恶意进程」的个人机器上成立。凭据原文不进本文件、不进日志、不进记忆。相关：[[credentials-never-in-memory-or-logs]]、[[credential-rotation-must-cover-all-entries]]。
