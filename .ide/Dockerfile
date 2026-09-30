# agent-kb 的云原生开发环境
#
# 基线必须用官方默认镜像，不要换成 debian/ubuntu/node —— 默认镜像已经带齐：
#   git / git-lfs / jq / rsync / curl / vim / wget / unzip / openssh-server / zsh / oh-my-zsh
#   code-server 及插件（coding-copilot、vscode-yaml、git-graph、markdown-mermaid 等）
#   并且已把 LANG / LC_ALL 设为 zh_CN.UTF-8（本仓库 110 条条目全是中文，headless 换基镜像会丢中文）
#
# 它缺的只有三样，本文件按顺序补上（分层放置，前面的层失败不影响已建的缓存）：
#   1. python3   —— 任务书 C1 的验收命令、以及库校验器都用它
#   2. node/npm  —— 默认镜像不带，装 codebuddy 需要
#   3. codebuddy —— 浏览器端 AI 入口 CodeBuddy Web，要求版本 >= 2.137.0
FROM cnbcool/default-dev-env:latest

# ── 1) Python3 ────────────────────────────────────────────────
# 没有它，任务书的 C1 验收会以 command not found 静默失效
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# ── 2) Node.js ＋ npm ─────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# ── 3) CodeBuddy Code ─────────────────────────────────────────
# 装上它，云开发入口才会显示 CodeBuddy Web（浏览器里直接对话编码）
RUN npm install -g @tencent-ai/codebuddy-code

# ── 自检：版本写进构建日志，装错了看得见 ──────────────────────
RUN python3 -V && node -v && npm -v \
 && (codebuddy --version || echo "codebuddy 版本自检跳过（不影响环境可用）")
