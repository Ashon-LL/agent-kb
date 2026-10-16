---
name: codex-hook-command-must-be-valid-in-powershell
description: Codex 的 hook command 在 Windows 上是交给 PowerShell 执行的，「双引号串+双引号串」写法会 ParserError 让 hook 全量静默失败；要用无空格 .cmd 桥或加 & 调用符，且验收必须按执行器的复现方式做
type: pitfall
source: 本机 Codex Desktop 26.1007.2314（二进制字符串 + pwsh 复现 + trusted_hash 变更验收，2026-10-13/14）
date: 2026-10-14
verified: 2026-10-14
topic: powershell
---

**经验**：Windows 上 Codex 的 hook `command` 由 **PowerShell** 执行（二进制内含 `-NoProfile -Command`）。凡是「命令行里能跑、hook 里跑不了」的，先怀疑**执行器语法差异**，别先怀疑字段名/格式。

**现象**：桌面端 hook 面板「运行次数 6 / 未成功 6」，6 个 handler 全挂；但把同一条命令贴终端手敲完全正常。日志里搜不到 `kb_hooks` 字面量、也没有 spawned 记录。

**根因**：hooks.json 写的是
```
"command": "\"C:\\Program Files\\Python313\\python.exe\" \"C:\\...\\kb_hooks.py\""
```
这在 cmd / bash 里合法，但 PowerShell 里 `"a.exe" "b.py"` 不是合法调用语法（第一个引号串被当字符串表达式，第二个是意外 token），实测：
```
pwsh -NoProfile -Command '"C:\Program Files\Python313\python.exe" "C:\...\kb_hooks.py"'
ParserError: Unexpected token '"C:\Users\...\kb_hooks.py"' in expression or statement.
```
失败发生在**进程创建之前**，所以日志既无命令字面量也无执行记录 —— 极易误判成「hook 没被调度」或「schema 字段名不对」。

**判别顺序**：
1. 验收不许手敲原命令，要**按执行器的方式复现**：`pwsh -NoProfile -Command "<原样命令>"`，再喂 stdin JSON 看退出码与 stdout。
2. 面板计数是「调用尝试数」而非「配置条数」：6 = 3 事件 × 2 handler ⇒ 说明确实调度了，可用来否掉「没调度」的假设。
3. `config.toml` 里 `[hooks.state.'<源文件>:<event>:<gi>:<hi>'] trusted_hash` 的**变化** = App 重读该文件并重新信任，可当「配置已生效」判据。

**修法（两种均实测通过）**：
- 指向**无空格路径**的 `.cmd` 桥：`"command": "C:\\Users\\<u>\\.codex\\hooks\\kb_hooks.cmd"` —— 裸路径在 PowerShell 合法、cmd 也能跑，跨执行器最稳。
- 保留 python 但补调用符：`& "C:\Program Files\...\python.exe" "...\kb_hooks.py"` —— 仅 PowerShell 成立。

**附带事实**：
- hook 配置源：user 层 `$CODEX_HOME/hooks.json`（同层另一种写法 `$CODEX_HOME/hooks/hooks.json`，两者并存会告警 prefer a single representation）；project 层 `<repo>/.codex/hooks.json`（项目未信任不生效）；plugin `<plugin>/hooks/hooks.json` 与 `plugin.json#hooks`；managed `hooks.managed_dir`/`hooks.windows_managed_dir`。
- **`~/.agents/` 不是 hook 配置源**（二进制里 `.agents` 只关联 skills 根与插件市场）；`~/.agents/kb/kb_hooks.py` 只是被 hook command 点名的普通脚本。
- 改完 hooks.json 必然要再点一次「信任」（trusted_hash 不匹配），无感生效不存在。

**相关**：[[stated-provenance-needs-evidence-and-conditions]]（「没找到记录」≠「不存在」）、[[report-what-you-did-not-what-you-meant-to-do]]
