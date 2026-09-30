# agent-kb 的云原生开发环境
#
# 基线必须用官方默认镜像，不要换成 debian / ubuntu / node —— 它已经带齐：
#   git / git-lfs / jq / rsync / curl / vim / wget / unzip / openssh-server / zsh / oh-my-zsh
#   code-server 及插件（coding-copilot、vscode-yaml、git-graph、markdown-mermaid 等）
#   并且已把 LANG / LC_ALL 设为 zh_CN.UTF-8
#   （本仓库 110 条条目全是中文，换基镜像就得自己重建中文环境，不划算）
#
# 它缺的只有一样：python3。
# 没有它，任务书 C1 的验收命令会以 command not found 静默失效 —— 唯一防线空转。
FROM cnbcool/default-dev-env:latest

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/*

# 自检：版本写进构建日志，装错了当场看得见
RUN python3 -V
