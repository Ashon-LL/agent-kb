---
name: cnb-npc-dispatch-essentials
description: CNB 平台与 NPC 派单要点：payload body 三层套嵌（env.userPrompt + npc.workMode 嵌 npc 内）、三大致命要点、OAuth scope 刷新、2h 硬边界改不了
type: tool
source: ailika + mh-agent-open（2026-09-13~16 实战）+ agent-kb 派单（2026-09-20 OAuth scope 坑）；完整手册见 Downloads/Project/DeepSeek/CNB-上手指南-给其他项目.md
date: 2026-09-20
verified: 2026-09-13
topic: cnb, security
---

**经验**（cnb.cool = GitHub + CI + AI 员工 NPC；全程可脚本化，docs.cnb.cool 有 llms.txt 可批量读）：

- ⭐ **需求单开在「目标仓」，不是 NPC 注册仓（2026-10-16 用户钉 + 官方原文）**：官方 `npc.md`：「流水线跑在**当前 Issue 或 PR 所属仓库**下（不是 NPC 所属仓库）」；角色注册仓只提供人设/`.cnb.yml` 行为配置。⇒ 要改仓库 R，就把**需求单开在 R**、在 R 的 issue **评论**里 @`<注册仓>(角色)` + 工作模式（网页勾「替我上班」或 CLI `--work-mode`）。⛔ 反例（我 2026-10-15 犯过）：把 mh 的活开在 x 仓 ⇒ 流水线/编排落在 x、还要 api_trigger_npc 子单打回 mh，绕远（虽也能交付）。对照：mh issue #144（正路）vs x issue #8（绕路）。> ⏰ **时效状态（2026-10-23 实测；2026-10-16 的「已删」是误记）**：现行入口 = **`@apigogo/x(中书令)`**；该仓 2026-10-19 重建，带密钥 imports + 4 核 runner。用前必须复核：`cnb repositories get-by-id --repo apigogo/x`。
  跨根「态B 真人首棒工作模式」：首棒勾 work-mode ⇒ 整链继承写权、接力走评论嵌套 @、⛔ 禁中途切 api_trigger。
  ⚠ 评论会话的配置源 = 入口注册仓（现为 `apigogo/x`）的 `.cnb.yml`；能否注入我方密钥库取决于该仓 `.npc` 锚点是否带 `imports`，以当前配置实测为准。需要真凭据且不确定时，走本仓 `api_trigger_npc` 直派或云开发环境（两者自带 imports）。
