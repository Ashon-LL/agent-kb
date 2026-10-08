# 全局经验库索引（kb）

> 一事实一文件；收录标准=跨项目可复用（项目专属留在项目 memory）。
> 目录：`tools/` 工具链 · `workflow/` 流程协作 · `pitfalls/` 失败教训

## pitfalls/ 教训与反模式
- [上游排队错误必须 429 而非硬 403](pitfalls/upstream-queue-error-must-be-429-not-hard-403.md) — 排队先切号试遍、全号耗尽才 429+Retry-After；⛔错误常在 200 建流的 SSE 信封里不在 HTTP 层
- [配置为空 ≠ 功能没做（空值常是正解）](pitfalls/empty-config-is-not-missing-feature.md) — 判断能力是否启用要读实现+实测产出；trae 设备隔离按账号 sha256 派生，填死 env 反而关掉换设备脱困；撞风控先分设备维度 vs 时段维度
- [每日奖励要找「调度器→回调→端点」三级链](pitfalls/daily-reward-need-scheduler-to-endpoint-chain.md) — 「桌面端启动自动调 X」≠X 是发放源（推广活动幂等 claim vs 账号服务 init-app，连日 Δ0 才发现）；奖励脚本必须记余额 delta
- [tool_choice 形态可能只收字符串 + 客户端参数错误不冷却账号池](pitfalls/gateway-tool-choice-string-only-and-no-cooldown-on-client-errors.md) — ⛔上游只收字符串 tool_choice（对象形态/max_tokens>65536/空arguments 三触发点=param invalid）；客户端形状错误绝不冷却整池；隔离参数用绕开账号池的上游直发矩阵
- [多账号领取的「按人去重」会把第二号活动隐藏](pitfalls/multi-account-claim-per-person-dedup-hides-second-account.md) — 列表缺失≠无此活动；直接 claim 幂等兜底；别拿缓存字段下「没得领」结论
- [账号池 credit-priority 必须服务账号=计费账号贯穿](pitfalls/pool-credit-priority-keep-serving-and-billing-account-tied.md) — 选号贯穿转发/上报/刷新；验证看余额差落谁家；无余额信号退化为健康轮询
- [划界看调用方而非文件位置](pitfalls/classify-by-consumer-not-by-file-location.md) — 同一文件常混着多方共用件；「住在哪」不等于「属于谁」，re-export 转发层尤甚
- [测量前先自检对照组与测量层](pitfalls/measurement-must-verify-control-group.md) — 对照组选「改动前真实状态」而非「本来就正常的状态」；GPU/合成开销主线程测不到；测试抓到错≠机制在生效
- [批量删除前必须逐包核实反向依赖](pitfalls/bulk-delete-requires-reverse-dep-check.md) — 删一个可执行文件 ≠ 删它所在目录；同目录兄弟包常被别的组件直接 import，删前逐个 grep
- [用户指令不是依赖已消失的证据](pitfalls/user-instruction-is-not-evidence-of-no-dependency.md) — 「删掉 X」只定义目标，X 是否还有人用要去查；验证到矛盾时当场报告而非硬办
- [「同步/都要最新」≠发版](pitfalls/sync-latest-is-not-a-release.md) — 动作上限=对齐到最新即停；bump/重建/tag 必须用户明说才做（动作不得升格）
- [桌面应用积分反代走结算上报端点](pitfalls/desktop-app-points-reverse-proxy-via-usage-report.md) — 聊天不扣分，扣分在独立 usage-report 结算端点；从客户端 outbox 拿真实 schema，UUIDv7 报告字段严格校验
- [模型换名漏同步会丢掉能力声明](pitfalls/model-rename-without-rule-sync-loses-capabilities.md) — 换名只改清单不改规则 ⇒ supportsToolCall 归默认 false ⇒ 工具调用退化成正文；三处同步 + 反证先行

