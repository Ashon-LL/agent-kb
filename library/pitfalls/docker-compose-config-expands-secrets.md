---
name: docker-compose-config-expands-secrets
description: `docker compose config` 会把 env_file 全量展开成明文打印（含 token/key）——在含密钥的 compose 上用它做校验=把真值打进终端/日志/转录；改用 -q 或只 grep ports/networks
type: pitfall
source: APIShow Trae relay 升级（2026-10-06 实测；验证 compose 端口/网络时误打印 TRAE_TOKEN/RELAY_API_KEYS）
date: 2026-10-06
verified: 2026-10-06
topic: methodology
---

# `docker compose config` 会打印全部 env 真值（含密钥）

## 事故

2026-10-06 升级 Trae relay（/opt/trae2api-cn）时，改完 `docker-compose.yml` 后用
`docker compose config` 校验「端口绑定 + 网络」是否正确。该命令**把 env_file（.env）
的全部键值展开成明文**打进 stdout，包括 `TRAE_TOKEN`、`TRAE_REFRESH_TOKEN`、
`RELAY_API_KEYS` 等真值 → 直接进入终端与自动化转录。**违反「不得打印任何真实密钥」铁律**，
属自己制造的一类泄漏（同一 compose 里 env 常混着上游登录态 token 与网关 api_key）。

## 教训

- 在**任何含密钥的 compose 项目**上，**禁止全量输出 `docker compose config`**。
- 需要校验时用：
  - `docker compose config -q`（只做解析，静默；非零退出即配置有错）——首选；
  - 或只取需要的片段：`docker compose config | grep -E "ports:|host_ip|published|networks:"`
    （⚠ 仍有风险：grep 不匹配的行不会打印，但管道若被整体 `cat`/日志捕获仍可能含 env 行；
    更稳妥是 `-q` + 用别的手段确认端口，如 `ss -tlnp` / `docker inspect`）。
- 校验「端口是否绑内网」的**权威真值**其实是 `ss -tlnp` 与 `docker inspect <c> --format '{{json .NetworkSettings.Ports}}'`，
  不必依赖 `config` 的展开。
- 迁移经验：凡「为了看 A 而运行会顺带打印 B」的命令，先问「B 里有没有敏感信息」。

## 通用形态

「校验/预览类命令顺带 dump 全量配置」是反复出现的一类泄漏：`docker compose config`、
`kubectl get ... -o yaml`（含 Secret）、`terraform show`、`env`/`printenv` 等。
用最小化/静默/过滤输出，或改用不接触敏感值的旁证命令。
