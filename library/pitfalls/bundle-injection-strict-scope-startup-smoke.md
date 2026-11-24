---
name: bundle-injection-strict-scope-startup-smoke
description: 注入打包产物的顶层代码不能依赖隐式全局；交付前必须真实启动冒烟，node --check 只查语法
type: pitfall
topic: delivery
source: zcodepro 2026-11-15（03ff 包启动即崩：preparing_session_storage / transport_closed）
date: 2026-11-15
verified: 2026-11-15
---

**经验**：向 minified / 打包产物注入顶层代码时，先确认宿主作用域。严格模式模块里的
裸赋值（`x=function…`，没有 `var/let`）会在**模块求值期**抛 `ReferenceError`；
`node --check` 只查语法，完全看不见。交付前必须真实执行一次启动命令。

## 发生了什么（2026-11-15）

给 CLI 注入「自定义请求路径/查询参数」的辅助函数时，把它作为逗号项塞进了一串既有裸赋值：

```js
I6e=64e3,Qgt=1e3,…,Ofo="Authorization",__zsmEndpointOverrideFetch=function(f,ov){…},e0t=class{…}
```

`I6e/Ofo/e0t` 在模块别处有 `var` 声明，新名字没有 ⇒ 严格模式求值期
`ReferenceError: __zsmEndpointOverrideFetch is not defined`。CLI 进程在写日志前就退出，
宿主为存储准备拉起的 Worker 随之关闭，界面报「无法完成启动准备」，
宿主日志 `phase=failed failedPhase=preparing_session_storage errorCode=transport_closed`。

## 判据与诊断

- 子进程日志在故障时段**零行** + 宿主 `transport_closed` ⇒ 先怀疑子进程模块求值期崩溃。
- 直接在 shell 里跑同一入口：`cd /tmp && node <cli> --version`，复现到 ReferenceError。
- `node --check` / 字符串锚点断言 / 执行型单测都可能在**没加载真实模块**的情况下通过。

## 规则

1. 注入前确认：文件是否 `"use strict"` / ESM；目标名字是否已有声明；注入点是不是表达式语句/逗号列表。
2. 优先**调用点内联**（全部用局部参数）或挂到**已存在的显式对象**（`globalThis.xxx`、既有命名空间），
   不要新增模块级裸名字。
3. 门禁分层：`node --check`（语法）→ `node <entry> --version`（模块求值/启动）→ 宿主实际拉起路径。
   启动冒烟失败即禁止出构建/出包。
4. 事故重发用新交付目录；坏包保留取证但明确标注「勿用」，避免用户拿到旧链接。
5. 修复后被注入点要有执行型回归：从真实产物抽出实现执行，并断言坏形式（裸赋值）零命中。

## 追加形态（2026-11-16）：测试沙箱喂假符号 = 假绿

产物里 `function home(){return __ZsmHome();}`，而主进程真实定义只有小写 `__zsmHome()`；三个测试都把 `__ZsmHome` 作为 `new Function` 的参数喂进沙箱，于是测试全绿、实机点「扫描可用模型」必报 `__ZsmHome is not defined`。这与严格模式裸赋值是同一个病根：**测试环境注入了产品里不存在的符号**。

判据与修法：
- 沙箱参数表就是「产品必须提供的符号契约」。新增/改名外部符号时，必须去最终产物确认它有真实定义（`grep "function <name>("` / 写入点），不能只改测试参数让它绿。
- 修这类 bug 要补两类断言：① 坏符号零命中（产物里 `__ZsmHome(` 计数为 0）；② 真作用域负控——**不**把该符号作为沙箱参数，初始化必须不抛错（若仍引用坏符号会 ReferenceError）。只有正向链路测试不算验证。
- 顺带：给文件/符号起名别带基线编号（如 `patch_main_model_ctx_3180.py`）——官方/果冻都没有这种语义标签，跨基线复锚时「名字像当前代」会掩盖「内容实为旧代符号」，本案的 `__ZsmHome` 就是这种旧代命名残留。改用职责名 `patch_main_model_context.py`。

关联 [[rebuilt-bundle-diff-needs-stable-anchors]]、[[installer-completion-by-hash-not-mtime]]。