- [fail-open 的 except 会吞调用方类型错误](pitfalls/fail-open-except-swallows-caller-type-errors.md) — 宽 except 把 AttributeError 归到「环境读不出」，真故障变静默跳过；入口 Path() 归一 + except 收窄
- [运行态异常也可能是用户造成的](pitfalls/runtime-anomalies-may-be-operator-actions.md) — 进程没了/端口空着/文件变了先想「是不是用户自己关的改的」；叙述去定性、恢复态动作先问；先查人为操作再查故障
- [出处要分「事实/推断/未见记录」三档](pitfalls/stated-provenance-needs-evidence-and-conditions.md) — 没找到记录≠不存在；4 样本编不出 P90；来源一致≠条件成立；「统一/全部」类词必须逐项复核
- [「以为在做」与「做了」要分开报](pitfalls/report-what-you-did-not-what-you-meant-to-do.md) — 后台/自动化尤其易犯：创建成功≠进程存活；说「已生效」前必须另起一次独立验证；错误的监控声明比没监控更糟
- [最小面原则会退化成「发现了但不修」](pitfalls/minimal-change-degenerates-into-skipping-real-bugs.md) — 最小面是「先修哪个」的规则，不是「能不能不修」的许可；复算见红要先分「真缺陷 vs 用例自身问题」两种都修
- [并行测试必须先隔离「会写仓库工作树的用例」](pitfalls/parallel-test-run-must-isolate-repo-mutators.md) — 会写工作树的用例独占跑；-n 别进 addopts
- [动态工作流的子代理身份与门禁三坑](pitfalls/dynamic-workflow-agent-identity-and-gates.md) — 循环内建 agent 撞重名；门禁先清被拦对象
- [CreateWorkflow 提交 cwd 漂移与 amend 重名追加](pitfalls/zcode-workflow-cwd-drift-and-amend-same-name.md) — 提交前 cd 漂移把 run 的 workspace 根带歪（draft/artifact 相对解析全错）；同名 agent 追加任务须复用引用而非再 agent()
- [Tauri 自定义命令的 ACL 三处一致](pitfalls/tauri-app-command-acl-three-places.md) — 命令名须同现三处 ACL，缺一静默失效
- [校验器 `continue` 掉缺项 = 门禁全绿地漏检](pitfalls/silent-continue-masks-lost-check-coverage.md) — 缺项 continue ⇒ 校验被跳过、门禁仍全绿
- [New API rc.26 渠道 CRUD 端点形状](pitfalls/newapi-rc26-channel-crud-shapes.md) — body 包 mode、删走路径参、option 非字典
- [New API rc.26 令牌 CRUD 三坑](pitfalls/newapi-rc26-token-crud-shapes.md) — key 在响应里、列表是掩码、DELETE 恒失败
- [New API model_limits 列是 CSV 不是 JSON](pitfalls/newapi-model-limits-column-is-csv-not-json.md) — 写 JSON 数组⇒该令牌全模型 403；SQL 改完必重启
- [Tauri Linux CI 需 webkit2gtk-4.1，无 Ubuntu 镜像](pitfalls/tauri-linux-ci-needs-webkit-41-and-target-override.md) — 无 Ubuntu 镜像；本机只编 Windows 目标
- [GitHub PR 表单是 details 折叠开关](pitfalls/github-pr-form-is-a-details-disclosure.md) — 大按钮非导航；用原生 setter+requestSubmit
- [孤儿常量与导入期告警不是阻塞项](pitfalls/orphan-constants-and-import-warnings-are-not-blockers.md) — 判阻塞先 grep 使用点；只有终点可观测物算证据
- [读-改-写全量 PUT 事故家族](pitfalls/redacted-get-full-put-wipes-secrets.md) — GET 脱敏/结构判错/白名单拒收四类静默事故；option 写操作六步铁律（留档→normalize→合并→PUT→回读全表→实测）
- [脱敏必须按键名判定并做负向自测](pitfalls/redaction-must-key-on-field-not-value.md) — 掩码判值不判键、行首锚定漏注释行，密钥静默裸奔；自测=断言输出不含已知密钥
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
- [docker compose config 会打印全部 env 真值](pitfalls/docker-compose-config-expands-secrets.md) — 含密钥的 compose 上用 config 校验=把 token/key 打进终端/日志；用 -q 或改看 ss -tlnp / docker inspect
- [测性能前清续跑锚点](pitfalls/clear-resume-anchors-before-benchmark.md) — 测墙钟前先清续跑锚点，否则只测到收尾
- [docx 管线交付坑](pitfalls/docx-pipeline-delivery-gotchas.md) — Word 重存丢字号、draw.io 0 字节导出
- [OOXML 排版属性四类静默失效](pitfalls/ooxml-layout-attributes-silently-ignored.md) — *Chars 覆盖磅值、exact 行距裁图、重存丢 tblW
- [图-引用距离与图例遮挡](pitfalls/figure-placement-and-legend-occlusion.md) — 几何自检只判出界不判遮挡；图须紧邻引用句不跨页
- [自动化"在跑"要查两件事](pitfalls/automation-artifacts-lie-existence-and-freshness.md) — 存在性与新鲜度须双层独立检查
- [日志字面语义不是规格](pitfalls/log-text-is-not-spec-read-emitting-code.md) — 先 grep 发提示语的代码；汇报分三档
- [shell 初始化文件是分层的](pitfalls/shell-init-files-are-layered-not-one.md) — 登录/交互/ssh命令执行三者读不同文件，只改一处会出现"同一台机器两个版本"；脚本用绝对路径
- [配置字段名不是规格](pitfalls/config-field-name-is-not-spec-read-consuming-code.md) — 名字像的字段各管一件事、改错无报错；读消费方代码
- [自定义 LLM 端点能力默认全关](pitfalls/custom-llm-endpoint-capabilities-default-false.md) — 认不出的端点按「未知兼容端点」处理，`supportsTools` 默认 false ⇒ 不发 tools ⇒ 工具调用退化成正文；显式声明 + 反证 + 看真实配置文件
- [覆盖式配置会丢掉隐式兜底](pitfalls/override-config-drops-implicit-fallbacks.md) — --config 驱动会丢向导默认；依赖能力须显式声明
- [多主人 config 必须读-合并-写](pitfalls/shared-config-multi-owner-merge-write.md) — 多写入者 config 全量覆盖会抹掉别人的键；读-合并-写
- [思考型模型 max_tokens 共用预算](pitfalls/reasoning-model-max-tokens-shares-budget.md) — 与正文共用 max_tokens；吃满时无 content 键
- [LLM 上下文窗口 = 输入 + 请求的 max_tokens](pitfalls/llm-context-window-is-input-plus-output.md) — 【作用域=AstrBot tdp+qwen3.8-27b】超窗先 400
- [kb 条目的 source 就是作用域边界](pitfalls/kb-entry-source-scope-is-the-boundary.md) — 检索命中≠该用；作用域标记写进 description
- [DETACHED_PROCESS 会引发黑窗风暴](pitfalls/detached-process-causes-console-window-storm.md) — 与 CREATE_NO_WINDOW 互斥，改用 NO_WINDOW
- [强规范对象别自造编码器](pitfalls/dont-handroll-spec-encoders-use-libraries-plus-fallback.md) — QR/条码/PDF 别自造编码器（错得静默）
- [测试的扫描范围/前提/断言三类假单](pitfalls/test-scope-must-be-pinned-by-index-not-walk.md) — 范围用 git ls-files；断言放宽分支是假绿
- [禁止讨好式确认开场](pitfalls/no-sycophantic-agreement-openers.md) — 删讨好开场；被纠正=认领+修正+干活
- [跟进 agent 循环看进展不看动静](pitfalls/agent-loop-follow-progress-not-liveness.md) — 同错×N+零交付判不收敛；守望须设时限
- [New API base_url 不能带 /v1](pitfalls/newapi-base-url-never-carry-v1.md) — 带了变 /v1/v1 报 404；全绿证不了 base_url
- [New API 多密钥 size 必须跟段数](pitfalls/newapi-multikey-size-must-track-key-count.md) — ⛔追加 key 不改 size⇒新钥当后缀；**10-08 起加钥首选原生 PUT**（GET 掩码→回填真钥→禁带 status→自动重建 size/BLOB→免重启）
- [台账核对必须双向](pitfalls/ledger-audit-must-be-bidirectional.md) — 只跑单向会漏整类问题；库里有值≠线上在用
- [待办台账会腐烂，开单前先复核](pitfalls/backlog-records-rot-verify-before-dispatch.md) — 未做≠还没做，按机制复核；实测 6/6 已闭环
- [同名配置键在不同步骤类型下语义不同](pitfalls/same-config-key-different-semantics-per-step-type.md) — 脚本 Job=总时长超时，npc:go=单次执行
- [New API 禁用渠道/改分组都要重建 abilities](pitfalls/newapi-disable-must-sync-abilities.md) — abilities 是唯一路由事实源；须手工重建+回读
- [产出端与消费端状态不匹配会静默空转](pitfalls/producer-consumer-status-mismatch-silently-noops.md) — 产出写 candidate、消费只查 active ⇒ 空转
- [容器镜像内源码补丁必须配重放脚本](pitfalls/container-image-source-patches-need-replay-script.md) — 扛 restart 不扛 rm/升级；须配幂等重放脚本
- [第三方应用 DB 列格式由读它的代码决定](pitfalls/third-party-db-columns-typed-by-reading-code.md) — 弱类型收得下≠读得动；一行类型不符可整表查询失败
- [手写 ECDSA 要拒 r==s 而不只 r==0/s==0](pitfalls/ecdsa-raw-signature-must-reject-r-equals-s.md) — 漏判则直接返回坏签名；偶发 InvalidSignature 不是 flaky
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
- [CI status=success 可能两 job 全 skipped](pitfalls/ci-status-success-can-be-fake-when-jobs-skipped.md) — ifModify 按需触发让 job 跳过仍报 success；判绿必须看 stages 不看顶层 status
- [手册/文档命令必须核消费代码](pitfalls/handbook-commands-must-verify-consuming-code.md) — API 用法凭记忆写 3 处错（KeyError/参数被静默忽略/凭据进日志）；核返回结构+参数契约键+出处行号
- [守卫必须覆盖改动那一层](pitfalls/guard-must-cover-the-changed-layer.md) — Python 守卫 + Rust 改动 = 没有守卫；加守卫问"扫的层和改动的层是同一层吗"
- [消融实验必须自证改到了](pitfalls/ablation-must-self-verify-change-applied.md) — 连续测错三次静默产出假数字；判据是计算后取值不是调用动作；根修=单页轮转+颠倒顺序+单对象传参+硬闸
- [别给边缘功能开战线](pitfalls/dont-open-frontline-for-edge-features.md) — 本来没坏只是不通→四层管线 40 分钟净零；改前先问挡不挡主线；降级路径已干净=完成态不是待办
- [盘点/逆向的两类搜索假阴性](pitfalls/survey-false-negatives-substring-and-enumeration.md) — 子串误命中当结论 + 枚举前缀即边界；否定结论须能说清枚举集合怎么来的
- [安全探针假阳性三防](pitfalls/leak-probe-false-positive-three-guards.md) — 关键词命中拒绝话术当泄露；报 LEAK 前须看原文+设对照组+复现；判定式分语义不分子串
- [数字/配置张口就来的三类错](pitfalls/quantity-and-config-claim-three-errors.md) — 量纲错配/作用域错/归属没查；"字段缺失"不能推出"功能关闭"；统计口径也要写明
- [凭据原文不进记忆/kb/日志](pitfalls/credentials-never-in-memory-or-logs.md) — 只记取值位置不记取值；装凭据走管道不 echo；脱敏用整体替换非只遮尾巴
- [kb 事故三层教训](pitfalls/kb-accident-three-layer-lessons.md) — 改运行中应用扩展点路径会全废；多个同名近似物先摊开地图；用户连问两次基础问题先停下讲清楚
- [摘要行限定词必须带作用域](pitfalls/summary-scope-qualifiers-must-be-explicit.md) — 不带作用域单读反向；别给通用规律乱加作用域标记；别用代理指标判定检查坏没坏
- [ssh here-doc 定界符必须加引号](pitfalls/ssh-heredoc-delimiter-must-be-quoted.md) — 未加引号时远端 $VAR 被本地 shell 提前展开成空串；跨 shell 边界送脚本一律 <<'EOF'
- [管道子 shell 会吞掉退出码](pitfalls/pipeline-subshell-swallows-exit-code.md) — cmd | tee 里 exit 1 不传播，systemd/CI 把失败报成成功；主体包函数用 return + PIPESTATUS[0]
- [容器 /tmp 与宿主 /tmp 不是同一个](pitfalls/container-host-file-and-exec-boundary.md) — 跨边界产物要 docker cp；stop 后 exec 直接失败，改容器 DB 走 bind-mount 宿主路径
- [TOML 双引号内嵌双引号会提前闭合](pitfalls/toml-double-quote-nesting.md) — tomllib 报 Expected newline 且行号指向语句起点；改写措辞或用单引号串
- [scope 白名单硬编码时加 key 无效](pitfalls/scope-whitelist-hardcoded-switch-auth-path.md) — 403 insufficient scope 先查源码白名单；同端点换认证路径做 A/B，走 JWT/会话取全权
- [vite 产物名与 scope id 随源码行尾全图变化](pitfalls/vite-build-output-names-track-source-eol.md) — CRLF↔LF 改 data-v-* 再级联改全部 chunk 哈希名；git 归一看不见；对拍勿误判「构建过期」
- [「只有浏览器成功」先查凭据失效再谈 TLS 指纹](pitfalls/browser-only-success-check-credential-first.md) — 同一 token 浏览器 200、curl/python/TLS伪装全 401 ⇒ 先页内裸 token 复测+指纹比对+新鲜凭据重放；实测真因=改密码吊销+cookie 轮换，WAF 假设是死凭据喂出来的
- [ZCode provider_config 的 group 只收 standard-personal](pitfalls/zcode-provider-config-group-enum-standard-personal.md) — config.group 是内部枚举，写成站点组名整份配置拒载、UI 全空；站点分组隔离靠令牌；排障走 [provider-config] 日志 ZodError path
- [新增宿主网关端口先放行白名单再固化开机重放](pitfalls/host-gateway-port-allowlist-before-relay-onboarding.md) — 绑网桥 IP 的服务白名单外被静默 DROP：直连 200、经容器网关 i/o timeout；iptables 一次性规则重启即丢，必须写进维护链的开机脚本