- **双通道授权不同**：①issue/PR 上 @npc——工作模式写权限来自**网页 UI 勾「替我上班」**且只挂触发那一处；⚠️ **「正文 @ 无写权限」只适用于 API/CLI 建的 issue**（实锤三连 403）——**网页手动建的 issue，@ 写在正文里照样有写权限**（默认勾「替我上班」，未勾选需检查）。20260924 agent-jev issue#1 实锤：网页建 issue + 正文末尾 @CodeBuddy → build 事件 `issue.comment@npc`、`npc.workMode=true`，NPC 正常推分支 `auto/platform-compat-76f9` + 建 PR#2，零 403。**判据 = build 里 `npc.workMode` 是否为 true**；②`api_trigger_npc`——body `npc:{name,workMode:true}` 直授 + env 注入任务书全文，前提 .cnb.yml 默认分支配 `npc:go`；**sandbox 必须 false**，true 时 token 失效但 exit 0 = 假成功零产物。
- **⛔ 要让 NPC 真干活，issue 必须网页里发**（0916 用户钉）：API/CLI 建的 issue 三态全无用——不 @ = 单纯挂着没人动；@ 了但触发评论不在网页发 = NPC 干活了却因无写权限、PR 建不出来、成果销毁。**首选一律 `api_trigger_npc`**（自带 workMode 直授，无权限坑）；若坚持走 issue，姿势=CLI/API 只发**正文**（记录用），然后**人到网页评论区**补一条 @CodeBuddy 普通段落触发（网页发评论默认勾「替我工作」才有写权限）。
- **⛔ `workMode` 必须嵌在 `npc` 内、禁止出现在 body 顶层**（0926-09-17 实锤事故）：手写派单脚本若写成 `body:{workMode:true, npc:{name}}`，NPC 拿到的是**非工作模式 scope**→ 第一秒 `git push` 即 403 `repo-code:rw`、API 建分支 `errcode:10023 Missing required scopes`，整个单白跑 3h 推不出一个字节（旧单 `cnb-l7g` 即此）。正确格式对照 `.cnb.yml` 注释逐字：`npc:{name:"CodeBuddy",workMode:true}`。脚本自检：`assert body["npc"]["workMode"] is True` 且 `assert "workMode" not in body`（顶层出现即错）。NPC 守纪律表现：被拒后不假交付，把根因贴到 issue 求授权。
- **⛔ 派单默认用系统 NPC `@CodeBuddy`、不要传自定义 `role`**：`api_trigger_npc` 的 body 若给 `env.role` 一个非 CodeBuddy 的自定义角色名，`npc:go` 会强制去仓库 `.cnb/settings.yml` 解析该角色，文件不存在即容器启动**秒 error**（"Cannot read .cnb/settings.yml"）。系统 NPC CodeBuddy 开箱即用、根本不读 settings.yml（官方文档：自定义 NPC 才在 settings.yml 定义角色）。正解=任务书全文塞 `env.userPrompt`/`systemPrompt`、`npc:{name:"CodeBuddy",workMode:true}`、**不填 role**。0915 实锤：09-14 全部 api_trigger_npc 用 @CodeBuddy 无 role 正常交付 #25~#32；我 09-15 传了自定义 role 才 error，误判成"通道要 settings.yml"并往主库加了该文件，实为自己造病、后 revert。
- **⛔⛔ env 必须同时有 systemPrompt + userPrompt（20260921 两次秒崩后补，务必逐字照抄）**：
  ```python
  body = {
    "event": "api_trigger_npc",
    "branch": "feat",
    "title": "...",
    "npc": {"name": "CodeBuddy", "workMode": True},   # ⛔ workMode 嵌在 npc 内，禁止在 body 顶层
    "env": {
      "systemPrompt": "你是 XXX 仓库的工程化 NPC。你的职责是……（简短人设，几十字够）",   # ⛔ 必须传！
      "userPrompt": TASK_BOOK_FULL_TEXT                                                  # ⛔ 任务书全文塞这里！
    },
  }
  ```
  - ⛔⛔ **env 必须同时有 systemPrompt + userPrompt**（20260921 实锤：只传 userPrompt 会秒崩 `npc:go requires "systemPrompt" parameter for non-NPC events`，stage <2s 即挂）。原因：仓库 `.cnb.yml` 的 `npc:go` options 段**同时引用了两个变量**（`systemPrompt: $systemPrompt` 和 `userPrompt: $userPrompt`），缺哪个平台就强校验秒报哪个。**先读仓库的 `.cnb.yml`，看 `npc:go` 的 `options:` 下写了什么变量名，env 里就必须都传**。
  - ⛔ **任务书塞 env.userPrompt，人设塞 env.systemPrompt**。二者语义不同：systemPrompt=通用人设（几十字，所有派单共用同一条都可以）；userPrompt=本次任务的具体指令（承载完整任务书）。⛔ 不要把任务书塞到 options.systemPrompt（平台走 env 变量替换，不走 options）；⛔ 不要把人设写死在 .cnb.yml 的 options 里（options 里写死的字符串会覆盖 env 传入）。
  - ⛔ **不要传 env.role**：api_trigger_npc + 系统 NPC CodeBuddy 场景，role 无意义且乱传自定义名会触发 settings.yml 解析失败（1 秒内 error）。
  - ⛔ **CLI `--env userPrompt=xxx` 单次只能传一个**，要同时传两个就得拼 `--env "userPrompt=xxx" --env "systemPrompt=yyy"`——但 `--data` 方式一次性传完整 JSON body 更不易错。
  - ✅ 自检（构造 body 后必跑）：
    ```python
    assert body["npc"]["workMode"] is True
    assert "workMode" not in body                        # 禁止在 body 顶层
    assert "role" not in body["npc"] and "role" not in body["env"]
    assert body["env"]["systemPrompt"].strip()
    assert body["env"]["userPrompt"].strip()
    assert "options" not in body                          # options 层级不存在，全在 env
    ```
  - 官方依据：npc.html「通过 API 以 NPC 身份触发」+ env.html「变量替换」（$env_name→env 值）。
