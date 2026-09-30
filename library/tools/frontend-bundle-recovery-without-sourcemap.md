---
name: frontend-bundle-recovery-without-sourcemap
description: 生产不部署 .map 时，从入口 JS 的 chunk 清单+公开 CDN 路径复原完整前端 bundle 与 API 面的方法
type: tool
source: SRC 挖洞项目千问线实测（2026-09-23）
date: 2026-09-23
verified: 2026-09-23
topic: browser
---

**场景**：逆向/侦察某 Web 应用，"抓 JS bundle"失败（入口只有几百字节 webpack runtime），或 sourcemap 404。

**方法（按序）**：
1. **入口 JS 里有两个金矿**：① webpack chunk 清单（`Promise.all([i.e("2354"),i.e("1558")...])`——所有异步 chunk 的 ID）；② `//# sourceMappingURL=main.<hash>.js.map`——暴露**构建版本号**（hash）。
2. **直接试 `<部署域>/js/main.<hash>.js.map`**：404 且返回 Spring 风格 JSON（`{"status":404,...}`）= 生产构建排除了 map，别再找 map。
3. **chunk 和主文件在公开 CDN**：阿里系通例 `g.alicdn.com/code/npm/@ali/<pkg>/<版本>/web/js/`。版本号从哪来——**先抓首页 HTML 的 `<script src>` 列表**（runtime 里没有 publicPath，但首页一定引了真实 CDN 全链）。用首页的 hash 对齐入口 JS 的 sourceMappingURL hash 确认同版本。
4. chunk 路径 = CDN 基址 + `async/<id>.js`（入口清单里的 ID 逐个下；个别 404 = 该版本已删除，跳过）。
5. **无 map 也够用**：压缩代码的字符串常量包含全部端点路径、请求体字段名、host 常量表（`grep -oE` 提路径，再取匹配点 ±400 字符看调用处拿参数结构）。本次 ~5.6MB 压缩码提取出约 90 个端点+主机拓扑，未读一行源码。

**Why**：前端 sourcemap 本身在 SRC 场景属低危（不收），但用 map/chunk 清单做**侦察**是合法被动的，价值在 API 面重建而非提交 map 泄漏。

**How to apply**：遇到"入口 JS 太小/只有 runtime"别判失败——提取 chunk ID 清单 → 首页 HTML 找 CDN 基址和版本 → 批量下载 → 正则提 API 路径 → 对每个路径取调用点上下文还原请求形状。抓已发出请求的兜底用 `performance.getEntriesByType("resource")`（页面内 hook fetch 会被导航清掉）。
