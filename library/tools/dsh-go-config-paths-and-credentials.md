---
name: dsh-go-config-paths-and-credentials
description: dsh-go（DSH Android 客户端，DSH 0.2.2-rc.1）配置落点与格式——provider 写 $DSH_HOME/profiles/web/cordis.patch.yml、key 写 $DSH_HOME/.credentials.yaml；profile patch 按 id 整行替换（只写自己那行）；app 数据目录 adb 不可访问（非 debuggable、无 root），只能走应用自身文件入口或 root
type: tool
source: default 会话 2026-11-08（dsh-go 1.0.13 + DSH 0.2.2-rc.1，文档+源码+proot 实测）
date: 2026-11-08
verified: 2026-11-08
topic: llm, toolchain
---

**经验**：dsh-go 把 DSH 跑在 proot 里（rootfs = `/data/user/0/io.github.ccch1mneyyy.dsh_app/files/runtime/rootfs`，env `DSH_HOME=/root/.dsh`）。要改模型渠道，落点是两个文件：

1. **provider 配置**：`/data/user/0/<pkg>/files/runtime/rootfs/root/.dsh/profiles/web/cordis.patch.yml`（`dsh web` 的 profile 固定 `web`）。格式是 Cordis patch 行，按 `id` 寻址：
   ```yaml
   - id: llm-pi-ai
     config:
       providers:
         longcat:
           apiKeyEnv: LONGCAT_API_KEY      # 凭证引用，不是明文 key
           api: openai-completions
           baseURL: https://api.longcat.chat/openai
           models:
             - id: LongCat-2.5
               contextWindow: 1000000        # 上下文；maxTokens 是最大输出，默认 128000
   ```
2. **密钥**：`/data/user/0/<pkg>/files/runtime/rootfs/root/.dsh/.credentials.yaml`：
   ```yaml
   version: 1
   refs:
     LONGCAT_API_KEY: ak_...
   records: {}
   ```
   `apiKeyEnv` 是「环境变量名」式引用，密钥本体只进 `.credentials.yaml`；`records:` 里存 OAuth 账号（如已登录的 DeepSeek 官方账号），**整体覆盖会掉登录**，只能合并 `refs`。

**关键机制**：Cordis config override **整行替换**（同 id 的 config 不合并），所以只写自己那一行（如 `llm-pi-ai`）即可，别的行不受影响；base bundle 的 `llm-pi-ai` 行是空挂载，官方 DeepSeek 走另一套适配器，不会被打掉。配置与凭证文件都是 `watch: true` 热加载，改完无需重启引擎，下次请求生效。

**Why**：dsh-go 的 app 数据目录普通 adb 进不去（`run-as` 报 not debuggable、无 su），直接改文件需要应用自身的文件入口（如网页端「打开配置文件」）或 root；而配置用 `apiKeyEnv` 引用、密钥单独放 `.credentials.yaml`，是为了密钥不进配置、可热轮换。

**How to apply**：给 dsh-go/DSH 加自定义渠道时，按上面两个文件的路径与格式写；只写 `llm-pi-ai` 一行；密钥合并进 `.credentials.yaml` 的 `refs`；改完靠热加载生效，不必重启。相关：[[dsh-llm-pi-ai-reasoning-config-traps]]、[[android-adb-ime-and-coordinate-gotchas]]。