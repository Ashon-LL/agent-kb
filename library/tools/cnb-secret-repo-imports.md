---
name: cnb-secret-repo-imports
description: CNB 密钥库（secret repo）只能网页编辑、拒绝一切令牌访问；`.cnb.yml` 的 imports 引用形态与「顶层键必须是分支名」的静默忽略坑；Prepare 秒失败无日志时的唯一取证手法
type: tool
source: MH-Agent-Open 项目（apigogo/mh-agent-open）
date: 2026-09-18
verified: 2026-09-18
topic: cnb, security
---

**经验**：CNB 密钥库引用环境变量的完整可用姿势 + 三个会让人白跑一轮的坑。

## 1. 密钥库拒绝一切令牌访问（硬边界，不是配置问题）

```
GET https://api.cnb.cool/<org>/<secret-repo>
→ {"errcode":7,"errmsg":"Secret repos do not support token access."}

GET https://api.cnb.cool/<org>/<secret-repo>/-/git/trees/main
→ {"errcode":5,"errmsg":"Resource not found."}
```

⇒ **API / CLI / Git 全部无法读写密钥库内容**，只能网页端编辑（官方：禁止 Git Clone、禁止本地推送）。
⇒ **别接受"帮我把它写进密钥库"这类委托**：技术上做不到，只能把文件内容给用户、由用户在网页粘。
⇒ 相应地，**用户为此专门生成的令牌是多余的**，提醒其吊销；日常派单/查构建用 `~/.cnb/token`（`client_id=cnb_cli`）即可。

## 2. `.cnb.yml` 顶层键 = 分支名，写错则**静默忽略**

`[实测]` 四组对照（同一份内容，只改键名/位置）：

| 写法 | 结果 |
|---|---|
| 独立文件 `xxx.cnb.yml`（不在 `.cnb.yml` 内） | ❌ 平台根本不读该文件 |
| 顶层键 `verify-secret-imports:`（非分支名） | ❌ **静默忽略**：无报错、pipeline 数不变 |
| 挂在 `feat.push` 下的 **list 项**（`- docker: …`，与具名键并列） | ❌ Prepare 立即 error（结构非法） |
| 挂在 `feat.push` 下的 **具名 job 键** | ✅ 生效 |

- 铁律一：顶层键必须是**分支名或事件名**。
- 铁律二：同一 `push` 下**要么全 list、要么全具名键**，不可混用。
- ⚠ 最危险的是"静默忽略"——改了配置以为生效了，实际平台当没看见。**每次改完必须验 pipeline 数量变化**。

## 3. `imports` 正确形态

job 级（与 `docker` 平级）与 pipeline 级（与 `stages` 平级）**都可用**，值可为字符串或列表：

```yaml
feat:
  push:
    my-job:
      docker:
        image: cnbus/base:latest
      imports: https://cnb.cool/<org>/<secret-repo>/-/blob/main/envs.yml
      stages:
        - name: probe
          script: echo "LEN=${#MY_KEY}"    # ⛔ 只打印长度，绝不打印值
```

密钥文件是扁平 YAML `KEY: value`，键自动注入为环境变量；与 `env` 冲突时 **`env` 优先**。

## 4. 报错取证：Prepare 秒失败且无日志时怎么办

症状：pipeline `Prepare` 阶段 **几十毫秒即 error**，`build-runner-download-log` 返回
`404 日志文件不存在…（如 prepare 阶段失败）`。

⇒ **唯一取证路径**（`get-build-stage` 需三个参数）：

```bash
cnb build get-build-stage --repo <slug> --sn <sn> --pipelineId <sn>-001 --stageId prepare
```

拿 `data.content`（含 `trace` / `pipeline imports` / 错误原文）与 `data.error`。

本次实测拿到：

```
pipeline imports: ["https://cnb.cool/apigogo/secret/-/blob/main/envs.yml"]
Pipeline init error: GetFileContent: not found
```

**读法**：`GetFileContent: not found` 是**文件不存在**，不是权限类错误
⇒ ① 密钥库里还没这个文件；② 报错既然不是权限类，说明**触发身份已通过引用校验**。

## 5. 权限：默认无需 `allow_*`

