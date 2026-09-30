---
name: tauri-remote-url-has-no-ipc
description: Tauri v2 窗口指向 http(s) URL（含 localhost）时 invoke() 被 ACL 拒绝而非 __TAURI_INTERNALS__ 缺失；权限名要把 _ 换成 -
type: pitfall
source: Tauri v2 远程 URL 实测（2026-09-21）
date: 2026-09-21
verified: 2026-09-21
topic: tauri

---

# Tauri：非 tauri:// 来源的 invoke() 被 ACL 拦，不是对象缺失

⛔⛔ **20260922 更正（重要）**：本条此前把机制写错了。
旧结论「`window.__TAURI_INTERNALS__` 为 undefined」**不对**。
真相：**对象一直在，`invoke()` 能调，但调用被 ACL 拒绝**。
症状一样（「点了没反应」），根因不同 ⇒ 旧结论会把修复引向完全错误的方向。

## 事实（Tauri 2.11.5 源码逐行核实）

窗口 URL 为 `http://localhost:PORT` 这类非 `tauri://` 来源时：

| 环节 | 行为 | 源码位置 |
|---|---|---|
| 初始化脚本注入 | **无条件注入**，不看 URL ⇒ `window.__TAURI_INTERNALS__` **存在**、`T.invoke` **是函数** | `manager/webview.rs:182`（`invoke_initialization_script` 无 URL 分支） |
| 来源判定 | `is_local_url()` 只认 ① `tauri://` ② 相对 `devUrl`/`frontendDist` ③ 已注册自定义协议 ⇒ `localhost:18088` = **remote** | `webview/mod.rs:1698` |
| 授权门 | `!is_local` ⇒ 必过 ACL；`resolve_access()` 查不到 ⇒ 拒绝 `"Command X not allowed by ACL"` | `webview/mod.rs:1823`、`ipc/authority.rs:439` |

**所以「远程 URL 不给 IPC」是误读**：给的是 IPC **句柄**，不给的是 IPC **许可**。

## 修法：补权限，且权限名要把下划线换成连字符

`tauri-build` 为每个 `#[tauri::command]` 自动生成 `allow-$command` 权限，
**但生成前会把 `_` 全部替换成 `-`**（`tauri-utils/acl/build.rs:290`：
`let slugified_command = command.replace('_', "-")`）。

⇒ 命令 `mha_drag_move` 的权限标识是 **`allow-mha-drag-move`**（连字符），
不是 `allow-mha_drag_move`（下划线）。写错形态会报 `Permission not found`。

还需给来源放行：capability 里加
```json
"remote": { "urls": [ "http://localhost:18088" ] }
```
⚠ 单独加 `remote` **不够** —— 必须同时有 `allow-<command>` 权限，否则
`resolve_access()` 仍返回 None。

## 为什么危险（静默性，这条仍然成立）

`fetch()` 这类普通 HTTP 照常工作，只有 IPC 坏 ⇒ 应用「看起来正常」。
前端 `.catch()` 常吞掉 ACL 拒绝 ⇒ 表现为「点了没反应、无报错」。

**实战踩到的两个连带缺陷（机制已更正，事实不变）**：
1. 一个「重启后端」按钮（`invoke('restart_backend')`）一直是坏的，长期无人察觉；
2. 「窗口标题栏主题跟随」（`setTheme`）从未生效过，而代码、权限、构建产物全绿。

## 三条出路（按代价排序）

1. **补 ACL**：`permissions` 加 `allow-<cmd>`（连字符）+ `remote.urls`。最便宜，
   且 invoke 是**进程内**往返，零网络面。
2. **绕开 IPC，走自有通道**：前端 → 后端 HTTP → 后端 → Rust 侧
   （指令文件轮询，零新增监听面）。适合「一次性」动作；
   ⛔ **不适合持续型交互**（拖动）—— 每帧都付轮询延迟，见 [[tauri-remote-url-has-no-ipc]] 的
   「连续流别走离散事件通道」教训（见下）。
3. **Win32 原生**：`SetWindowLongPtrW(GWL_WNDPROC)` 子类化 + `WM_NCHITTEST`
   返回 `HTCAPTION`。完全不依赖 Tauri，零 IPC 零延迟，但要写 unsafe。

## ⛔ 连续型交互（拖动）别塞进离散通道

把「拖动」这类**持续型**交互塞进为「按钮点击」这类**一次性**交互设计的通道，
代价是**三处延迟串联且每帧必付**（rAF + 传输 + 轮询空转 + 下一帧 rAF）
⇒ 端到端 33~55ms + 每帧文件读写 ⇒ 窗口必然落后鼠标，表现为「几乎不动」。

修法二选一：**① 走进程内 IPC**（补 ACL，见上面第 1 条），
或 **② 走 Win32 原生 hit-test**（第 3 条）。
⛔ 正确反应不是「把轮询间隔从 16ms 调到 8ms」—— 那是在错路上加码。

## ⛔ 别在错的假设上静默降级

若「桥」是否可用只判**存在性**（`typeof bridge.start === 'function'`）而不判**功能性**，
则「桥装上了但 invoke 被拒」的情形下：桥已定义 ⇒ 回落路径永远不触发 ⇒
结果是**完全不动**（比「几乎不动」更糟），且零报错。
降级门必须判**首次调用是否成功**，不是「对象在不在」。

## 已验证过但容易写错的 Tauri API

| 想做的事 | ❌ 错的写法 | ✅ 正确的 |
|---|---|---|
| 给已建好的窗口挂页面加载回调 | `WebviewWindow::on_page_load(...)` | **不存在**（`E0599`）。`on_page_load` 只在 `WebviewWindowBuilder` / `WebviewBuilder` 上 |
| 给 conf.json 声明的窗口注初始化脚本 | 在 `setup` 里找 builder | `Builder::default().append_invoke_initialization_script(js)` —— builder 追加的脚本排在**核心 IPC 脚本之后**执行，故 `__TAURI_INTERNALS__` 可用 |
| 运行期执行 JS | 依赖注入管线 | `Webview::eval()`（走原生句柄，不经注入管线，与 URL 是否 remote 无关） |

⚠️ builder 追加脚本的执行次序是**踩过坑才知道的**：
`manager/webview.rs:222-224` 把 builder 追加的 `initialization_scripts` **最后** extend，
所以它必然晚于 Tauri 自己的核心脚本 ⇒ 握手可靠。用 `WebviewBuilder::initialization_script`
之外的时机（比如自建握手脚本早于核心脚本）会拿不到 `invoke`。

## 纪律

- 诊断这类问题**必须在壳内实测**，不能只读源码/权限/产物。
- **改 Rust 必须真编译一次**：容器里 `which cargo` 为空就根本发现不了 `E0599`。
  「只用了既有 API」不等于「API 存在于你想调的那个类型上」。
- 做窗口级功能前**先确认 IPC 是否真的被 ACL 放行**（看 `permissions` 里的 `allow-<cmd>`）。

关联 [[tauri-app-command-acl-three-places]]。
