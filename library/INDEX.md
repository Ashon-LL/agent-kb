# 全局经验库索引（kb）

> 一事实一文件；收录标准=跨项目可复用（项目专属留在项目 memory）。
> 目录：`tools/` 工具链 · `workflow/` 流程协作 · `pitfalls/` 失败教训

## pitfalls/ 教训与反模式

- [并行测试必须先隔离「会写仓库工作树的用例」](pitfalls/parallel-test-run-must-isolate-repo-mutators.md) — 会写工作树的用例独占跑；-n 别进 addopts
- [动态工作流的子代理身份与门禁三坑](pitfalls/dynamic-workflow-agent-identity-and-gates.md) — 循环内建 agent 撞重名；门禁先清被拦对象
- [Tauri 自定义命令的 ACL 三处一致](pitfalls/tauri-app-command-acl-three-places.md) — 命令名须同现三处 ACL，缺一静默失效
- [校验器 `continue` 掉缺项 = 门禁全绿地漏检](pitfalls/silent-continue-masks-lost-check-coverage.md) — 缺项 continue ⇒ 校验被跳过、门禁仍全绿
- [New API rc.26 渠道 CRUD 端点形状](pitfalls/newapi-rc26-channel-crud-shapes.md) — body 包 mode、删走路径参、option 非字典
- [New API rc.26 令牌 CRUD 三坑](pitfalls/newapi-rc26-token-crud-shapes.md) — key 在响应里、列表是掩码、DELETE 恒失败
- [Tauri Linux CI 需 webkit2gtk-4.1，无 Ubuntu 镜像](pitfalls/tauri-linux-ci-needs-webkit-41-and-target-override.md) — 无 Ubuntu 镜像；本机只编 Windows 目标
- [GitHub PR 表单是 details 折叠开关](pitfalls/github-pr-form-is-a-details-disclosure.md) — 大按钮非导航；用原生 setter+requestSubmit
- [孤儿常量与导入期告警不是阻塞项](pitfalls/orphan-constants-and-import-warnings-are-not-blockers.md) — 判阻塞先 grep 使用点；只有终点可观测物算证据
- [读-改-写全量 PUT 事故家族](pitfalls/redacted-get-full-put-wipes-secrets.md) — GET 脱敏 + 全量 PUT 会静默清空
- [环境变更陈述必须命令复测](pitfalls/env-claims-must-be-reverified.md) — 环境陈述一律命令复测；“通过”字样不可信
- [一次性脚本改文件四铁律](pitfalls/oneoff-script-file-edit-rules.md) — 备份不被重跑覆盖、重发留段头、改后校验存在性
- [文件更新 ≠ 代码在跑](pitfalls/file-change-not-code-running.md) — 核对进程启动晚于文件 mtime，别看“已更新”
- [Windows 脚本/终端/互操作坑合集](pitfalls/windows-scripting-terminal-gotchas.md) — MSYS 路径、双引号吞 $_、spawn、裸名 bash=WSL
- [从 Python spawn CNB CLI 必须用 `cnb.cmd`](pitfalls/cnb-cli-needs-cmd-suffix-when-spawned-from-python.md) — subprocess 调 npm CLI 须用 .cmd 全名
- [PS 工具 stdout 恒空，改用「写文件 + Bash 读」](pitfalls/powershell-tool-stdout-empty-write-files-instead.md) — Stdout:(empty)≠没输出；只写文件可靠
- [克隆整行会留下模板残留](pitfalls/clone-row-leaves-template-residue.md) — 克隆必带模板残留；用值重复检测
- [here-doc 进容器必须显式要 stdin](pitfalls/container-heredoc-needs-stdin-flag.md) — docker exec 缺 -i、ssh 缺 -T 会丢 stdin
- [PS here-string 定界符语法与运行时字节分岔](pitfalls/powershell-herestring-grammar-and-runtime-divergence.md) — 开闭不对称、<< 是重定向、UTF8 不跨运行时
- [bind mount 属主必须匹配容器 uid](pitfalls/bind-mount-owner-must-match-container-uid.md) — 属主由宿主决定、容器内 chown 无效；看容器真读到
- [吞掉 OSError 会把权限错配伪装成「未配置」](pitfalls/broad-oserror-swallow-hides-permission-misconfig.md) — 只吞 FileNotFoundError、其余 OSError 冒泡
- [Qoder Office pptx 图片管线故障与页内动画注入](pitfalls/qoder-office-pptx-image-and-animation-workarounds.md) — 带图 put_page 会挂→拆两步；动画只能 zip 注 timing
- [裸 wait 会被常驻子进程永久阻塞](pitfalls/bare-wait-deadlocks-on-long-lived-children.md) — 裸 wait 被常驻子进程永久阻塞；兜底包整个脚本
- [空值 credential.helper 阻塞 git fetch，unset-all 误删好条目](pitfalls/credential-helper-empty-value-blocks-git-fetch.md) — 空值 helper 让 git 阻塞；unset-all 误删好条目
- [凭据管理器里的 host 级条目会抢先命中](pitfalls/credential-rotation-must-cover-all-entries.md) — host 级条目抢先命中；按库隔离挂专用 helper
- [测性能前清续跑锚点](pitfalls/clear-resume-anchors-before-benchmark.md) — 测墙钟前先清续跑锚点，否则只测到收尾
- [docx 管线交付坑](pitfalls/docx-pipeline-delivery-gotchas.md) — Word 重存丢字号、draw.io 0 字节导出
- [OOXML 排版属性四类静默失效](pitfalls/ooxml-layout-attributes-silently-ignored.md) — *Chars 覆盖磅值、exact 行距裁图、重存丢 tblW
- [图-引用距离与图例遮挡](pitfalls/figure-placement-and-legend-occlusion.md) — 几何自检只判出界不判遮挡；图须紧邻引用句不跨页
- [自动化"在跑"要查两件事](pitfalls/automation-artifacts-lie-existence-and-freshness.md) — 存在性与新鲜度须双层独立检查
- [日志字面语义不是规格](pitfalls/log-text-is-not-spec-read-emitting-code.md) — 先 grep 发提示语的代码；汇报分三档
- [配置字段名不是规格](pitfalls/config-field-name-is-not-spec-read-consuming-code.md) — 名字像的字段各管一件事、改错无报错；读消费方代码
- [覆盖式配置会丢掉隐式兜底](pitfalls/override-config-drops-implicit-fallbacks.md) — --config 驱动会丢向导默认；依赖能力须显式声明
- [多主人 config 必须读-合并-写](pitfalls/shared-config-multi-owner-merge-write.md) — 多写入者 config 全量覆盖会抹掉别人的键；读-合并-写
- [思考型模型 max_tokens 共用预算](pitfalls/reasoning-model-max-tokens-shares-budget.md) — 与正文共用 max_tokens；吃满时无 content 键
- [LLM 上下文窗口 = 输入 + 请求的 max_tokens](pitfalls/llm-context-window-is-input-plus-output.md) — 【作用域=AstrBot tdp+qwen3.8-27b】超窗先 400
- [kb 条目的 source 就是作用域边界](pitfalls/kb-entry-source-scope-is-the-boundary.md) — 检索命中≠该用；作用域标记写进 description
- [DETACHED_PROCESS 会引发黑窗风暴](pitfalls/detached-process-causes-console-window-storm.md) — 与 CREATE_NO_WINDOW 互斥，改用 NO_WINDOW
- [强规范对象别自造编码器](pitfalls/dont-handroll-spec-encoders-use-libraries-plus-fallback.md) — QR/条码/PDF 别自造编码器（错得静默）
- [测试的扫描范围/前提/断言三类假单](pitfalls/test-scope-must-be-pinned-by-git-index.md) — 范围用 git ls-files；断言放宽分支是假绿
- [禁止讨好式确认开场](pitfalls/no-sycophantic-agreement-openers.md) — 删讨好开场；被纠正=认领+修正+干活
- [跟进 agent 循环看进展不看动静](pitfalls/agent-loop-follow-progress-not-liveness.md) — 同错×N+零交付判不收敛；守望须设时限
- [New API base_url 不能带 /v1](pitfalls/newapi-base-url-never-carry-v1.md) — 带了变 /v1/v1 报 404；全绿证不了 base_url
- [New API 多密钥 size 必须跟段数](pitfalls/newapi-multikey-size-must-track-key-count.md) — 追加 key 不改 multi_key_size，新钥当后缀
- [台账核对必须双向](pitfalls/ledger-audit-must-be-bidirectional.md) — 只跑单向会漏整类问题；库里有值≠线上在用
- [待办台账会腐烂，开单前先复核](pitfalls/backlog-records-rot-verify-before-dispatch.md) — 未做≠还没做，按机制复核；实测 6/6 已闭环
- [同名配置键在不同步骤类型下语义不同](pitfalls/same-config-key-different-semantics-per-step-type.md) — 脚本 Job=总时长超时，npc:go=单次执行
- [New API 禁用渠道/改分组都要重建 abilities](pitfalls/newapi-disable-must-sync-abilities.md) — abilities 是唯一路由事实源；须手工重建+回读
- [产出端与消费端状态不匹配会静默空转](pitfalls/producer-consumer-status-mismatch-silently-noops.md) — 产出写 candidate、消费只查 active ⇒ 空转
- [容器镜像内源码补丁必须配重放脚本](pitfalls/container-image-source-patches-need-replay-script.md) — 扛 restart 不扛 rm/升级；须配幂等重放脚本
- [第三方应用 DB 列格式由读它的代码决定](pitfalls/third-party-db-columns-typed-by-reading-code.md) — 弱类型收得下≠读得动；一行类型不符可整表查询失败
- [多层服务各有凭据，接错层表现为 401](pitfalls/layered-service-credentials-must-match-layer.md) — 接错层只报 401；验证与配置须共用常量
- [文件"持久化"要连清理钩子一起放开](pitfalls/persisting-files-also-requires-exempting-cleanup.md) — 换持久目录仍被每轮 cleanup 删
- [验证要用应用自己的类走真实管线](pitfalls/verify-with-real-pipeline-and-readonly-probes.md) — 持久化格式≠API 输入格式；用应用自己的类验证
- [PS Start-Process 参数会丢内层引号且静默失败](pitfalls/powershell-start-process-argumentlist-strips-quotes.md) — 会剥内层引号且不抛异常；参数先落盘再传
- [扫描器把自己的输出扫回来](pitfalls/scanner-flags-its-own-archived-output.md) — 门禁恒 FAIL 先怀疑自指；修完须做反证防假绿
- [阿里系SRC资产WAF拦截路径探测](pitfalls/alibaba-src-assets-waf-block-probing.md) — 路径枚举会触发 WAF block_deny 页并留痕
- [验证脚本的 UA 会伪造配置失败](pitfalls/verification-script-ua-can-fake-a-config-failure.md) — CF 1010 拦的是 urllib 指纹非无 UA
- [PowerShell bool-eq string 隐式转换坑](pitfalls/powershell-bool-eq-string-casts-string-to-bool.md) — bool 与 string 比较会隐式转换；比较前显式转类型
- [SRC 无效漏洞判定基准](pitfalls/src-invalid-bug-baseline.md) — 门店电话/POI 坐标属“其他数据”，默认驳回
- [接码/号码平台的号多为存量已消耗号](pitfalls/resource-pool-acquired-numbers-are-spent.md) — “未使用过”只看本平台；用 CreateTime 跨度判存量
- [额度耗尽 vs 账号级封禁：两类不可用，修法完全不同](pitfalls/quota-exhausted-vs-banned-distinguish.md) — 【作用域=New API】429 额度尽 vs 403 封禁
- [配额取哪个字段决定结论](pitfalls/quota-field-whose-value-decides.md) — 多个剩余量字段只有消费方用的算数
- [纯标准库手写 P-256 ECDSA/DPoP 的四个坑](pitfalls/p256-ecdsa-handrolled-pitfalls.md) — a=−3 非 0、ES256 是裸 r‖s 非 DER；须与库比对
- [DSH 桌面端自定义网关的六处反直觉](pitfalls/dsh-llm-pi-ai-reasoning-config-traps.md) — 补丁替换整行 config、必写 off、路由名禁连字符
- [会 roll 的 refresh token 只能有一个刷新者](pitfalls/rotating-refresh-token-needs-single-writer.md) — 多组件各刷会让 RT 作废→401/账号被禁
- [应用自生成的凭据文件权限默认是宽的](pitfalls/generated-credential-files-default-permissive.md) — 程序写的凭据多 644、明文 token 同机可读
- [ZCode 配置无 reasoning.enabled，禁用须用 reasoningLevel.map](pitfalls/zcode-provider-config-no-reasoning-enabled-schema.md) — 写 enabled:false 被静默忽略
- [同一概念有多套实现，选错会静默丢语义](pitfalls/same-concept-multiple-implementations-pick-semantics.md) — 禁用多实现语义差别大、选错不报错；先枚举读注释
- [Tauri 非 tauri:// 来源的 invoke 被 ACL 拦而非对象缺失](pitfalls/tauri-remote-url-has-no-ipc.md) — 坏的是 invoke 被 ACL 拒，非对象缺失
- [Windows 标题栏颜色由系统主题说了算](pitfalls/windows-titlebar-theme-dictated-by-system.md) — 由系统设置支配，IMMERSIVE_DARK_MODE 被忽略
- [被周期覆盖的状态文件不能手改](pitfalls/periodically-overwritten-state-file-cannot-be-hand-edited.md) — 周期全量重写的文件手改双重无效

## workflow/ 流程与协作

- [哨兵（后台监查进程）](workflow/sentinel-background-watch.md) — 起后台进程轮询并自己判终态 exit；响≠好消息
- [最小改动与不越界三铁律](workflow/minimal-change-and-no-scope-creep.md) — 按字面范围改、闭环即止、不做表面修补
- [线上是运营态、全量扫描双扫对齐](workflow/online-is-authoritative-dual-scan.md) — 漂移以线上为权威先问再修；只扫本地不算全量
- [上游异常先查现状再动手](workflow/research-upstream-before-fixing.md) — 免费源脆弱；是否已切换以 DB/API 实测为准
- [子代理编排实战细节](workflow/subagent-orchestration-lessons.md) — 契约先行+文件不相交才并行；失败先续跑勿重派
- [Jev 与 KB 的适用场景及 DSH 清单核验](workflow/use-jev-and-kb-deliberately.md) — Jev 做类型化判断、KB 做检索沉淀
- [日志全量通读方法论](workflow/log-full-read-not-just-errors.md) — 只筛 error 会漏显示假象与产品缺陷
- [平台操作优先 CLI 而非浏览器](workflow/cli-over-browser-automation.md) — 先读文档用命令/API；浏览器只留扫码与一次性 token
- [凭据卫生](workflow/token-and-secrets-hygiene.md) — token 不内联命令行、公开内容零敏感痕迹
- [git 操作先核对仓库归属](workflow/git-remote-ownership-check.md) — 先 remote -v 认角色；默认分支=ls-remote --symref
- [数值结论必须带基准与主语](workflow/numeric-claims-need-baseline-and-subject.md) — 数字全真但表述错也会被读成离谱结论
- [AI 使用披露一致性](workflow/ai-disclosure-consistency.md) — 支撑材料与声明逐项对齐、禁缩水披露
- [用户手工调过的产物即最终稿](workflow/deliver-user-tuned-artifact.md) — 改文字给可粘贴纯文本；改版式只报重建代价
- [交付前本机文本自检](workflow/pre-delivery-text-selfcheck.md) — 不联网查重复/AI 痕迹：10 字窗口重合、句长 CV
- [缺陷定位方法论](workflow/defect-localization-methodology.md) — 根因分层排除+对照实验；对照组须含基线身份
- [OpenClaw 真实上游实弹验证](workflow/openclaw-real-upstream-fire.md) — 直连→最小回合→工具回合；CF 要浏览器 UA
- [交付格式规范优先级](workflow/spec-priority-official-first.md) — 官方规范>模板默认>通用知识库；未规定的保持默认
- [任务书要写「性质」而非「我猜的手段」](workflow/taskbook-write-the-property-not-your-guessed-mechanism.md) — 写死手段会逼执行方两难；写性质+已满足则回报
- [SRC 挖洞前先查驳回标准](workflow/src-prehunt-check-rejection-standard.md) — 先读无效范围/分级/降级规则；拿不准就放弃
- [账号池汇报用用户可认的称呼](workflow/account-pool-friendly-naming.md) — 用手机尾号/系列+序号称呼，禁内部 ID 与裸序号

## tools/ 环境与平台

- [GitHub 大陆双向通路（下载+推送）](tools/github-china-network-workarounds.md) — 下载用 jsdelivr/curl 续传；推送须探测+hosts 一体
- [git 传输死时走 Git Data API 构造提交](tools/github-git-data-api-push-without-git-transport.md) — 零 git 二进制建分支推提交；须本地 SHA1 预验证
- [细粒度 PAT 缺 PR 写权限 → 403](tools/github-fine-grained-pat-pr-write-403.md) — 能推≠能开 PR；先 GET /pulls 分辨权限 vs 不存在
- [CNB NPC 派单要点](tools/cnb-npc-dispatch-essentials.md) — 大任务书走 argv 会截断；workMode 嵌 npc 内
- [CNB issue 附件下载坑](tools/cnb-issue-attachment-download.md) — asset_link 是 Cookie 鉴权路由；200 可能是假 SPA
- [LLM 网关排障优先级](tools/llm-gateway-triage-priorities.md) — 命中率波动先查 429 切渠道/前缀缓存
- [ZCode 平台实测事实](tools/zcode-platform-verified-facts.md) — 资源落点 + hooks 默认关与 trust 门控
- [ZCode 删会话是软删：状态与正文分两个库](tools/zcode-session-delete-is-soft-delete-two-dbs.md) — 状态在 tasks-index、正文在 cli/db 无删除标记
- [数模论文图与摘要视觉基线](tools/mathmodel-paper-visual-baseline.md) — 高级图型清单、rcParams 固化、摘要按方法→数值
- [stdio MCP 安装验收法](tools/mcp-stdio-install-smoke-test.md) — 装前必实测 initialize+tools/list
- [MCP 有没有用看 handler 返回什么](tools/mcp-prompt-template-servers-add-no-capability.md) — 别读 description 宣称，读 handler 返回什么
- [CNB 密钥库与 imports 引用](tools/cnb-secret-repo-imports.md) — 密钥库拒一切令牌；.cnb.yml 顶层键须是分支名
- [OpenClaw typed hook 目录](tools/openclaw-hook-catalog.md) — 拦工具调用叫 before_tool_call
- [present_files 传 URL 即开侧栏浏览器](tools/workbuddy-present-files-url-opens-sidebar-browser.md) — URL→侧栏浏览器、本地 .html→预览面板
- [无 sourcemap 时复原前端 bundle 全量与 API 面](tools/frontend-bundle-recovery-without-sourcemap.md) — 入口只有 runtime 别判失败；对齐 chunk 清单
- [出版级中文配图：HTML/CSS 卡片 + 无头浏览器元素截图](tools/html-playwright-figure-pipeline.md) — 设计型中文图别用 matplotlib/AI 生图
- [html-to-docx 在 Windows 的 venv 布局坑](tools/html-to-docx-windows-venv-layout.md) — 插件按 bin/python 判，uv 建 Scripts/ ⇒ 反复重建
- [electron-builder NSIS 静默安装兜底](tools/electron-builder-nsis-silent-install-fallback.md) — /D 必崩、/S 会崩；须 7z 解包 + pylnk3 建快捷方式

## 条目格式


```markdown
---
name: kebab-case-slug
description: 一句话摘要（检索靠它）
type: tool | workflow | pitfall
source: 来源项目或事件
date: YYYY-MM-DD
verified: YYYY-MM-DD
---

**经验**：直接说怎么做。
**Why**：（可选）不这样做会怎样。
**How to apply**：（可选）什么场景、如何应用。
```
