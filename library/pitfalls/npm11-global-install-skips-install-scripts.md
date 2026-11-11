---
name: npm11-global-install-skips-install-scripts
description: "npm 11.19+ 全局安装默认不跑 install scripts：只 warn、exit 0、--version 正常，原生依赖缺 postinstall 时运行时才崩；须用 --allow-scripts 补跑并实际 require/spawn 验收"
type: pitfall
source: APIShow 多服务器管理（2026-11-10，apishow-prod / qiniumei 安装 @deepseek-ai/dsh 0.2.2-rc.1）
date: 2026-11-10
verified: 2026-11-10
topic: toolchain
---

# npm 11 全局安装静默跳过 install scripts

## 经验

- npm **11.19+** 对全局安装启用 `allowScripts` 白名单：未列入的包，其 `install` / `preinstall` / `postinstall` 脚本**不执行**。
- 表现是**只 warn 不报错**：

  ```
  npm warn install-scripts 5 packages have install scripts not yet covered by allowScripts:
  npm warn install-scripts   node-pty@1.2.0-beta.15 (install: node scripts/prebuild.js || node-gyp rebuild; ...)
  ...
  added 654 packages in 1m
  ```

  退出码 0，`<cli> --version` 也正常。

- 补跑：把 warning 列出的包名原样贴进参数：

  ```bash
  npm install -g <pkg> --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs
  ```

  或一次写进用户配置：`npm config set allow-scripts=<列表> --location=user`。

- 依赖位置：全局包的依赖常被**嵌套**装在 `<prefix>/lib/node_modules/<pkg>/node_modules/`，不在顶层；`require` 前把 `NODE_PATH` 指到那里。

## Why

- 静默跳过 = 「装好了」的假象：缺 postinstall 生成物（如 spawn helper）或原生模块没编译，安装阶段一切正常，**到运行时才崩**，现场离病因很远。
- 有 prebuild 的包（node-pty / koffi 都带 linux-x64 预编译）会**侥幸可用**，于是表现为「有的机器好、有的机器坏」，比直接失败更难查。
- 只看 `--version` 无法区分：它只读 package.json，不加载原生依赖。

## How to apply

1. 任何 `npm install -g` 出现 `npm warn install-scripts`，**立即**用 `--allow-scripts=<列表>` 重跑，再验收。
2. 验收要打到真功能，不看版本号：

   ```js
   // node-pty：真 spawn 一次
   const pty = require('node-pty');
   const p = pty.spawn('/bin/echo', ['pty-ok'], {name:'xterm-color', cols:80, rows:24});
   p.onData(d => process.stdout.write(d));
   p.onExit(e => console.log('exit', e.exitCode));

   // koffi：真调一次 FFI
   const libc = require('koffi').load('libc.so.6');
   console.log(libc.func('int getpid()')() > 0);
   ```

   跑法：`NODE_PATH=<prefix>/lib/node_modules/<pkg>/node_modules node -`。

3. 定位原生二进制：`find <prefix>/lib/node_modules -name 'pty.node' -o -name 'koffi.node'`；存在 ≠ 能加载，仍要跑第 2 步。
4. 版本边界：本条目实测 npm **11.19.1** / node **24.22.2** / Debian 12（2026-11-10）。项目内安装禁止该参数的情形见 [[remotion-project-gotchas]]。