- **⛔ `api_trigger` 的 userPrompt 传参双通道**：除 `--data body.json`（推荐，见上），也可 `--env userPrompt=<全文>` + `--env role=<角色>`（cli 层拼入 env）。二选一即可；`--data` 更不易错（JSON 转义由 json.dumps 保证）。
- **⛔⛔ 大任务书（实测 ~32KB 起）走 CLI argv 会被 Windows 命令行长度截断**（20260918 实锤）：`cnb build start-build ... --data "$(cat payload.json)"` 报 `Argument list too long`（node 起的 CLI 包装器先撞上限，`--env userPrompt=<全文>` 同路径同样会撞）。**正解 = 绕开 CLI，直投 OpenAPI**：
  ```python
  # POST https://api.cnb.cool/<repo>/-/build/start
  # headers: Authorization: Bearer <token>、Accept: application/json、Content-Type: application/json
  # body = 整个 payload 文件的字节（json.dump(..., ensure_ascii=True) → 全 ASCII，零中文 argv 风险）
  urllib.request.Request(url, data=open("payload.json","rb").read(), method="POST", headers={...})
  ```
  返回 `{"sn":"cnb-xxx-...","success":true}` 即受理；随后照常用 `cnb build get-build-status --sn <sn>` 验 `npc go` stage = `start`。
  ⛔ token 从 `~/.cnb/token`（JSON，`access_token` 字段）读进变量，**不要内联进命令行**。
  附带：payload 用 `ensure_ascii=True` 落盘，可彻底规避「Git Bash argv 传中文给原生 exe」的编码风险。
- **⛔ `npc:go` 的 `timeout` 语义**：`timeout` 是 **Job 级**配置项（Pipeline / Stage 级**都没有** timeout 字段）。对 `npc:go` 而言它作用于 **Agent 的每一次工具执行**（单条 bash 命令）：单次超时或连续无输出达到该值 → 该条命令被中断；**未声明时 = 无输出 10 分钟 + 单次最长 2 小时**；**Agent 会话本身不设整体超时**。
  ⇒ 常见误解（含旧手册口径）是"声明 timeout: 4h = 整单能跑 4 小时"，**错**。声明 6h 的真实收益 = 单条长命令不会被 2h 砍 + 无输出容忍拉长。
  ⇒ ⚠ 平台另有**约 2h 的流水线硬性中止**（真值 `CNB_PIPELINE_MAX_RUN_TIME=7200000`，与 timeout 声明无关，脚本 Job 同样被掐）⇒ 完整取证与档位差异见 [[cnb-pipeline-2h-hard-cap]]；实操按 ≤1.5h 分段 + 开工即推/增量推送。
- **⛔ 别往 `env` 里塞 `role`（20260918 实测，1 秒内 error）**：OpenAPI 直投时若带 `env.role="<角色名>"`，`npc:go` 会去解析角色并**必读仓库内 `.cnb/settings.yml`**；没有该文件 → 立刻 `error: Cannot read .cnb/settings.yml`（936ms 就死，日志在 `get-build-stage` 里一眼看到）。
  ⇒ **默认不带 role**（`.cnb.yml` 里的 `role: $role` 解析为空即跳过角色解析）。只在仓库确实有 `.cnb/settings.yml` 且需要角色时才带。
  附带同一处的另两个坑：① `~/.cnb/token` 是 **JSON**（取 `access_token` 字段），直接 `Bearer <整个文件>` → `ValueError: Invalid header value`；② `branch` 字段可正常带（指定派单基线分支）。
