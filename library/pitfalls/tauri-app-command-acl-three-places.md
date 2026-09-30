---
name: tauri-app-command-acl-three-places
description: Tauri 2 自定义命令要在前端 invoke 通，必须同一命令名在三处（handler/build.rs/capabilities）同时出现，缺一处静默失效
type: pitfall
source: MH-Agent-Open D-44/D-46（拖动桥 + restart_backend）
date: 2026-09-22
verified: 2026-09-22
---

**经验**：Tauri 2 里每个 `#[tauri::command]` 想被前端 `invoke('cmd_name')` 调通，
**命令名必须同时出现在三处**，缺任何一处都**静默失效**（前端只拿到一个 rejected
promise，甚至零报错）：

1. `src/lib.rs` 的 `tauri::generate_handler![...]` —— 注册；
2. `build.rs` 把它报给 `tauri_build::AppManifest::commands(...)`；
3. `capabilities/default.json` 的 `permissions` 里放行 `allow-<命令名>`。

**Why**：三处的失败形态各不相同，但**都不报错**：

- 漏了 ③ ⇒ 运行期 `resolve_access()` 拒，报 `Command X not allowed by ACL`。
  但前端若 `await invoke(...)` 外面没 catch，用户看到的就是「按钮没反应」。
- 漏了 ② ⇒ `tauri-build` **一个 `allow-*` 都不生成**（`acl.rs`：
  `if manifest.commands.is_empty() { Vec::new() }`）⇒ ③ 写什么都 `Permission not found`，
  **构建期**就挂。所以 ② 是 ③ 的前提。
- 权限名形态错 ⇒ 构建期 `Permission ... not found`。生成规则是
  `command.replace('_', "-")` ⇒ `restart_backend` → `allow-restart-backend`
  （**连字符**，不是下划线）。

**How to apply**：

- 新增命令时，**三处一起改**，别指望编译器提醒你。写一条**集合对账**测试：
  用正则从 `generate_handler![]` 解析出命令集，与 `build.rs` 的命令集作**双向**
  差集断言（单向只能抓一半）；再拿同一集合与 capabilities 的 `allow-*` 对账。
  ⛔ 单点断言（`for cmd in ("a","b","c"): assert ...`）会在新增命令时**悄悄漏掉**
  —— 本仓就是这样把 `restart_backend` 漏了很久（D-46）。
  若要允许「有意不放行」，保留一个**显式 `waived` 字典**并要求每条写清理由，
  否则「一律放行」会掩盖真实意图。
- 判「权限名对不对」**别只看源文件**：`cargo check` 能过就说明 `tauri-build`
  认了这个名字（错形态是构建期错误）；进一步看 `gen/schemas/capabilities.json`
  —— 那是**解析后**的 ACL，能证明它真的进了产物而不是只写在源里。
  终极取证：`strings -a <exe> | grep -c allow-<cmd>`（本仓用这个确认过
  安装区 exe 到底有没有带上新权限）。
- 只看「应用级命令」，别把插件命令（`core:*` / `shell:*`）混进对账集合。

相关：[[tauri-linux-ci-needs-webkit-41-and-target-override]]、[[tauri-remote-url-has-no-ipc]]