## workflow/ 流程与协作

- [跨工具技能目录语义各异](workflow/cross-agent-skill-dir-semantics.md) — ~/.agents/skills 是共享约定但支持不一；各工具装法跟着语义走；装前先看本机惯例再搜文档，未实测不断言
- [接手半途任务先 diff 部署面与版本面](workflow/diff-deployed-vs-vcs-before-reimplementing.md) — 新实现常写在部署目录没回流仓库；找到现成版做回流别重写，丢注释里的踩坑修正是重写最大代价
- [多工具共享脚本用硬链接统一](workflow/hardlink-unify-shared-scripts-across-tools.md) — 留一个真相源其余同 inode；git 会断链，校验器按内容兜底；改配置指向换不掉副本漂移
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

- [决策理由落 ADR 而非 PR 描述/代码史书](workflow/adr-over-pr-description-and-code-history.md) — 优先级 ADR>代码注释>PR 描述；PR 描述随时间失上下文，注释写史书会污染代码
- [两个 Agent 分工迭代：用派活板代替人工转述](workflow/two-agent-iteration-via-dispatch-board.md) — 待办/进行中/已完成三区 + 维护约定；「已完成」表要带维护者复算结论而不只是自报；派活书别写约束清单（会把对方框死）
- [用户指令覆盖一切默认纪律](workflow/user-authority-overrides-default-discipline.md) — 存疑一句话报告后照做；不许为门禁变绿回退用户指令；"我知A用户说反B"=读错上下文
- [禁令类结论需二次确认](workflow/prohibitions-need-second-confirmation.md) — 禁令说错会静默阻止正确行动；"事实+条件+规避"优于"⛔别做"；措辞不得比原文宽
- [提问当场给多选项不拖到收尾](workflow/ask-with-options-early-never-at-end.md) — 开放式文字问+末尾抛=让用户在已完成动作后才发现要决策；"我真服了你了"=别解释直接给选项或动手
- [两个 Agent 互相等=死锁](workflow/two-agents-waiting-on-each-other-is-deadlock.md) — 给明确到无解释空间的下一步；判"在等"看会话文件 mtime+writerOccupied+无待发指令三条同时成立
- [破坏性动作必须显式报告](workflow/destructive-actions-must-be-reported-explicitly.md) — 杀进程/覆盖文件在回复开头明说；"✅已应用"不能掩盖副作用；"打算做"必须先问哪怕看起来有益
- [先理清全局给计划再动手](workflow/plan-before-acting-and-verify-before-claiming.md) — 外发/破坏动作前报状态等确认；声称完成必须附验证证据；入口/通道/模式三类使用方式要直接问别假设
- [别把待决定项包装成已定](workflow/never-pad-reports-with-desired-state.md) — 成果汇报只放已发生的事；需要拍板当场摆多选项独立成段；工具债是自己收拾不是塞给对方
- [工作流是探针不是目的](workflow/workflow-is-a-probe-not-the-goal.md) — 问题充分取证就转派单修，比硬跑完更有价值；门禁没落地别续跑；"双线跟进"=两线互相把控
- [动手前先只读盘点现状](workflow/survey-before-acting-on-own-project.md) — 连续迭代自有项目功能常早已存在；先列"已有什么vs缺什么"再决定动什么；连续踩墙2次→回到只读盘点
- [关掉某个对象时优先最小作用域原生开关](workflow/prefer-narrow-native-switch-over-broad-global-or-plugin.md) — 逐对象状态机 → prompt 软约束 → 全局开关 → 自写插件，找到第一档就停；全局 allow-list 会误伤

