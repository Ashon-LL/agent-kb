---
name: cnb-quota-runner-cli-notes
description: CNB 配额与 Runner 要点：云原生构建 160 核时/月、云原生开发 1600 核时/月独立不共享（超额 ¥0.125/核时）；**本账号实况：派 NPC/push/合并都吃构建额度，官方免费额度数字不作数**（用户 20260930 纠正，优先于官方文档）；省配额三招及代价；自托管 Runner 不开 Docker、不计核时、仅构建；CLI 新坑（start 缺 title 报 401、Windows 用 cnb.cmd、patch-pull 关闭不合并、list-pulls 无 --number）；「请了裁 ≠ 免责」
type: tool
source: CNB 官方文档核对 + 2026-09-23 实测 + 用户 2026-09-30 账号实况纠正
date: 2026-09-23
verified: 2026-09-23
topic: cnb, delivery
---

**经验**：CNB 配额、自托管 Runner、CLI 三类易错点的速查。

## 两种 CPU 配额独立不共享（官文档核得）

- 「云原生构建」CPU **160 核时/月**（push/PR/API 触发流水线）；
- 「云原生开发」CPU **1600 核时/月**（网页 IDE）。

均 ¥0.125/核时超额、月底清零。公式 =「自然月累积 − 免费额度」；**核时 = 核数 × 小时**
（官方节点默认 8 核）。CLI：`cnb charge get-quota / get-volume / get-repos-volume --slug <org>`。

## 本账号实况（2026-09-30 用户亲口纠正，优先级高于官方文档）

- **派 NPC 吃的是「构建额度」，不是开发额度**：`api_trigger_npc` / 评论 `@npc`、push、合并 PR、
  任何 CI 流水线都计**云原生构建-CPU**；只有手动在网页云原生开发工作区写代码才计开发额度。
  ⛔ 与官方 `npc.md`「NPC 归入开发场景，消耗云原生开发用量」**直接冲突**——以本账号实况为准
  （日志里流水线运行位置在「云原生构建」标签下）。
- **官方 pricing 的免费额度数字（160 / 1600 核时）不作数**，以账号实际账单/用量为准。
- **推论**：「不派单」不是省额度方案（派单与推送省不掉），能省的只有 PR 触发的**额外那条**
  `pull_request` CI。

> ⏰ 时效状态（2026-09-30 记录，未复核）：以上为本账号当时实况；官方文案/账号档位变化后需重测，
> 复核命令：`cnb charge get-quota --slug <org>` 与一次派单前后用量对比。

## 省配额三招

1. **不开 PR**（实测推非 feat 分支 `push` 事件 = 0，顶层键只有 feat；开 PR 则每次 push 都重跑全门禁 = 大头）
2. **`[ci skip]` / `[skip ci]` in commit msg 或 `git push -o ci.skip`**
   ⚠ 仅对 `push` / `commit.add` / `branch.create` 生效，**对 `pull_request` 无效**
3. 本地跑门禁（pytest + cargo check + npm run build）——不花 CNB 配额

⛔ 省配额的代价 = 丢服务端 CI 保险 ⇒ 本地门禁**必须含 cargo check**
（跨平台编译错误只有 Linux 的 rust job 抓得到）。
⛔ **不许**把 `api_trigger_npc` 搬去别的顶层键省构建：顶层键和分支名是同一件事。

## 自托管 Runner（Windows/Mac 打包 + 免核时）

根组织管理员在「组织设置 / 构建节点」接入自己的 Win/Mac/Linux 机；
流水线用 `runner.namespace: group` + `runner.tags: [windows,...]` 调度。

⚠ 宿主机直跑、**默认不开启 Docker** ⇒ `pipeline.docker.image` 不生效 / `runner.cpus` 无效 /
OverlayFS 不可用；⭐ **不参与核时计费**；⚠ **仅限云原生构建**，不支持云原生开发；
Linux 自托管仅 arm64。⇒ 「容器无 cargo / 无 Windows ⇒ 跨平台验不了」的正解。

## CLI 新坑（全部实测）

- **`build/start` 缺 `title` → 返回 `401 Unauthorized`**（极误导，不是 token 问题）；
  真实原因在 400 body：`[API_BUILD_START_FAIL]Event must be 'api_trigger' or start with 'api_trigger_'`
  ⇒ 见 401 先用只读端点（如 `/user/repos`）验 token 再怀疑别的
- Windows 上 **Python subprocess 调 `cnb` 必须用 `cnb.cmd`**
  （裸名是 sh 包装，CreateProcess 不做 PATHEXT 解析 ⇒ FileNotFoundError）
- **要「关闭但不合并」PR 用 `patch-pull --state closed`**，别用 `merge-pull`（会真合并）
- `cnb pulls` 无 `create-pull`（用 `post-pull`）；`list-pulls` 无 `--number`；状态无 `merged`（看 `is_merged`）
- 读构建日志：输出是 YAML-ish + ANSI 转义 + 超大 flow-list ⇒ 先剥 `\x1b\[[0-9;]*m` 再抽 `"..."`
- 大任务书（>32KB）别走 CLI argv（Windows 截断），直投 OpenAPI + `ensure_ascii=True`

## 「请了裁 ≠ 免责」

NPC 主动指出冲突并请裁决是好事；但**裁决给了却不执行** ≠ 完成。
派发方验收必须逐条对照裁决项 —— NPC 报告里写「我论证过应做 X」而代码里没 X，
是最隐蔽的半成品形态。

## 读官方文档技巧

索引 `https://docs.cnb.cool/zh/llms.txt`；**每篇把 `.html` 换成 `.md` 直接 curl**，干净且省 token。

**How to apply**：设计流水线先算配额账（PR 是最大头）；Windows 上跑 CLI 一律 `cnb.cmd`；
验收 NPC 交付逐条对照裁决项，不看报告自述。

关联 [[cnb-npc-dispatch-essentials]]、[[cnb-pipeline-2h-hard-cap]]、
[[cnb-cli-needs-cmd-suffix-when-spawned-from-python]]。