官方口径：默认只有密钥仓库的**管理员 / 负责人**成员触发的流水线才有权引用。
⇒ 自己是以负责人身份派单/推送的，**不必配 `allow_*`**。

⚠ 官方警告：「一旦配置了 `allow_*` 规则，系统将**忽略触发者的角色权限**，完全依据规则校验」。
⇒ 配了 = 从"看身份"切成"看规则"，**可能收窄也可能放宽**。无明确需求不配。

## 6. 防凭据进日志

`imports` 注入的变量会进 CI shell 环境。任务书/脚本必须写死：
**只允许 `env | grep -i <关键词>` 列变量名，禁止 `echo $VAR`**（构建日志对仓库成员可见）。

**How to apply**：接 CNB 密钥库时按 1→2→3 顺序确认硬边界与写法；配置改完必验 pipeline 数量；
`Prepare` 秒失败先走 §4 取证，不要凭猜疑权限。

## 7. ⛔ 两个必须知道的落地坑（2026-09-18 实测补齐）

### 7.1 NPC 基础镜像没有 `python`，只有 `python3`

`cnbcool/default-npc:latest` 是 Debian 系，实测 `python3` = **Python 3.11.2**，
而 **`python` 不存在**。在 `script:` 里写 `python xxx.py` 会直接：

```
sh: 1: python: not found
Finished, code: 127
```

⇒ 别按本地 Windows 环境硬编码 `python`。稳妥写法（`command -v` 逐个探测）：

```yaml
- name: my-step
  script: |
    set -e
    PY=""
    for c in python3 python python3.13 python3.12 python3.11; do
      if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
    done
    if [ -z "$PY" ]; then echo "FATAL: 无 python 解释器"; exit 1; fi
    echo "使用解释器: $PY ($($PY --version 2>&1))"
    "$PY" scripts/xxx.py
```

⛔ **不要用 `python3 xxx.py || python xxx.py`**：每个失败的解释器都会往日志
喷一句 `not found`，排障时噪音很大。

### 7.2 `Prepare` success 不等于「凭据已注入」

排查时容易犯的错：看到 `Prepare` 阶段 success，就断言「密钥库引用生效了」。

**这是越界结论。** `Prepare` 过只证明**引用未被拒绝**（不是权限问题、文件路径可解析），
**不能证明变量真的注入了** —— 变量是否到位，要看**终点可观测物**：

```bash
env | grep -i -E '^(prefix1|prefix2)_' | cut -d= -f1 | sort   # 只列变量名
env | grep -c -i -E '^prefix1_'                                # 计数佐证
```

判据对照：

| 现象 | 含义 |
|---|---|
| `Prepare` 33ms error + `GetFileContent: not found` | 密钥库里没这个文件 |
| `Prepare` success，但 `env \| grep` 一个变量都没有 | 引用被接受但**注入未发生**（层级/写法问题） |
| `Prepare` success + 变量名单齐全 | ✅ 真正打通 |

⇒ **验证任何「链路是否通」的问题，都要盯终点可观测物，不要拿中间态 success 当结论。**

### 7.3 完整可用的 `.cnb.yml` 骨架（实测通过）

```yaml
feat:
  api_trigger_npc:
    - docker:
        image: cnbcool/default-npc:latest
      sandbox: false                     # ⛔ 必须 false，否则 NPC 推不了分支
      imports: https://cnb.cool/<org>/<secret-repo>/-/blob/main/envs.yml
      stages:
        - name: bootstrap-settings-from-env   # 先跑 env→settings 翻译层
          script: |
            set -e
            PY=""
            for c in python3 python; do
              command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
            done
            "$PY" scripts/bootstrap_settings_from_env.py
        - name: npc go
          type: npc:go
          options: { ... }
```

⚠ **注意**：`imports` 注入的变量是给**运行时 shell** 的，不会自动被应用读取。
若目标应用（如本项目 harness）**不读环境变量、只读自己的 DB/settings 表**，
则**必须**在中间插一个「env → 应用配置」的翻译步骤，否则变量注了也白注，
且应用只会报一个和凭据无关的错（本项目表现为 `No route-compatible
authentication source`，而 build 是绿的 —— 典型假 success）。

