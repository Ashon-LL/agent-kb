---
name: cnb-workspace-agent-direct-channel
description: CNB 云开发工作区里 CodeBuddy 的 REST API/CLI 直连通道（SSH+8688，必带 x-codebuddy-request:1）；⭐CLI 打通=继承 serve 进程注入环境（含 CNB_TOKEN 本库令牌，~7 天过期）；⭐保活硬门槛=「进页面」（创建后 10 分钟内未进 VS Code 页面即回收，SSH 不算）；+ 关闭取证字段（backup_status/commit_count；file_count 非未提交口径；平台全量日志不含对话）
type: tool
source: mh-agent-open
date: 2026-10-03
verified: 2026-10-16
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

## 配套：容器保活（⛔ 2026-10-16 更正：硬门槛是「进页面」，SSH 不算数）

官方原文（`docs.cnb.cool/zh/workspaces/workspace-recycling.md`）：
- 「环境创建后 **10 分钟内未进入 VS Code 页面**」⇒ 回收；
- 「打开页面后关闭，超过 10 分钟无操作」⇒ 回收；
- 「最大保持时间：默认 **18 小时**，持续心跳可维持」；过夜规则=「使用超过 8 小时 **且** 处于凌晨 4–6 点」**两条件同时成立**才强制回收。

⭐ **2026-10-16 实测三例（推翻本文件旧结论「SSH 即心跳」）**：两个环境 SSH 心跳每 2 分钟一次、次次成功，仍在 **+10.4 / +10.9 分钟**被回收（只与「无人进页面」吻合）；第三个在 ~6 分钟处用 IAB 打开 `<sn>.cnb.space` 页面后，随即越过 +11 分钟仍存活。
⇒ **铁律：`start-workspace` 后第一件事 = 10 分钟内打开它的 VS Code 页面**（IAB 可行，2026-10-16 实测能渲染；或请用户在真浏览器开），**并保持页面开着**；SSH 心跳只当补充，⛔ 不能顶替「进页面」。
⇒ 判「探针被拒」先查工作区状态：SSH 回 `Received disconnect … port 22:11` / `get-workspace-detail` 404 = 工作区已回收（不是密钥坏、不是限流）。

⚠️ 别把它和 Job 级 `timeout`（默认 2 小时 / 最大 12 小时 / 无输出 10 分钟）混了：
那是**构建流水线**（NPC 那种）的口径，与云开发工作区无关。

（留档：2026-10-12 曾实测「纯 `git fetch` 轮询 ~12 分钟无 SSH 被回收」——当时的「SSH 即心跳」归因已被 2026-10-16 三例更正。）

### 关闭取证（2026-10-12 实测：判"有没有东西丢了"看这几项）

- **关闭备份自述**（git-backup 日志）：「未push提交 N / 修改文件 N / 总修改行数 N / 未跟踪 N」——`未push提交=0 且 总修改行数=0` ⇒ 零丢失的**直接口径**；未跟踪小文件会打进关闭备份（bundle 上传云端）。
- **workspace API 字段**：`backup_status`（1=关闭备份成功）、`commit_count`/`remote_stash_count`（未推送提交 / stash 数，判"全落远端了吗"）、`latest_sha`（最后所在分支的远端提交，拿它去核该提交是否已合入主线）。
- ⚠ **`file_count`/`file_list` 是"工作区累计变更展示字段"**（按字典序取前 5 个、随活动增长），**不是"未提交"口径**——别读成"有 N 个文件没提交"。
- **平台"下载全量日志"= 工作区管理日志**（git-save-meta 心跳 + 启停/备份编排），**不含 Agent 对话内容**；`cnb workspace` 只有 start/stop/delete/list/detail 5 命令、**无日志下载**（工作区日志只能平台 UI 下载；构建侧日志才走 `cnb build`）。
- **对话历史唯一落点=容器内**（~/.codebuddy），随容器销毁 ⇒ 关闭后**不可追**；重启（`start-workspace`）会重建容器 + **自动恢复最近备份**（启动日志可见"下载备份→恢复完成"，≠"全毁"），但恢复不了对话、且烧核时。
- 关闭**触发者**可能不被任何日志记录——别把"时间与某某操作吻合"写成实锤归因（未知档就写未知档）。

---

## ⭐ 2026-10-16：CLI 打通（不用面板也能跑，模型/思考等级可控）

