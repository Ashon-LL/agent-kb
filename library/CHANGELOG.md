# 全局经验库 变更日志（kb）

> 自 `INDEX.md` 迁出（2026-09-30 知识库治理 P0-1）。内容为历次沉淀与修订记录，原文照录、未做删减。
> 索引与条目正文见 `INDEX.md` 与 `{pitfalls,tools,workflow}/`。

> 2026-09-14 首次收割：从 8 个项目记忆库晋升 18 条（经用户逐条确认）。
> 2026-09-15 二次收割：+2（凭据轮换 / 续跑锚点基准坑），CNB 派单条目两轮修订（MR 决策点、按库作用域、验收扫全分支）。
> 2026-09-15 三次收割：+10（OOXML 属性静默失效、图文遮挡与距离、数值基准表述、AI 披露一致性、不覆盖用户手调产物、本机文本自检、缺陷定位方法论、规范优先级、数模图表基线、ZCode 资源落点），另扩充"读-改-写全量 PUT 事故家族"与 docx 管线条目的指针。
> 2026-09-15 日常沉淀：+6（自动化产物新鲜度、日志字面语义三档汇报、禁讨好开场、stdio MCP 安装验收法、其余见 git log），条目数至 36。
> 2026-09-15 全量质检+整合：合并 3 组（/tmp 坑并入 Windows 合集；GitHub 下载+推送→双向通路；ZCode hooks+落点→平台事实），MCP 条目的 Windows 进程 spawn 知识迁至 Windows 合集，docx 管线去掉与 OOXML 专条的逐字重复。**36 → 33**。
> 2026-09-17 日常沉淀：+1（New API base_url 不能带 /v1）。**33 → 34**。
> 2026-09-17 日常沉淀：+1（New API 多密钥 size 必须与 key 段数同步）。**34 → 35**。
> 2026-09-17 日常沉淀：+1（台账核对必须双向），并补索引上一轮漏登记的 `newapi-multikey-size-must-track-key-count`（此前只有 header 计数、无 INDEX 行）。**实际条目 38**（此前计数偏少 2）。
> 2026-09-17 日常沉淀：+1（New API 禁用渠道必须同步 abilities.enabled）。**实际条目 39**。
> 2026-09-17 扩充 `newapi-disable-must-sync-abilities`（非新增条目，计数仍 39）：改 `channels.group` 同样要手工重建 abilities（照 `UpdateAbilities` 语义，Tag 取 `channels.tag`）；**INSERT 占位符/列顺序错位会静默产出不可路由行**——字面量 `1` 占错槽，第 4 个占位符落进 `enabled`，全表写成 `enabled=4/5/2/0`，行数看着对但 `WHERE enabled=1` 把整批路由全断。别把"行数对"当验收。
> 2026-09-17 重大修订：`tools/cnb-npc-dispatch-essentials.md` 补 **api_trigger_npc 派单三字段唯一正解**（任务书塞 `env.userPrompt` 而非 `options.systemPrompt`；`userPrompt` 不可写死；`workMode` 嵌 `npc` 内）+ **派单失败后正确动作**（先查日志根因、修配置、确认无 pending 残留、只派一次）+ **"该停的停"≠"全停"** 判据。事故来源：同一任务连派 4 次（u4o/618/2qo），误判在跑单"卡住"。
> 2026-09-17 日常沉淀：+1（配置字段名不是规格，读消费它的代码）。**实际条目 40**。
> 2026-09-18 日常沉淀：+2（思考型模型 reasoning 与正文共用 max_tokens 预算；**测试扫描范围必须钉在 git 索引**）。**实际条目 42**。
> 2026-09-18 日常沉淀：+1（**here-doc 进容器缺 `-i` 静默丢 stdin，零输出零报错**）。**实际条目 43**。
> 2026-09-18 日常沉淀：+1（**WorkBuddy `present_files` 传 URL = 侧栏内置浏览器打开该网页**）。**实际条目 44**（20260918 实测 `find tools workflow pitfalls -name '*.md' | wc -l` = 43，与「实际 44」差 1，历史计数本身有偏差，以 `find` 为准）。
> 2026-09-18 日常沉淀：+2（**从 Python spawn CNB CLI 必须用 `cnb.cmd`**；**任务书要写性质而非我猜的手段**）。
> 2026-09-18 日常沉淀：+1（**OpenClaw 真实上游实弹验证**：三层验证法 + UA/Cloudflare、MSYS 路径、`exec` 稳过但 `--local` 不收敛）。**实际条目 45**（`find` 实测 44，历史计数仍偏 1，以 `find` 为准）。
> 2026-09-18 日常沉淀：+1（**同名 `timeout` 键在 `npc:go` 与脚本 Job 上语义不同**）。另修 INDEX 漏登记两条（`bare-wait-deadlocks-on-long-lived-children` 与 `same-config-key-...` 曾只有文件无索引行）。**实际条目 49**（`find tools workflow pitfalls -name '*.md' | wc -l` = 49，INDEX 行数亦 49，本次首度对齐）。
> 2026-09-18 日常沉淀：+3（**2h 硬边界取证两出口 + 日志分层纪律**已并修订 `same-config-key-...`；**PS 工具 stdout 恒空改用写文件**；**从 Python spawn CNB CLI 用 `cnb.cmd`**）。**实际条目 52**（`find` = 52，INDEX 行数 = 52，仍对齐）。
> 2026-09-18 日常沉淀：+4（AstrBot 运维会话提炼，四条同属"改第三方应用内部状态/验证"家族：**镜像内源码补丁必须配幂等重放脚本**、**DB 列格式由读它的代码决定**、**文件持久化要连清理钩子一起放开**、**验证要用它自己的类走真实管线且探针不得有写副作用**）。**实际条目 56**。
> 2026-09-18 重大修订（非新增条目）：`tools/cnb-npc-dispatch-essentials.md` 补两块 —— ① **PR / issue / 分支的 CLI 命令形态对照表**（`create-pull` 不存在⇒用 `post-pull`；`merge-pull` 必给 `--merge-style` **且** `--commit-title`，否则 400；`issues close/comment` **不接受 `--repo`**⇒用 `update-issue`/`post-issue-comment`；删分支 = `cnb git delete-branch`（**不在 repositories 模块**）；`--body-file` 必须传 **Windows 原生路径**；`--repo` 必须用 **短路径名 `org/repo`**，写成 `cnb.cool/...` ⇒ **404/errcode:5**）；② **「建 PR」vs「合并」口径统一** —— 20260915 与 20260918 两次相反枪口（先说"擅自做事"、后说"为什么没见 pr"）已裁定：**验收通过 ⇒ 建 PR + 合并都是常规动作**，别再把"用户决策点"读成"禁止建"。
> 2026-09-19 补充修订（第三次复发，非新增条目）：同条目补 **验收强制衔接** —— 「**验收报告写完 ≠ 验收完；合并回执贴上 = 验收完**」；验收 SOP 最后一步 = 查 PR（`cnb pulls list-pulls` 核对 open + head==产物 SHA）→ 有则 `merge-pull`、无则先 `post-pull` 再合；⛔ 不得以「NPC 没建 PR」为由停下；报告末尾必须留「合并回执」行。另补：**判断"有没有 PR" 禁用 `git ls-remote | grep refs/pull`**（数的是累积 160 条 pull ref，会误判），唯一权威 = `cnb pulls list-pulls`。
> 2026-09-19 补充修订（非新增条目，仍改同一条 `cnb-npc-dispatch-essentials`）：补 **PR 分支名字段是 `head.ref` 而非 `source`/`sourceBranch`** —— 我自己的 `watch_sn.py` 因此**过滤恒空、PR #78 明明 open 却报 `PR=0`**，险致验收卡在「NPC 没建 PR」；另补 `cnb pulls list-pulls` **不接受 `--number`**（单查也只能全量列出后自筛）。⇒ 同族铁律再添一例：**「查不到」先怀疑自己的查询形态**。
> 2026-09-20 日常沉淀：+1（**覆盖式配置会丢掉隐式兜底** —— `--config`/自建最小配置驱动外部工具时向导默认全丢，依赖能力须逐项显式声明，漏一个即静默降级；含「可见性≠可用性」「声明不可用值⇒整份 config invalid」「全局开关须先就绪后声明」三坑）。**实际条目 66**（`find` 实测，与索引行数对齐）。
> 2026-09-19 日常沉淀：+1（**扫描器把自己的输出扫回来** —— 门禁自指假阳性）。另**事实修正**一条：`same-config-key-different-semantics-per-step-type` 里原标 `未验证` 的「纯脚本 Job 跑超 2h 会否被掐」⇒ 经用户裁定**定为「会被掐」**（用户做过对照实验），故 `CNB_PIPELINE_MAX_RUN_TIME` 是**与步骤类型无关**的流水线硬天花板。（证据来源为用户裁定，已在文中如实标注，不冒充我的实测。）
> 2026-09-19 日常沉淀：+1（**自己维护的「未做/待办」台账会腐烂** —— 一次通读 + 逐条复核发现 6 条「未做」**全部其实已闭环**；拿台账当任务书输入前必须按**机制**（消费点/迁移代码）而非**名字**在代码里复核，并把结论当场写回）。**实际条目 64**（`find` 实测）。
> 2026-09-19 补充修订（非新增条目，仍改 `pitfalls/windows-scripting-terminal-gotchas`）：**引号 heredoc 也吃反斜杠** —— `python - <<'PYEOF'`（**带单引号**、按 POSIX 应逐字传递）在本机 Git Bash 里仍把 `\\` 折成 `\`，症状是补丁锚点**静默不匹配**（`count(old)==0`，易误判"锚点抄错"）或更糟——反斜杠落进写入内容把文件写坏。对策：补丁脚本别写含反斜杠的锚点，必须写就用 `chr(92)`，或改用编辑工具/Write 落盘；写后立刻 `ast.parse()`。同处补写侧 CRLF 修法（`open(..., newline="\n")`，只写 `encoding=` 不够）。**条目数不变。**
> 2026-09-19 补充修订（非新增条目，仍改同上条目）：补四条 —— ① **改 PATH 顺序解决不了**（CreateProcess 里 System32 恒先于 PATH；⚠ 且 Git Bash 里看到的 PATH 顺序是它自己前置过的，**会骗人**，真实 Windows PATH 是 System32 在 [0]）；② **没有「禁用别名」捷径**（System32ash.exe 是真文件非别名）；③ 正解用显式变量 `CLAUDE_CODE_GIT_BASH_PATH`（但**只影响宿主 shell**，python subprocess 不解析它）；④ ⛔⛔ **能力探针必须测「真正要用的能力」** —— 只测 bash 语义时，WSL 被拒靠的是转发层劫持 `$X` 的**偶然**，怪癖一变就会漏放进来；应把「能跑 `/c/...` 形态脚本文件」当入选条件。**「碰巧拒绝」≠「判据正确」。**
> 2026-09-21 日常沉淀：+2（**Tauri 远程 URL 没有 IPC**；**Windows 标题栏由系统设置支配** —— 两者都是"代码/权限/产物全对、运行时静默失效"型，且都附了实测四联证据与出路）。**实际条目 69**（`find` 实测）。
> 2026-09-21 日常沉淀：+1（**阿里系 SRC 资产有 WAF，路径枚举式探测会被 block_deny 页拦截并留痕** —— 别把 WAF 页（含 gateway-diagnostic/block_phase 特征）当"接口存在"；单主机经典路径 ≤10、串行、正常 UA；WAF 页/SPA 兜底页/登录跳转页是三种最常见假阳性）。**实际条目 67**（`find` 实测）。
> 2026-09-21 日常沉淀：+2（**SRC 挖洞前先查驳回标准** + **SRC 无效漏洞判定基准**）——源自 BUG-004 理想门店电话被用户裁定「不算」：263 家门店手机号+坐标免登录全量返回、证据链完整、报告写完，仍落在 ASRC 敏感数据分级「其他数据=可能直接驳回」档。教训：**半公开经营信息泄露 ≠ 敏感信息泄露**；POI/商家联系方式类默认不投，动手前先拿目标 SRC 的分级表自问一遍。
> 2026-09-23 日常沉淀：+2（**出版级中文配图管线** —— HTML/CSS 卡片 + Playwright 元素截图；**html-to-docx 的 Windows venv 布局坑** —— `bin/` vs `Scripts/` 判据失配 + 依赖安装静默失败）。另**修复** `INDEX.md` 一处真实 NUL 字节（Git blob 哈希示例 `sha1("blob <len>\0"+bytes)` 被写成了裸 0x00，致 `grep` 把整份索引判为二进制而跳过）。**实际条目 88**（`find` 实测）。
> 2026-09-24 日常沉淀：+1（**OpenClaw typed hook 目录** —— 拦工具调用的 hook 叫 `before_tool_call` 不是 `tool_call`（我任务书里写错过，NPC 依官方 reference 纠正）；`session_start` 是 Observe 型改不了数据；⚠️ `before_tool_call` 超时 15s 且 **fail-closed**，桥接脚本必须自带兜底）。**实际条目 89**（`find` 实测）。
> 2026-09-28 日常沉淀：+2（**校验器 `continue` 掉缺项静默漏检**；**New API rc.26 渠道 CRUD 端点形状与 `data` 列表陷阱**）。
> 2026-09-28 补：+1（**New API rc.26 令牌 CRUD 三坑** —— `POST` 成功但 `data=null` 拿不到 key、列表接口是**掩码 key**、`DELETE /api/token/{id}` 读错参数恒假失败；另含 `UserUsableGroups` 模型名在 value 不在 key 的漏判坑）。**同时更正** `newapi-rc26-channel-crud-shapes` 的错误结论：`GET /api/channel/test/{id}` **不是免 token**，要 admin Bearer，且 401 与模型是否存在无关。另：写幂等脚本时**别断言 key 以 `sk-` 开头** —— 库里存的是裸 48 位无前缀，那一步会让脚本 abort 在**已经成功的生产写操作之后**。**实际条目 103**（`find` 实测）。
> 2026-09-30 日常沉淀：+1（DSH 桌面端 llm-pi-ai 自定义网关的六处反直觉，ZCode 8 路由 19 模型迁入，全部从 app.asar 解包源码实证）。
> 2026-09-30 作用域修正：+1（**kb 条目的 source 就是作用域边界**）+ **修订 2 条**（`llm-context-window-is-input-plus-output` 与 `dsh-llm-pi-ai-reasoning-config-traps` 第 8 条）——起因是我把 AstrBot 网关的 `input + max_tokens ≤ window` 教训当通用定律套到 DSH/StepFun，去劝阻用户有意设的 1000000；正文作用域块、`description:` 前缀、INDEX 行**三处**都补了标记（只写 body 等于没写，检索只读 description）。另按用户「不要乱动」收口：stepfun2 的思考模式设置、workbuddy 的 image 输入均为有意为之，停止上报为缺陷。**索引行数与 `find` 实测重新对齐（此前 107 vs 108，缺本条）**。
> 2026-09-30 日常沉淀：+1（**MCP 有没有用看 handler 返回什么** —— 用户问 sequential-thinking 有用吗，读源码判定"传进去的 thought 一个字不回传"= 单向通道零信息量，且描述常驻系统提示每轮烧 token，可删；同族判据：返回值与入参无关 + 只 `console.error` 给人类看 + description 全是祈使句提示词）。
> 2026-09-30 作用域二次审计：用户指出"模型上下文和最大输出方面是专项却容易被当公用，这只是一个方面还有其他"。按**「description 里有具体数值上限/错误码/返回结构/字段名却没点名平台」**这条标准扫 110 条，**真要修的只有 2 条**：`reasoning-model-max-tokens-shares-budget`（商汤 sensenova-6.8-flash-lite 单模型实测，"content 键整个不存在"疑似该模型特有）、`quota-exhausted-vs-banned-distinguish`（`14018`/`11140` 是 New API 平台业务码，换网关即失效），两条的 description/正文/INDEX 行三处都补了作用域。**同时立下反向规则：单来源≠伪通用**——bind mount、克隆行残留、全量 PUT、P-256 那些本就是通用规律只是碰巧在某项目踩到，硬贴作用域只是噪声。元教训已写进 `kb-entry-source-scope-is-the-boundary`：**修了一条 ≠ 修了这个家族，补标记时必须 grep 同族**。
