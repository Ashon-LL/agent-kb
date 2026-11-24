---
name: audit-capability-check-artifact-before-marking-unimplemented
description: 审计报告把某能力判成「未实现/无消费者」时，先在最终产物里 grep 关键类/函数/设置键并追到调用点；不要凭技术栈假设（如 undici 不支持 SOCKS）判未实现
type: pitfall
source: zcodepro 2026-11-14 v29.21 Wave 3 审计复核（CLI SOCKS、J-P2-3 两个设置键）
date: 2026-11-14
verified: 2026-11-14
topic: verification
---

**经验**：审计项说「未实现 / 无消费者 / 死设置」时，先在**最终产物**里 grep 关键符号，再追到真实调用点；不要凭技术栈假设或源码里的旧注释定性。对网络能力，先查 bundled dependencies 是否已包含对应 agent；对设置键，先追到渲染层/IPC 消费点。

**Why**：zcodepro v29.21 审计曾判 CLI SOCKS「未做」，依据是 undici 限制；实际 CLI 已打包 `proxy-agent` 的 `SocksProxyAgent`，且主进程已把 SOCKS URL 写入官方 `network.httpProxy`，全链路成立。同一轮中两个设置键也被判成「疑似死项」，实际 `off/styles` 里分别有 `fileTreeHtmlClickOpensBrowser===!0` 和 `computerUseComposerEntryHidden!==!1` 的读取点。凭假设判未实现会导致重复造轮子、错误记录未修项，甚至把已有能力改坏。

**How to apply**：① 定性前先 grep 最终产物（asar/CLI/渲染包）中的关键类、函数、设置键；② 对设置键/函数，用 `grep -n` 或源码上下文追到 UI/IPC/主进程消费点，别只看 schema；③ 对网络代理/协议能力，查 bundle 是否已打包 `proxy-agent`/`socks-proxy-agent`/`undici` 等依赖；④ 把误报写入对账报告并附可点击证据；⑤ 修复前以最新源码上下文为准，不盲信审计行号；⑥ 若审计工具本身版本漂移，先核对工具期望值（见 [[acceptance-tool-version-drift-false-failure]]）。
