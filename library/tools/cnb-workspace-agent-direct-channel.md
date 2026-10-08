---
name: cnb-workspace-agent-direct-channel
description: CNB 云开发工作区里 CodeBuddy 的 REST API 直连通道（SSH+8688，必带 x-codebuddy-request:1）
type: tool
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-03
topic: cnb
---

# 直连云环境里的 AI Agent（不经人工转述）

**场景**：CNB 云原生开发工作区（`cnb workspace start-workspace`）里跑着 CodeBuddy。
你想给那个 Agent 派活、读它的进度，但**不想当传声筒**（人工复制粘贴会漏、会走样）。

**结论：可以。** CNB OpenAPI 里**没有**这个接口（199 个端点全查过，`workspace/*`
只有 start/stop/delete/list/detail），但 Agent 自己的 REST API 就在容器里。

---

## 三步

### 1. 拿 SSH 地址（免密直连）
```bash
cnb workspace get-workspace-detail --repo <org>/<repo> --sn <sn>   # → data.remoteSsh
ssh -o StrictHostKeyChecking=no -o BatchMode=yes <remoteSsh> "echo ok"   # 免密
```

### 2. 找到 Agent 的服务端口
容器里 `codebuddy --serve` 监听 `0.0.0.0:8688`（版本不同端口可能变，
先 `ps aux | grep codebuddy` 或 `ss -ltnp` 确认）。
顺带：官方要求 CodeBuddy Code **≥ 2.137.0**，否则网页不显示该入口。

### 3. 调它的 REST API（⛔ 必须带头）
| 用途 | 方法与路径 | body / 说明 |
|---|---|---|
| 投递消息 | `POST /api/v1/sessions/{id}/reply` | `{"text":"..."}`；**不占用 ACP writer**，Agent 正忙时也能投 |
| 读每轮对话 | `GET /api/v1/sessions/{id}/history?limit=N` | 返回 `requests[]`，每项含 `userInput` / `finalReply` |
| 取活跃会话 | `GET /api/v1/sessions/live` | `{sessionId, writerOccupied}` |
| 列全部会话 | `GET /api/v1/sessions` | 含 `messageCount` / 会话名 |

⛔ **`x-codebuddy-request: 1` 缺了全站 403**（极具误导性：看起来像"没登录/无权限"）。

```bash
# 实测可用
curl -s -X POST -H 'x-codebuddy-request: 1' -H 'content-type: application/json' \
  -d '{"text":"收到请回一句：探针收到"}' \
  http://127.0.0.1:8688/api/v1/sessions/<SID>/reply
# → {"data":{"delivered":true}}
```

---

## 配套：容器保活（这条顺带解决了一个老大难）

官方机制：`vscode` 流水线有 **`keepAliveTimeout`**（默认 **600000 ms = 10 分钟**），
超时且**无 HTTP/SSH 心跳**就回收开发环境。

⇒ **只要你保持 SSH 连接（或偶尔发一次），环境就不会被回收。**
这解释了"容器开着 12~93 分钟就没了"这类现象——不是平台限时长，是**无心跳被判死**。

⚠️ 别把它和 Job 级 `timeout`（默认 2 小时 / 最大 12 小时 / 无输出 10 分钟）混了：
那是**构建流水线**（NPC 那种）的口径，与云开发工作区无关。

---

## 现成脚本（Python 版，跨平台，KB 内置）

`~/.agents/kb/tools/cnb-workspace-agent-cli.py`（与 `github-push-ip-retry.py` 同款形态）：

```bash
python cnb-workspace-agent-cli.py reply "<文本>"   # 派活
python cnb-workspace-agent-cli.py history 6         # 读最近 6 轮
python cnb-workspace-agent-cli.py sessions          # 列会话
python cnb-workspace-agent-cli.py keepalive         # 心跳
python cnb-workspace-agent-cli.py watch 240         # 持续盯：定期心跳 + 只打印新发言
#                                  # ⛔ 必须在自己可见的窗口跑；挂后台/会话结束会哑（实测踩过：日志只写了启动行）
```

环境变量 `CNB_WS_SSH`（工作区 SSH 地址，随工作区重建会变，用前最好更新）、
`CNB_WS_BASE`（默认 `http://127.0.0.1:8688`）。

### shell 版（历史留档）
`mh-agent-open` 仓库的 `scripts/cbc.sh` 早于本脚本，行为一致（`reply`/`history`/`sessions`/`keepalive`），
可继续用；新脚本多一个 `watch` 且跨平台。

`mh-agent-open` 仓库已内置 `scripts/cbc.sh`（可直接抄走）：

```bash
bash scripts/cbc.sh reply "<文本>"     # 派活
bash scripts/cbc.sh history 6          # 看最近 6 轮输入/输出
bash scripts/cbc.sh sessions           # 列会话
bash scripts/cbc.sh keepalive          # 发一次心跳
```
环境变量 `CNB_WS_SSH`（工作区 SSH 地址）、`CNB_WS_BASE`（默认 `http://127.0.0.1:8688`）。

实现要点：**"文本→JSON"放在远端做**（本机 PowerShell/Git Bash 的引号转义不可靠），
用 `ssh host "bash -s" <<< "$script"` 传脚本。

---

## 相邻事实（同一批调研得出，别重复查）

- **工作区 start 无法指定模型/思考等级**：`dto.StartWorkspaceReq` 的 body **只有
  `branch` 与 `ref`**。要换模型只能在 CodeBuddy 会话界面里选
  （CLI 支持 `--model space-bunny --effort max`，但 `-p` 非交互模式需要登录态，
  **网页端登录态不共享给 CLI** ⇒ 容器内 `codebuddy -p` 会报 "Authentication required"）。
- **Dockerfile 构建期没有 git 凭据**（凭据只在运行期注入，`[git-credential]: hit self by env`）
  ⇒ 想在镜像里 clone 仓库装依赖必失败；未认证的 raw/blob URL 对私有仓库一律 404。
  仓库依赖只能在运行期装（见 `scripts/dev_env_setup.sh`）。
- **`.ide/Dockerfile` 的构建上下文不是仓库根** ⇒ `COPY backend/requirements.txt` 会让
  Prepare 直接 error、工作区起不来。
- **个人环境变量**（`https://cnb.cool/profile/workspaces`）可按用户给多个仓库注入密钥
  （`imports` + `use_in_slugs`），注入顺序晚于仓库 `.cnb.yml` 的 `imports`，同名后者覆盖。