- **容器=触发时点快照**：任务书触发前写全；之后补的评论它看不到；未推 commit 随容器蒸发；**未写进评论正文的附件会被平台回收**。
- **触发禁区**：@ 在引用块/代码块/表格/列表里不触发（必须普通段落）；编辑/重开不重触发；评论数 >100 不再触发；单事件最多 10 个 NPC。
- **代码版本语义**：issue 事件=默认分支最新 commit、PR 家族=预合并、push=当前分支——派单前确认默认分支是哪个。
- **串行铁律**：同 issue 上 @npc 未出终结态前禁再 @（叠触发=双容器）；"是否在跑"唯一权威=`GET /-/build/logs` 非终态条数（需 scope `repo-cnb-history:r`）；宁愿少发，发前问。
- **⛔⛔ 派单失败后的正确动作（20260917 四连败事故，用户点名骂"不要重复派发"）**：
  1. **先拉日志定位根因**（`cnb build get-build-stage --repo <r> --sn <sn> --pipelineId <sn>-001 --stageId stage-0`），**不要急着重派**。
  2. 根因若是 `.cnb.yml` 配置错 → **修配置、推送、等该 push build 结束**，再派**一次**。重派前先 `get-build-logs` 确认**无 pending 残留**（我 22:2x 就是没查，连开 4 单：u4o error→618 pending→2qo error，还误判 618"卡住"）。
  3. ⛔ **同一任务同一时刻只允许一个在跑**；重复单要 `cnb build stop-build --sn` 停掉（用 `--sn`，无需 pipelineId）。停 build 的判据：`status` 非终态（pending/running）才停；已是 error/success 的会返 `STOP_FAIL_WRONG_STATUS`（正常，说明它早已结束）。
  4. ⛔ **用户说"把该停的停掉"≠"全部停掉"**：先分辨哪些**在正常产出**（含已跑完还没合并的）、哪些是**卡死/重复的**；只停后者。我 22:3x 把跑出真产出的 `cnb-618` 一起停了，是过度扩大动作范围。
