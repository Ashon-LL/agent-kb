---
name: cnb-secret-repo-imports
description: CNB 密钥库（secret repo）只能网页编辑、拒绝一切令牌访问；`.cnb.yml` 的 imports 引用形态与「顶层键必须是分支名」的静默忽略坑；Prepare 秒失败无日志时的唯一取证手法；另含 env 分层（注入层=容器主进程非 ssh shell）/bootstrap 正确跑法/settings 被上传 DB 覆盖/跨套错配 401 的判读（2026-10-14 补）
type: tool
source: MH-Agent-Open 项目（apigogo/mh-agent-open）
date: 2026-09-18
verified: 2026-10-14
topic: cnb, security
---
<!-- hook-reviewed 2026-10-20：已人工确认 INDEX 钩子覆盖本条全部更新内容 -->


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


## 8. 2026-10-14 补齐：云开发环境的 env 分层、bootstrap 正确跑法、DB 覆盖与跨套错配

同上密钥库在**云原生开发环境**（非 NPC 构建容器）里的消费链路，四条实测新事实。

### 8.1 注入层 = 容器**主进程** env，不是 ssh 登录 shell 的 env

`ssh <workspace>@cnb.space 'env'` 只有 **13 个变量**（ssh 会话最小环境），密钥库键**一个都没有**。
真正带注入的是 pid 1 / `codebuddy --serve` 等主进程 ⇒ 核对密钥库内容要读：

```bash
tr '\0' '\n' < /proc/<pid>/environ | cut -d= -f1 | sort   # 只列键名
```

⛔ **列键名不要 `head` 截断**：实测 `| grep ... | head -20` 把 `reviewer_api_key` 截掉，
据此误判"密钥库没配该键"（与 §7.2 同族：拿不完整观测下结论）。

### 8.2 `bootstrap_settings_from_env.py` 必须在「带注入 env 的进程」里跑

该脚本读**自身进程**的 env ⇒ 在 ssh 里直跑必然 `[bootstrap] 未从环境变量拿到任何白名单键。`（rc=1）。
正确跑法（读主进程 env 重建后传入）：

```python
raw = open("/proc/85/environ", "rb").read().decode("utf-8", "replace")
d = dict(kv.split("=", 1) for kv in raw.split("\0") if "=" in kv)
subprocess.run([sys.executable, "scripts/bootstrap_settings_from_env.py"], env={**os.environ, **d})
```

跑完**逐键验证 `env == settings`** + 冒烟一次真实上游调用（HTTP 200 才算通）。

### 8.3 环境 settings 是「bootstrap 那一刻的密钥库快照」——密钥库改了不会自动同步

实测溯源（2026-10-14）：某云环境 settings 全套指向 `token.sensenova.cn`，而当前密钥库里只有 TDP 配置。
查 `settings.updated_at` 发现 **所有 base_url 键写于同一秒**（`2026-10-03 18:42:22`，executor/reviewer/editor_ai
= sensenova，vision/gpt_image = bigmodel），**2 分钟后**就建了第一条工作流 ⇒ 典型的「环境初始化跑 bootstrap」形态；
而云端库 `model_presets` 为 **0 条**（纯程序写入痕迹），本机库只有一条 TDP 预设 ⇒ 排除"手工配过"与"本地 DB 带过去"。

⇒ **机制**：`bootstrap_settings_from_env.py` 只在建环境那一刻跑一次，把**当时的密钥库版本**写进 settings；
此后**密钥库怎么改都不会回流**，直到下一次 bootstrap。所以"环境用的上游"与"密钥库现在的配置"可以长期不一致，
且**没有任何告警**。

**排查姿势**：
1. 看 `settings` 里各 `*_base_url` 的 **`updated_at`**——**同一秒批量** ⇒ 来自 bootstrap（程序），逐项不同时间 ⇒ 有人手工改过；
2. 与**当前**密钥库（容器主进程 env）逐键比对；不一致即"停在旧快照"；
3. 修正 = 备份 db → §8.2 跑 bootstrap → 逐键验证。**只对齐上游角色可只改 `executor_*` / `reviewer_*` 8 键**，
   避免把容器行为参数（看门狗 0 / 电源 / 音效 / 并发）覆盖到本机偏好。

### 8.4 跨套错配导致的 401 **不能推定为「key 无效」**

实测形态：settings 里 reviewer 的 base/model 来自 A 套（本地 DB），key 来自 B 套（另一通道遗留）
⇒ 打 A 端点必 `401 Forbidden`。⛔ 断言"这把 key 是坏的"是越界结论——
把该 key 放回**它自己的端点**实测往往 **200**（本例 42 字符 key 在 `ai.tdp.fan` 上 200、在 sensenova 上 401）。
⇒ 否证式结论先做"回到正确条件的最小实测探针"。

关联 [[git-remote-ownership-check]]。