## tools/ 环境与平台

- [WSL 里的 Docker 按需启动（不装 Desktop）](tools/wsl-docker-on-demand-startup.md) — Windows 侧无 docker 命令须 wsl.exe 转发带 MSYS_NO_PATHCONV；关自启后按需启走 -u root；"装好却跑不了"=用户不在 docker 组
- [Git Bash 的 `&` 会拆掉 gh auth login 参数](tools/git-bash-ampersand-breaks-gh-auth-login.md) — 管道送 stdin；Fine-grained 全选=完全权限但删不了库
- [GitHub 大陆双向通路（下载+推送）](tools/github-china-network-workarounds.md) — 下载用 jsdelivr/curl 续传；推送须探测+hosts 一体；`github-push-ip-retry.py` DoH 源已扩（阿里/腾讯×2 + UDP 电信/联通/百度/360/CNNIC，2026-10-06 实测国外 DoH 被墙）
- [git 传输死时走 Git Data API 构造提交](tools/github-git-data-api-push-without-git-transport.md) — 零 git 二进制建分支推提交；须本地 SHA1 预验证
- [细粒度 PAT 缺 PR 写权限 → 403](tools/github-fine-grained-pat-pr-write-403.md) — 能推≠能开 PR；先 GET /pulls 分辨权限 vs 不存在
- [直连云环境里的 AI Agent（CNB 工作区）](tools/cnb-workspace-agent-direct-channel.md) — 附**可执行脚本** `tools/cnb-workspace-agent-cli.py`（reply/history/sessions/keepalive/**watch**） — SSH 进容器 + `POST :8688/api/v1/sessions/{id}/reply` 发消息（⛔ 必带 `x-codebuddy-request: 1`）；顺带解掉「容器无心跳 10 分钟即被回收」；附「工作区 start 不能指定模型」「Dockerfile 构建期无 git 凭据」等 4 条相邻事实
- [CNB NPC 派单要点](tools/cnb-npc-dispatch-essentials.md) — 大任务书走 argv 会截断；workMode 嵌 npc 内
- [CNB token 用量统计方法](tools/cnb-token-usage-audit.md) — 正解=逐构建 get-build-ai-audit 累加；credit 是额度≠token（免费期 0 credit 照记 token）；charge_type_token 是平台 bug；截止时刻默认北京时间
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
- [NPC 迭代：把红的原文回传](tools/npc-iterate-by-sending-failure-text-back.md) — 别自己改；给断言原文+失败行+期望语义；既有用例回归单标必修
- [Windows 用户目录清理：可删的 vs 陷阱](tools/windows-home-cleanup-safe-vs-traps.md) — `*updater*`/缓存/解包暂存可删；⛔ `%APPDATA%\npm` 是全局 CLI 入口不是缓存；孤儿 MSI 记录单清
- [ESP32 编译烧录链路（本机 arduino-cli）](tools/esp32-arduino-cli-flash-workflow.md) — 工具链落点 + FQBN 必带 huge_app + sketch 目录同名硬约束 + ELF 体积分析法；附 GFX/ST7789 三坑与"参考图别手绘"

## 条目格式


```markdown
---
name: kebab-case-slug
description: 一句话摘要（检索靠它）
type: tool | workflow | pitfall
source: 来源项目或事件
date: YYYY-MM-DD
verified: YYYY-MM-DD
topic: 受控词表之一（见 kb 技能）
---

**经验**：直接说怎么做。
**Why**：（可选）不这样做会怎样。
**How to apply**：（可选）什么场景、如何应用。
```
- [上游排队类错误先查社区实现再发明等待机制](pitfalls/upstream-queue-blind-wait-backfires.md) — 排队≠时间窗，盲等把快速失败变超长挂起；同类项目早有 queue-poll/串行化/不惩罚账号的答案