- **⛔ 派单前自检清单**（贴墙上）：① `.cnb.yml` npc:go 的 options 段引用了哪两个变量名？（通常是 systemPrompt + userPrompt）② body env 里这两个变量都传了吗？systemPrompt 是短人设（几十字），userPrompt 是完整任务书 ③ workMode 嵌 npc 内、不在 body 顶层 ④ 不传 role（env 和 npc 都不传） ⑤ 上一单是否已终结态 ⑥ 同一时刻只派一单 ⑦ **派完立刻等 30 秒再查 build 状态**，确认 npc go stage 不是秒崩（<2s error）而是 start/running。
- **验收金标准 = `git ls-remote` 出现新分支/PR**，不是 build 绿；NPC 会自己再检验再合并，本地勿抢跑；双容器处置=合并先交付的、关闭重复的。等交付时别死守预设分支名：`git ls-remote --heads` 扫全部新分支 + 查 build logs，别只盯一个 refspec 干等。
- **⛔⛔ 「建 PR」与「合并」的口径（两次相反枪口，务必区分场景，别再打架）**：
  - **20260915 被骂**：「**为什么建 PR？擅自做事**」（那次是**没被要求**就去建）。
  - **20260918 被骂**：「**为什么没见 pr？我不理解！肯定要建啊**」+「以后直接合并」（那次是**交付完成后该建却没建**）。
  - ⇒ **统一口径**：**「交付闭环」的正常流程 = 建 PR → 合并，两步都是常规动作**；用户说「为什么没见 PR」时，含义是**你漏了流程**，不是"不能建"。
  - ⛔ **我此前的错误解读**：把手册里「MR 与合并都是用户决策点」读成「**不该擅自建**」，于是交付后不建 PR。**正确含义 = 「由用户拍板触发」，不是「禁止建」**。
  - ✅ **可操作的判据**：**NPC 交付 + 我验收通过 ⇒ 直接建 PR 并合并**（用户 20260917/20260918 两次授权"以后直接合并"）；**验收没过 / 用户没派单 / 只是中途 sync ⇒ 不要建**。拿不准就问，别猜。
  - ⛔⛔ **20260919 第三次复发（同一坑，最严重一次）**：NPC 已建 PR #77，我却「验收通过后只写报告、没合并」→ 用户再问「**那为什么没看到pr呢？**」。
    ⇒ **病根 = 「验收通过」与「执行建/合」之间没有强制衔接**：审核完就以为收工了，把合并当"另一件事"。
    ⇒ **现起硬约束（写进验收 SOP，不许跳过）**：
      ```
      验收流程最后一步 = 合并动作本身，不是「写验收报告」。
      ✅ 验收结论一出，紧接着就查 PR：
          cnb pulls list-pulls --repo <org/repo>        # 看有无 open 且 head==产物 SHA
          - 有 → cnb pulls merge-pull --repo <r> --number <n> --merge-style merge --commit-title "<t>"
          - 无 → 先 cnb pulls post-pull 建，再合并
      ⛔ 不允许以「NPC 没建 PR」为由停下 —— 验收通过时，建 PR 也是我的活。
      ⛔ 报告末尾必须留一行「合并回执：<sn>/PR#<n>/sha」；没有这行 = 验收未完成。
      ```
    ⇒ 自查口诀：**「验收报告写完 ≠ 验收完；合并回执贴上 = 验收完」**。
    ⇒ ⚠ 与「串行铁律」的关系：合并是**收尾**动作，不违反串行；但若同时有多条未合并分支，**先看有无交集**（`comm -12 <(两分支改动文件列表)`）——无交集可按序合并，有交集才需解冲突。

- **⛔ 「有没有 PR」不能用 `git ls-remote | grep refs/pull` 判断**：该命令数的是**累积的全部 pull ref**（实测返回 160），既非本单、也非 open 态 ⇒ 会得出"有 PR"的错误结论。**唯一权威 = `cnb pulls list-pulls --repo <org/repo>`**，核对 `state: open` + `head.sha == 产物 SHA`。
  - 手册原文依据：合并/关闭由人做**或明确授权的 AI 做** —— 本用户的"直接合并"授权即属后者。
- **⛔⛔ 写 PR 监测脚本时：分支名字段是 `head.ref`，不是 `source`/`sourceBranch`**（20260919 实锤）：我自己的 `watch_sn.py` 只按顶层 `source` / `sourceBranch` 过滤分支名，而 CLI 实际输出的是**嵌套**的
  ```yaml
  head:
    ref: refs/heads/auto/xxx      # ← 真正的字段
  ```
  ⇒ 过滤**恒为空** ⇒ **PR #78 明明存在（`state: open`）却报 `PR=0`**，险致验收卡在「NPC 没建 PR」。
  ⇒ **修法**：解析块内 `ref:` 行（剥 `refs/heads/` 前缀），并留 `source`/`sourceBranch`/`head` 多形态兜底。
  ⇒ 同族铁律（第 N 例）：**「查不到」时先怀疑自己的查询形态** —— 字段名猜错会把「存在」判成「不存在」。同族：`grep "X = "` 对 `X: tuple[...] = ()` 不匹配；`--repo` 写长 URL 致 404；`wc -c` 当字符数。