**问题**：SSH shell 里直接跑 `codebuddy -p ...` 报 `Authentication required. Please use /login command`。
**根因**：SSH shell 的 env 不是注入层；平台把凭据注入在 **`codebuddy --serve` 进程**的环境里（`CNB_TOKEN`=本库令牌 27 字符 + `CNB_TOKEN_USER_NAME` + `CODEBUDDY_GATEWAY_AUTH` 等；⚠️ 只列名，不打印值）。
**解法**：读 serve 进程的 `/proc/<pid>/environ`，用这份环境 spawn CLI —— 实测 `rc=0`、真回话；模型/思考等级/权限全可控；`--session-id`/`-c`/`-r` 可多轮；`nohup` 后长跑（本例用它把 6 小时级实验任务书直投给云环境执行者）。

```python
# 在容器内跑；先 pid=$(pgrep -f "codebuddy --serve" | head -1)
env = {}
for item in open(f"/proc/{pid}/environ", "rb").read().split(b"\x00"):
    if b"=" in item:
        k, v = item.split(b"=", 1)
        env[k.decode()] = v.decode()
subprocess.run(["codebuddy", "-p", "--session-id", "task-x",
                "--model", "deepseek-v4.1-flash", "--effort", "max",
                "--permission-mode", "bypassPermissions"],
               env=env, input=open("taskbook.txt", encoding="utf-8").read(),
               text=True, stdout=open("out.txt", "w", encoding="utf-8"),
               stderr=subprocess.STDOUT)
```

- ⚠️ **`CNB_TOKEN` 可能 ~7 天过期**（用户 2026-10-16 提示）：过期时 CLI/相关服务会再报 auth 类错误 ⇒ **正解=提示用户登录刷新**（⛔ 不要自己乱找/换凭据）。⛔ **不建定时提醒**（用户 2026-10-16 明确：过期日不可知——"已经忘了是哪天登录打上的"）⇒ 改为**报错驱动**：哪次报 auth 类错误，就在那一次提示刷新。
- ⚠️ 与面板路径的关系：cbc 的 `reply` 只投「live」（面板当前打开的）会话；CLI 自建会话不被 reply（409 `SESSION_FOLLOW_NOT_LIVE`），用 `-r <session-id>` 自己续。**两条路各管各的**。

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
  `branch` 与 `ref`**。
  ⛔ 旧结论（2026-10-03~15）「CLI `-p` 非交互必报 Authentication required、网页登录态不共享给 CLI」**已被推翻**（2026-10-16，见下节「CLI 打通」）：继承 serve 进程的注入环境即可，`--model`/`--effort`/`--session-id` 全可控。
- ⭐ **面板四项设置的实操方法（2026-10-15 用户口授，IAB 里实测有效）**：
  模式与权限的菜单**要滚动到下面**才看得到目标项（创造模式 / 完全访问都在列表尾部）；
  模型菜单可直接选。用户给的捷径原文：**「先点击 high，然后它会出现 MAX，然后点击 MAX 就可以了」**
  （即思考等级选 high → 展开出 max 档 → 点 max；⛔ 不是 "Hi"）。
  ⚠️ IAB（ZCode 内嵌浏览器）对这些浮层菜单的坐标点击**常打不中**（`aria-expanded` 恒 false、
  `menuitemradio` 取不到）——点不动时**不要反复重试**，把要点告诉用户让他点，或说明原因。
- **默认模型**：用户不在面板里选时，新会话默认 **`Hy4 preview`**（每次新对话都要重选；
  面板设置只对当前会话生效，⛔ 模型不随工作区/仓库持久化——模式与权限在用户级
  `~/.codebuddy/settings.json`（`default: create` / `defaultMode: fullAccess`）里，
  由平台账号侧漫游；插件在仓库级 `/workspace/.codebuddy/settings.json`（`enabledPlugins`，
  ⛔ 必须提交进 git 否则环境重建即丢））。
- **Dockerfile 构建期没有 git 凭据**（凭据只在运行期注入，`[git-credential]: hit self by env`）
  ⇒ 想在镜像里 clone 仓库装依赖必失败；未认证的 raw/blob URL 对私有仓库一律 404。
  仓库依赖只能在运行期装（见 `scripts/dev_env_setup.sh`）。
- **`.ide/Dockerfile` 的构建上下文不是仓库根** ⇒ `COPY backend/requirements.txt` 会让
  Prepare 直接 error、工作区起不来。
- **个人环境变量**（`https://cnb.cool/profile/workspaces`）可按用户给多个仓库注入密钥
  （`imports` + `use_in_slugs`），注入顺序晚于仓库 `.cnb.yml` 的 `imports`，同名后者覆盖。
