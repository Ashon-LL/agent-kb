---
name: runasadmin-breaks-dictation-and-dragdrop
description: 应用被设成「以管理员身份运行」后，普通权限的语音输入/输入法注入、拖放、部分剪贴板 IPC 全部失效；症状是「焦点在该应用就不行，焦点在桌面就行」
type: pitfall
source: zcodepro（2026-10-24 ZCode 微信语音输入失效）
date: 2026-10-24
verified: 2026-10-24
topic: windows, diagnosis, safety
---

**症状**：微信输入法的语音输入（默认 Ctrl+Win）在别的软件里正常，在某个 Electron 应用里**完全不触发**；
把焦点切到桌面按同一组合键却正常。应用内页面能收到 keydown（`Meta` 带 `ctrlKey`），所以不是应用吞键。

**Why**：Windows 的 **UIPI**。低（普通）完整性进程的全局键盘钩子收不到发往**更高完整性窗口**的按键，
合成输入（`SendInput`/TSF 注入）也进不去。所以只要前台窗口属于管理员进程，
普通权限的输入法/听写工具就"瞎了"——不只是语音输入，**从资源管理器拖文件进来**也会失效。

**How to apply**（排查顺序，30 秒）：
1. 看兼容性标记（exe 属性→兼容性→"以管理员身份运行"就写在这）：
   ```powershell
   $k='HKCU:\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
   (Get-ItemProperty $k).'C:\Program Files\<App>\<App>.exe'   # 形如 "~ RUNASADMIN"
   ```
   HKLM 同名键也要看；另：**快捷方式**自身也能带 RUNASADMIN 标记，删了 Layers 仍会提权。
2. 用 token 提权位确认实况（别只看 exe 清单，`asInvoker` 也可能被 compat 标记覆盖）：
   `OpenProcess` → `OpenProcessToken` → `GetTokenInformation(TokenElevation)`
3. 修复：删掉该 Layers 值（`Remove-ItemProperty`），或取消 exe 属性里的勾选；然后**完全退出应用再正常启动**。
4. 验证：主进程 `elevated=False`，再试语音输入/拖放。

**教训**：遇到"只有某个应用不行、换焦点就行"的输入类问题，先查前台窗口的完整性级别，别在应用代码里找。
关联 [[installer-completion-by-hash-not-mtime]]
