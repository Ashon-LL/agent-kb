---
name: github-china-network-workarounds
description: 大陆网络 GitHub 双向通路——下载向（jsdelivr 镜像/curl 续传/WARP）与推送向（探测+hosts+推送一体循环，分步必败）；推送脚本全文在源指南
type: tool
source: ebot（arduino-cli 实测）+ mh-agent-open（推送兜底指南）；2026-09-14 两条晋升、2026-09-15 合并
date: 2026-09-15
---

**经验**：本机到 GitHub 的连通性问题是**双向、秒级波动**的，两条通路分开治理。

## 下载向（raw 不可达 / release 大文件中断）

- 本机网络 `raw.githubusercontent.com`/GitHub Pages 超时不可达，`github.com` release 间歇可下但大文件中途断。
- JSON 索引/小文件换 jsdelivr 镜像：`https://cdn.jsdelivr.net/gh/<owner>/<repo>@<branch>/<path>`（gh-proxy.com、ghfast.top 也可达）。
- 大文件续传进工具缓存目录：`curl -L -C - --retry 15 --retry-all-errors -o <精确文件名> <url>`，放工具的 staging 目录（arduino-cli 是 `~/AppData/Local/Arduino15/staging/packages/`），下次安装会自动校验复用。
- 还不行请用户开 Cloudflare WARP 再试大二进制。

## 推送向（git push 随机 timeout/reset/EOF）

- 到 github.com 部分 IP 通部分被干扰、分钟级翻转，"先测通→再改 hosts→再推"的分步方案在间隙里 IP 状态已变，**必败**——这是网络本质不是代码问题。正解=四件事同一个循环：
  1. **真握手探测**：候选 IP:443 做 TLS 握手（SNI=github.com）。⛔别用 ping/TCP connect（ICMP 可禁而 443 通）。
  2. **hosts 只在推送进行中临时改**：只动 `IP github.com` 精确行（正则锚定），绝不殃及 raw./api.github.com。
  3. **try/finally 无论成败恢复 hosts 原始字节** + flushdns——曾因异常退出没恢复把 hosts 清到剩一行（血泪事故）；进程被强杀是唯一例外，运行期别关终端。
  4. **候选 IP 段自更新**：内置 140.82.x 段，全失败从 `api.github.com/meta` 拉最新段。
- 适用 HTTPS 远程（SSH 走 22 端口需自改探测端口与候选段）；API 也被干扰时同法对 `api.github.com` 做，候选取 meta 响应 `api` 字段、正则单独写。
- 脚本全文（约 80 行纯标准库，Windows）见 `Downloads/Project/DeepSeek/GitHub推送网络兜底指南-给其他项目.md` 第五节，新项目拷成 `scripts/push_with_ip_retry.py` 或配 `git alias pushx`。
- ⛔ 探测循环也救不活 git 传输时，改走 **Git Data API 构造提交**（零 git 二进制，blobs→tree(base_tree)→commit(parents)→ref），见 [[github-git-data-api-push-without-git-transport]]；推送成功但开 PR 撞 `403 Resource not accessible by personal access token` 是 PAT 缺 `pull requests: write`，见 [[github-fine-grained-pat-pr-write-403]]。

**How to apply**：GitHub 相关下载/推送失败先判断方向再选本节招式；相关：[[zcode-platform-verified-facts]]、[[cnb-npc-dispatch-essentials]]。