- **编码纪律**：请求体一律 `json.dumps(...).encode("utf-8")`（ASCII 转义最稳）；禁 curl argv 内联中文（GBK 静默乱码入库）；合并用 `cnb pulls merge-pull`，REST merge 路径是 404 勿猜。
- **⛔ PR / issue / 分支的 CLI 命令形态（20260918 实测踩全套，逐条都是"看起来该有却没有"）**：

  | 想做什么 | ⛔ 错的写法 | ✅ 正确写法 |
  |---|---|---|
  | 建 PR | `cnb pulls create-pull`（**子命令不存在**） | `cnb pulls post-pull --repo <org/repo> --title <t> --head <b> --base <b> --body-file <win-path>` |
  | 合并 PR | `cnb pulls merge-pull --repo …`（缺参数即 400） | 必给 **`--merge-style merge\|squash\|rebase`**（缺 ⇒ `errcode:2000009 parameter merge_style must be one of …`）**且**必给 **`--commit-title`**（缺 ⇒ 400 `commit_title is required`，**无 `--title` 别名**） |
  | 关 issue | `cnb issues close --repo <r> --number N` | ⛔ 快捷命令 **不接受 `--repo`**（`unknown option '--repo'`）⇒ 用 `cnb issues update-issue --repo <r> --number N --state closed --state-reason completed` |
  | 评论 issue | `cnb issues comment --repo …` | 同上 ⇒ 用 `cnb issues post-issue-comment --repo <r> --number N --body-file <win-path>` |
  | 删分支 | 在 `cnb repositories` 模块里找 | **`cnb git delete-branch --repo <r> --branch <b>`**（**不在 repositories 模块**） |
  | 查 PR 列表 | `cnb pulls list-pulls --repo <r> --number <n>`（**`--number` 不存在**） | `cnb pulls list-pulls --repo <r> --state open --page-size 30`；⛔ **单查某 PR 也用不了 `--number`**，只能全量列出后自己筛 |

  - ⛔ **`--body-file` 必须传 Windows 原生路径**（`C:\...`）：传 `/tmp/x.md` ⇒ 报**文件不存在**（MSYS 路径未被原生 exe 识别）。
  - ⛔⛔ **`--repo` 必须用短路径名 `org/repo`**（如 `apigogo/mh-agent-open`）：写成 `cnb.cool/org/repo` ⇒ **`status:404 / errcode:5`**，极易误判成「PR 不存在」⇒ **排查任何"查不到"之前，先怀疑自己的参数形态**。
  - ⚠ **合并报 409 `the pull can not merge yet` = 有冲突**，不是"还没准备好"：查 `cnb pulls get-pull` 看 **`mergeable_state: conflict`**，逐文件定位（常见成因：分支基点早于其他已合并 PR，同区段重叠）。
  - ⛔ **删分支前必须 `git fetch` 并核对该分支最新 SHA 是否已并入主线**：分支可能在你「删过之后」**又出现**——不是被重建，而是**删除时机早于它的最后一次推送**（NPC 常在合并完成后补推一份交付报告/证据文档）。实测：删掉 `auto/ghost-wait-fix-e972` 数分钟后它在远端复现，因其在 PR 合并后又推了 `347fe3d`（323 行解冲突报告）。
    ⇒ 处置：`git log --oneline origin/<base>..origin/<branch>` 看有无**独有提交**；有实质内容（尤其证据/报告文档）就 `cherry-pick` 并入主线**再删**，别无脑删。
  - ✅ 成功回执形态：建单/合并/删分支均返 `status: 200`；合并另返 `sha` 与 `merged: true`。

- **API 卫生**：OpenAPI 必须带 `Accept: application/json` 否则 406；errcode **10023=scope 不足**（别误判"没登录"）；关 issue 的 `state` 与 `state_reason` 必须成对；删分支走 OpenAPI 且先关挂着的 PR（服务端禁 `git push --delete`）；⛔`credential.helper store`（明文落盘）。
- **git 凭据单源**：token 只认 `~/.cnb/token` 一处，git 走**按库** URL 级 helper 现读它（⛔ 禁配 cnb.cool 全域——会把一个库的 token 塞给别的库）；**修好的唯一验收 = `GIT_TERMINAL_PROMPT=0 git fetch <remote> <branch>` 静默通过**；轮换漏条目/弹窗/`credential approve` 不可靠三连坑详见 `pitfalls/credential-rotation-must-cover-all-entries.md`。
- 入口两个都免费：`@CodeBuddy` 默认免二选、日常用；`@npc/CodeBuddy(模型)` 要选模型。合并/关闭默认人工（或明确授权的 AI）。


