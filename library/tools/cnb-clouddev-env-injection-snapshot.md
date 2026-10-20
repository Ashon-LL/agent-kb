---
name: cnb-clouddev-env-injection-snapshot
description: 云开发环境（非 NPC 构建）的凭据消费链路：注入层是容器主进程 env 不是 ssh 登录 shell（读 /proc/<pid>/environ，且别 head 截断）；bootstrap 必须在带注入 env 的进程里跑；settings 是 bootstrap 那一刻的密钥库快照（改库不回流，看 *_base_url 的 updated_at 同秒批量即知）；跨套错配 401 不能推定 key 无效；Prepare success ≠ 变量已注入
type: tool
source: MH-Agent-Open 云原生开发环境（2026-10-14 实测补齐）
date: 2026-10-14
verified: 2026-10-14
topic: cnb, security
---

**经验**：CNB 云原生开发环境里的密钥注入与「环境实际用什么上游」是两件事，核对姿势与 NPC 构建容器不同。

## 1. 注入层 = 容器**主进程** env，不是 ssh 登录 shell 的 env

`ssh <workspace>@cnb.space 'env'` 只有 **13 个变量**（ssh 会话最小环境），密钥库键一个都没有。
真正带注入的是 pid 1 / `codebuddy --serve` 等主进程 ⇒ 核对密钥库内容要读：

```bash
tr '\0' '\n' < /proc/<pid>/environ | cut -d= -f1 | sort   # 只列键名
```

⛔ **列键名不要 `head` 截断**：实测 `| grep ... | head -20` 把 `reviewer_api_key` 截掉，
据此误判「密钥库没配该键」。**不完整观测不能下结论。**

## 2. `bootstrap_settings_from_env.py` 必须在「带注入 env 的进程」里跑

该脚本读**自身进程**的 env ⇒ 在 ssh 里直跑必然
`[bootstrap] 未从环境变量拿到任何白名单键。`（rc=1）。
正确跑法（读主进程 env 重建后传入）：

```python
raw = open("/proc/85/environ", "rb").read().decode("utf-8", "replace")
d = dict(kv.split("=", 1) for kv in raw.split("\0") if "=" in kv)
subprocess.run([sys.executable, "scripts/bootstrap_settings_from_env.py"], env={**os.environ, **d})
```

跑完**逐键验证 `env == settings`** + 冒烟一次真实上游调用（HTTP 200 才算通）。

## 3. 环境 settings 是「bootstrap 那一刻的密钥库快照」

实测溯源（2026-10-14）：某云环境 settings 全套指向 `token.sensenova.cn`，而当前密钥库里只有 TDP 配置。
查 `settings.updated_at`：所有 base_url 键写于**同一秒**（`2026-10-03 18:42:22`），
**2 分钟后**建了第一条工作流 ⇒ 典型「环境初始化跑 bootstrap」形态；云端库 `model_presets` 为 0 条
（纯程序写入痕迹），本机库只有一条 TDP 预设 ⇒ 排除手工配置与本地 DB 带入。

⇒ **机制**：bootstrap 只在建环境那一刻跑一次，把当时的密钥库版本写进 settings；
此后**密钥库怎么改都不会回流**，直到下一次 bootstrap。环境用的上游与密钥库现状可以长期不一致，
且**没有任何告警**。

**排查姿势**：
1. 看各 `*_base_url` 的 `updated_at`——**同一秒批量** ⇒ 来自 bootstrap；逐项不同时间 ⇒ 有人手工改过；
2. 与**当前**密钥库（容器主进程 env）逐键比对；不一致即「停在旧快照」；
3. 修正 = 备份 db → 按 §2 跑 bootstrap → 逐键验证。只对齐上游角色可只改
   `executor_*` / `reviewer_*` 8 键，避免把容器行为参数（看门狗/电源/音效/并发）覆盖到本机偏好。

## 4. 跨套错配导致的 401 **不能推定「key 无效」**

实测形态：settings 里 reviewer 的 base/model 来自 A 套（本地 DB），key 来自 B 套（另一通道遗留）
⇒ 打 A 端点必 `401 Forbidden`。⛔ 断言「这把 key 是坏的」是越界结论——
把它放回**自己的端点**实测往往 200（本例 42 字符 key 在 `ai.tdp.fan` 上 200、在 sensenova 上 401）。
⇒ 否证式结论先做「回到正确条件的最小实测探针」。

## 5. `Prepare` success ≠ 变量已注入

`Prepare` 过只证明**引用未被拒绝**（不是权限问题、文件路径可解析），不能证明变量真的注入了。
变量是否到位看**终点可观测物**：

```bash
env | grep -i -E '^(prefix1|prefix2)_' | cut -d= -f1 | sort   # 只列变量名
env | grep -c -i -E '^prefix1_'                                # 计数佐证
```

| 现象 | 含义 |
|---|---|
| `Prepare` 33ms error + `GetFileContent: not found` | 密钥库里没这个文件 |
| `Prepare` success，但 `env \| grep` 一个变量都没有 | 引用被接受但**注入未发生**（层级/写法问题） |
| `Prepare` success + 变量名单齐全 | ✅ 真正打通 |

⇒ **验证任何「链路是否通」，盯终点可观测物，不要拿中间态 success 当结论。**

**How to apply**：在云开发环境排查凭据问题时，顺序是
「主进程 env → bootstrap 进程 → settings 快照 → 端点归属」，每步都以可观测物为准。

关联 [[cnb-secret-repo-imports]]、[[layered-service-credentials-must-match-layer]]、
[[automation-artifacts-lie-existence-and-freshness]]、[[no-assertion-without-measurement]]。