- **⛔⛔ cnb login 拿的 OAuth token scope 可能不够派单**（20260920 agent-kb 项目实锤）：旧的 `~/.cnb/token`（`cnb_cli` OAuth 设备码授权）scope 只有 `account-engage:r`、`repo-cnb-history:r` 等只读权限——调 `build start-build` 直接 `HTTP 403 errcode:10024 The token's resource does not match this request`；调 `users get-user-info` 也 `10023 Missing required scopes: account-profile:r`（这两条是排查 scope 问题的好探针）。
  - **解法 = 重跑 `cnb login`**（设备码 OAuth）会重新协商 scope，新 token 会带上 `build:npc` 等；重 login 后 `build start-build` 直接通，**不需要再写 Python 拼 OpenAPI**绕 CLI。
  - 或者用 PAT（Personal Access Token，网页创建，scope 按需勾选）——一开始就是靠 PAT 直投才跑通，但 Python 拼 OpenAPI 维护成本高；**重 login 才是根解**。
  - 快速验证：重 login 后立刻跑 `cnb build get-build-logs --repo <r>`，能出 JSON = scope 够了。
  - PAT vs OAuth 两套凭据**共存不冲突**：git 凭据层走 URL 匹配（`credential.https://cnb.cool.helper = cnb git-credential`），API 层走 `~/.cnb/token`。轮换 token 时两边同步换——`~/.cnb/token` 是 OAuth 产物；Windows 凭据管理器里可能还有历史 PAT 残留（按 repo URL 存的 7 条 `git:https://cnb.cool/...`），不用管，git 会优先走 cnb git-credential 再 fallback。


- **⛔⛔⛔ payload body 格式（20260921 补 systemPrompt 必传，四次迭代才对）**：
  正确：{"npc": {"name": "CodeBuddy", "workMode": True}, "env": {"systemPrompt": "短人设", "userPrompt": "任务书"}}
  错误1：env 只传 userPrompt 不传 systemPrompt → 秒崩 "requires systemPrompt"（<2s error）
  错误2：workMode 在 body 顶层不在 npc 内 → NPC 拿到只读 scope，第一次 push 就 403
  错误3：扁平 userPrompt/workMode 直接在 body 顶层
  - **禁 role**：不传 env.role 也不传 npc.role（系统 NPC 不读 settings.yml，传了反会去解析不存在的文件秒崩）
  - **必跑断言**：构造 payload 后先 assert body["npc"]["workMode"] is True; assert "workMode" not in body; assert body["env"]["systemPrompt"].strip(); assert body["env"]["userPrompt"].strip(); assert "role" not in body["env"] and "role" not in body["npc"]
  - **为什么会错**：CLI 的 --npc-name / --npc-workMode 只是命令行便捷参数，最终还是要嵌回 body 的 npc 结构里。别把 CLI 参数名和 body JSON 字段名搞混。env.systemPrompt 容易漏是因为 .cnb.yml 的 options 段同时引用了 $systemPrompt 和 $userPrompt 两个变量。
  - **排错信号**：派单成功(200)但 build 跑 <2s 就 error + runner log 全是 setup（没进 NPC 阶段）→ 99% 是 payload 格式缺字段，拉 build-runner-download-log 看 runner log 最后几行通常能看到明确的参数校验报错（"requires systemPrompt"/"requires userPrompt"）。
  - **排错信号**：派单成功(200)但 build 跑 5-6 秒就 error + runner log 全是 setup（没进 NPC 阶段）→ 99% 是 payload 格式错，拉 build-runner-download-log 看 runner log 最后几行通常能看到明确的参数校验报错。

**配额 / 自托管 Runner / CLI 新坑**已拆为独立条目：见 [[cnb-quota-runner-cli-notes]]。
