# 全局经验库索引（kb）

> 一事实一文件；收录标准=跨项目可复用（项目专属留在项目 memory）。
> 目录：`tools/` 工具链 · `workflow/` 流程协作 · `pitfalls/` 失败教训

## pitfalls/ 教训与反模式
- [「空闲回收」判据必须是「有没有事在做」不是「有没有人在看」](pitfalls/idle-reclaim-criteria-must-be-work-not-attention.md) — 无人值守/自动化场景下 UI 状态判据**结构上失效**（实测订阅事件 0 条 vs 正常时段 3 条/次）；先枚举进程所有「活着」的形态再定判据，优先用对端主动推的心跳/通知（与谁在场无关）；挂点选记录构造处 + try/catch + 宽限窗口；★阈值和判据是两件事，修误杀只改判据、不顺手拉长用户阈值
- [成品包补丁锚点要内容寻址，别写死文件名/变量名](pitfalls/patch-pipeline-content-addressing-beats-filename-anchors.md) — 压缩名每代全换（实测三代文件名/类名/函数名整体漂移）；内容寻址的收益可量化：新版 27,995 条目只 1 针失配、其余零适配直接出包；★配套要求＝桩测试动态解析绑定名，否则版本改名后测试静默失真（17 个假 FAIL 而产品完全正确）；引用原名用正则取回不复制；任何测试失败先怀疑桩
- [图件必须做渲染前几何自检（并按图元类型分级判据）](pitfalls/matplotlib-figure-geometry-selfcheck.md) — 图例压柱/注释压柱/出画布只有 bbox 几何量可靠；三层根因：避让写在 continue 之后、漏 `ax.patches`、`Annotation.get_window_extent` 含箭头 ⇒ 取 `Text` 基类 bbox；内边距按 `borderaxespad×fontsize×dpi/72`、抬 ylim 造留白须设增幅上限、柱内数值标签豁免要含水平居中、布局守卫后要再避让一次；门禁须临时副本+随附工具库，正例 0 违规且负例必须能拦住
- [CNB NPC 派单：@地址/配置源/timeout 不是会话上限](pitfalls/cnb-npc-dispatch-channel-config-and-time-caps.md) — 裸 `@角色` 不产生事件（必须 `@<NPC仓>(<角色>)`+`--work-mode`，CLI 评论 2 秒建 pipeline）；评论事件配置源在 **NPC 仓** `.cnb.yml`（改机型/轮次要改 fork）；`timeout` 只管单次工具执行、实测 2h01m 被 SIGKILL（声明 6h 无效）；`strings 日志 grep =7200000` 会命中自己注释文本、真实值 `<masked>`；长任务靠增量推送兜底
- [注入式 UI 增强失效先查「取凭据/取上下文」段](pitfalls/injected-ui-feature-failure-check-credential-plumbing-first.md) — 引擎/锚点/桥全在也可能是 gate 前那几行把 Key 拿不到就静默 return；判据＝桩 DOM 跑真块 A/B（调用次数）；打包应用主 chunk grep testid 0 命中是正常（lazy chunk + 常量压缩）；修法＝复用已桥接通道多路复用 + 主进程按 id 读明文配置兜底
- [JOSE 定长 r‖s 转 DER 必须剥前导零](pitfalls/jose-raw-sig-to-der-must-strip-leading-zero.md) — DER 要求最小编码；首字节为 0 时被 OpenSSL/cryptography 拒签，伪装成「签名器 10% 随机失败」；先统计失败样本特征再怀疑 nonce
- [错误日志归因按 baseURL 判线，模型名会重名](pitfalls/multi-line-log-attribution-use-baseurl-not-model.md) — ZCode model.* 事件归属字段在 context.baseURL；导出 txt 丢 baseURL，须回原始 jsonl 聚合
- [上游排队错误必须 429 而非硬 403](pitfalls/upstream-queue-error-must-be-429-not-hard-403.md) — 排队先切号试遍、全号耗尽才 429+Retry-After；⛔错误常在 200 建流的 SSE 信封里不在 HTTP 层
- [配置为空 ≠ 功能没做（空值常是正解）](pitfalls/empty-config-is-not-missing-feature.md) — 判断能力是否启用要读实现+实测产出；trae 设备隔离按账号 sha256 派生，填死 env 反而关掉换设备脱困；⛔**同一项目的多条「设备」路径要分开读**（trae：签到=按号派生 / 聊天=上游自带的进程级轮换伪设备）——先与上游源码 diff 再断言；撞风控先分设备维度 vs 时段维度
- [每日奖励要找「调度器→回调→端点」三级链](pitfalls/daily-reward-need-scheduler-to-endpoint-chain.md) — 「桌面端启动自动调 X」≠X 是发放源（推广活动幂等 claim vs 账号服务 init-app，连日 Δ0 才发现）；奖励脚本必须记余额 delta
- [tool_choice 形态可能只收字符串 + 客户端参数错误不冷却账号池](pitfalls/gateway-tool-choice-string-only-and-no-cooldown-on-client-errors.md) — ⛔上游只收字符串 tool_choice（对象形态/max_tokens>65536/空arguments 三触发点=param invalid）；客户端形状错误绝不冷却整池；隔离参数用绕开账号池的上游直发矩阵
- [伪装客户端门禁的占位工具必须合并不能替换](pitfalls/disguised-client-gate-needs-placeholder-tools-merged-not-replaced.md) — 免费档按模型要求 bash/read 占位工具在场；客户端带 tools 时整表替换⇒该族全 403/502（纯聊正常、agent 模式挂）；逐模型跑「真实工具/占位+真实」对照，探针别用 1×1 退化图
- [多账号领取的「按人去重」会把第二号活动隐藏](pitfalls/multi-account-claim-per-person-dedup-hides-second-account.md) — 列表缺失≠无此活动；直接 claim 幂等兜底；别拿缓存字段下「没得领」结论
- [账号池 credit-priority 必须服务账号=计费账号贯穿](pitfalls/pool-credit-priority-keep-serving-and-billing-account-tied.md) — 选号贯穿转发/上报/刷新；验证看余额差落谁家；无余额信号退化为健康轮询
- [划界看调用方而非文件位置](pitfalls/classify-by-consumer-not-by-file-location.md) — 同一文件常混着多方共用件；「住在哪」不等于「属于谁」，re-export 转发层尤甚
- [测量前先自检对照组与测量层](pitfalls/measurement-must-verify-control-group.md) — 对照组选「改动前真实状态」而非「本来就正常的状态」；GPU/合成开销主线程测不到；测试抓到错≠机制在生效
- [对平台能力零实测就零断言](pitfalls/no-assertion-without-measurement.md) — 别臆测/想当然/凭记忆下结论；口头陈述是线索不是定论；先看本机先例再搜文档，用户纠正后最小修正；症状词：搞错、又错、越做越错
- [批量删除前必须逐包核实反向依赖](pitfalls/bulk-delete-requires-reverse-dep-check.md) — 删一个可执行文件 ≠ 删它所在目录；同目录兄弟包常被别的组件直接 import，删前逐个 grep
- [用户指令不是依赖已消失的证据](pitfalls/user-instruction-is-not-evidence-of-no-dependency.md) — 「删掉 X」只定义目标，X 是否还有人用要去查；验证到矛盾时当场报告而非硬办
- [「同步/都要最新」≠发版](pitfalls/sync-latest-is-not-a-release.md) — 动作上限=对齐到最新即停；bump/重建/tag 必须用户明说才做（动作不得升格）
- [桌面应用积分反代走结算上报端点](pitfalls/desktop-app-points-reverse-proxy-via-usage-report.md) — 聊天不扣分，扣分在独立 usage-report 结算端点；从客户端 outbox 拿真实 schema，UUIDv7 报告字段严格校验；同账号多网关权益面各自漂移（/v1 403、/v2 200 都正常），可用性按需复测别拿一次快照当永久事实
- [模型换名漏同步会丢掉能力声明](pitfalls/model-rename-without-rule-sync-loses-capabilities.md) — 换名只改清单不改规则 ⇒ supportsToolCall 归默认 false ⇒ 工具调用退化成正文；三处同步 + 反证先行

- [邮件 HTML 对齐必须内联 + 块居中要用属性，不能只靠 <style>](pitfalls/email-html-alignment-must-be-inline.md) — 剥 <style> 后 `th` 默认居中、数字列被右对齐 ⇒ 「只有部分列跑偏」；**块居中与格内左对齐是两件事**：居中用 `td align=center`/`table align=center`+`cellpadding` 属性（零副作用），对齐逐格内联；验收=剥掉样式后用无头浏览器截图 + 断言每个单元格都带内联对齐
- [聚合报表缺失值必须先判类型再运算](pitfalls/aggregate-report-missing-values-must-be-none-guarded.md) — 任一源都可能返回 None：做差/求和前 `isinstance` 两边都判，缺失渲染成 `—`/`n/a`；这类崩溃是**间歇**的（同脚本同天早上成功、手动重跑就炸）⇒ 一次成功不等于健壮
- [用户给的「相等」必须原样落成同值](pitfalls/user-given-equalities-must-stay-equal.md) — 排序里的 `=` 是并列意图：等号组落成同值 + 同档只用 `‖`（`>`/`→` 仅跨档）；把同档内的权重差异写成先后 = 「没看懂输入」；非榜单对象照给值但明说是我给的
- [fail-open 的 except 会吞调用方类型错误](pitfalls/fail-open-except-swallows-caller-type-errors.md) — 宽 except 把 AttributeError 归到「环境读不出」，真故障变静默跳过；入口 Path() 归一 + except 收窄
- [运行态异常也可能是用户造成的](pitfalls/runtime-anomalies-may-be-operator-actions.md) — 进程没了/端口空着/文件变了先想「是不是用户自己关的改的」；叙述去定性、恢复态动作先问；先查人为操作再查故障
- [出处要分「事实/推断/未见记录」三档](pitfalls/stated-provenance-needs-evidence-and-conditions.md) — 没找到记录≠不存在；4 样本编不出 P90；来源一致≠条件成立；「统一/全部」类词必须逐项复核
- [「以为在做」与「做了」要分开报](pitfalls/report-what-you-did-not-what-you-meant-to-do.md) — 后台/自动化尤其易犯：创建成功≠进程存活；说「已生效」前必须另起一次独立验证；错误的监控声明比没监控更糟；症状词：我以为
- [最小面原则会退化成「发现了但不修」](pitfalls/minimal-change-degenerates-into-skipping-real-bugs.md) — 最小面是「先修哪个」的规则，不是「能不能不修」的许可；复算见红要先分「真缺陷 vs 用例自身问题」两种都修
- [并行测试必须先隔离「会写仓库工作树的用例」](pitfalls/parallel-test-run-must-isolate-repo-mutators.md) — 会写工作树的用例独占跑；-n 别进 addopts
- [跨环境传文件/凭据要走原生机制，别造明文副本](pitfalls/cross-env-file-handoff-must-use-native-mechanism.md) — Git Bash 的 /tmp 与 Windows Python 的 /tmp 不是同一个目录（⇒ FileNotFoundError）；真错是为传一个秘密在盘上造第二份明文；应让目标侧自己取（同进程内读+写）、用 load_secrets/tomllib 别手写解析、写完断言键存在+值非空并由实际使用方验证
- [动态工作流的子代理身份与门禁三坑](pitfalls/dynamic-workflow-agent-identity-and-gates.md) — 循环内建 agent 撞重名；门禁先清被拦对象
- [CreateWorkflow 提交 cwd 漂移与 amend 重名追加](pitfalls/zcode-workflow-cwd-drift-and-amend-same-name.md) — 提交前 cd 漂移把 run 的 workspace 根带歪（draft/artifact 相对解析全错）；同名 agent 追加任务须复用引用而非再 agent()
- [IMAP 管邮箱的夹名归一化与删除标记坑](pitfalls/imap-mailbox-ops-qq-folder-quirks.md) — 中文夹名被服务端归一化会建出两个同名夹（CREATE 返 OK 也要 LIST 回读点数）；删夹要夹内数为 0 而非仅标 \Deleted；COPY+标Deleted 邮件仍留在收件箱、要 EXPUNGE 才空箱；接收侧用 LIST 原始编码名 SELECT 别本地重编码；EXPUNGE 前逐封指纹比对副本
- [Tauri 自定义命令的 ACL 三处一致](pitfalls/tauri-app-command-acl-three-places.md) — 命令名须同现三处 ACL，缺一静默失效
- [校验器 `continue` 掉缺项 = 门禁全绿地漏检](pitfalls/silent-continue-masks-lost-check-coverage.md) — 缺项 continue ⇒ 校验被跳过、门禁仍全绿
- [New API rc.26 渠道 CRUD 端点形状](pitfalls/newapi-rc26-channel-crud-shapes.md) — body 包 mode（POST）/扁平 body（PUT 走 PATCH+GORM 非零字段：稀疏安全、清空不行、免重启）、删走路径参且硬删、option value 类型不稳定、摘模型要连死 mapping 键一起清
- [New API rc.26 令牌 CRUD 三坑](pitfalls/newapi-rc26-token-crud-shapes.md) — key 在响应里、列表是掩码、DELETE 恒失败
- [New API model_limits 列是 CSV 不是 JSON](pitfalls/newapi-model-limits-column-is-csv-not-json.md) — 写 JSON 数组⇒该令牌全模型 403；SQL 改完必重启
- [Tauri Linux CI 需 webkit2gtk-4.1，无 Ubuntu 镜像](pitfalls/tauri-linux-ci-needs-webkit-41-and-target-override.md) — 无 Ubuntu 镜像；本机只编 Windows 目标
- [GitHub PR 表单是 details 折叠开关](pitfalls/github-pr-form-is-a-details-disclosure.md) — 大按钮非导航；用原生 setter+requestSubmit
- [孤儿常量与导入期告警不是阻塞项](pitfalls/orphan-constants-and-import-warnings-are-not-blockers.md) — 9 条：判阻塞先 grep 使用点、只有终点可观测物算证据、附两层证据排障法（中间态 vs 终态）
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
- [Qoder Office pptx 图片管线故障与页内动画注入](pitfalls/qoder-office-pptx-image-and-animation-workarounds.md) — 12 条：带图 put_page 拆两步、动画 zip 注 timing、GIF 循环直替、字体须装 HKLM、slide rels 相对路径等
- [改 pptx 动画用 COM 原生接口，别手写 timing XML](pitfalls/pptx-anim-com-not-handwritten-xml.md) — 平铺 clickEffect 会退化成"点一次出一条"；COM TriggerType 2/3 让 PowerPoint 自己重写；12 条坑（Visible/Runs/HWND/AddEffect 重置 cond/清空再加重/Pulse 落点/关闭弹保存框用 ReadOnly=1）
- [裸 wait 会被常驻子进程永久阻塞](pitfalls/bare-wait-deadlocks-on-long-lived-children.md) — 裸 wait 被常驻子进程永久阻塞；兜底包整个脚本
- [空值 credential.helper 阻塞 git fetch，unset-all 误删好条目](pitfalls/credential-helper-empty-value-blocks-git-fetch.md) — 空值 helper 让 git 阻塞；unset-all 误删好条目
- [凭据管理器里的 host 级条目会抢先命中](pitfalls/credential-rotation-must-cover-all-entries.md) — host 级条目抢先命中；按库隔离挂专用 helper
- [docker compose config 会打印全部 env 真值](pitfalls/docker-compose-config-expands-secrets.md) — 含密钥的 compose 上用 config 校验=把 token/key 打进终端/日志；用 -q 或改看 ss -tlnp / docker inspect
- [测性能前清续跑锚点](pitfalls/clear-resume-anchors-before-benchmark.md) — 测墙钟前先清续跑锚点，否则只测到收尾
- [docx 管线交付坑](pitfalls/docx-pipeline-delivery-gotchas.md) — Word 重存丢字号、draw.io 0 字节导出
- [OOXML 排版属性四类静默失效](pitfalls/ooxml-layout-attributes-silently-ignored.md) — *Chars 覆盖磅值、exact 行距裁图、重存丢 tblW
- [图-引用距离与图例遮挡](pitfalls/figure-placement-and-legend-occlusion.md) — 几何自检只判出界不判遮挡；图须紧邻引用句不跨页
- [自动化"在跑"要查两件事](pitfalls/automation-artifacts-lie-existence-and-freshness.md) — 存在性与新鲜度须双层独立检查
- [日志字面语义不是规格](pitfalls/log-text-is-not-spec-read-emitting-code.md) — 先 grep 发提示语的代码；汇报分三档；目录清单/余额/状态字段都不等于能力（29 个模型实测 7 个 400；封禁号余额仍正常）——判可用只认真实调用
- [采集件必须「先落盘后统计」](pitfalls/collected-data-must-be-persisted-before-analysis.md) — ⛔ `collect();stats();dump()` 会把数据困在内存：实测 1.26M tokens 采集随 kill 归零；顺序铁律=采集→dump→push→统计，跑器归档进仓、分批增量落盘、统计特征预计算
- [pkill 的 pattern 会杀到承载它的 shell 自己](pitfalls/pkill-self-match-kills-own-shell.md) — `pkill -f "x"` 连带杀掉外层命令链：部分生效+后续静默丢失；先取 PID 再杀 / 方括号技巧 / 破坏性动作拆两次独立调用
- [本机 SSH 断 ≠ 云端任务死](pitfalls/local-ssh-fail-is-not-cloud-task-death.md) — 判完成看 git 远端新提交、判环境看平台 status/duration；心跳 FAIL 只说明本机通道断（实测：心跳 02:54 全 FAIL，容器内执行者一路干到 04:18 并全部完成归档）
- [把历史工作流导进 MH-Agent-Open 的三个必核点](workflow/importing-historical-runs-into-mh-agent-open.md) — ①先确认形态（桌面 `~/.MHAgentOpen` vs 容器 `/data`，导错=白干）②文件须在**契约声明位置**（工作区根，不是归档目录）③校验=按 output_files 逐个 test -f；缺件分「在别处」与「真丢了」，后者如实报不造空壳
- [shell 初始化文件是分层的](pitfalls/shell-init-files-are-layered-not-one.md) — 登录/交互/ssh命令执行三者读不同文件，只改一处会出现"同一台机器两个版本"；脚本用绝对路径；⛔Debian /etc/profile 会重置 PATH ⇒「登录壳报缺件」是假失败，须两种壳各验一次
- [配置字段名不是规格](pitfalls/config-field-name-is-not-spec-read-consuming-code.md) — 10 条：名字像的字段各管一事、声明式列表缺项会清掉无关能力、默认值在代码不在配置、UI 字段先证有消费者、反向验证能力
- [自定义 LLM 端点能力默认全关](pitfalls/custom-llm-endpoint-capabilities-default-false.md) — 认不出的端点按「未知兼容端点」处理，`supportsTools` 默认 false ⇒ 不发 tools ⇒ 工具调用退化成正文；显式声明 + 反证 + 看真实配置文件
- [模型能力判定要查官方文档，别靠探针](pitfalls/model-capability-verdict-needs-official-docs-not-probes.md) — 单张图/数点题会给假阳性（GLM-5.3/5.2 被探针判「有视觉」，官方=纯文本；Kimi K3 才原生多模态）；探针只作验收，官方口径 > 多家网关既有声明 > 单次探针
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
- [kb 检索无结果≠库里没有](pitfalls/kb-search-miss-is-not-kb-empty.md) — 检索失败≠对象不存在；症状词多轮+ls 目录+读 INDEX 三步；20261023 实测漏读 6 条直接相关
- [同名配置键在不同步骤类型下语义不同](pitfalls/same-config-key-different-semantics-per-step-type.md) — 脚本 Job=总时长+无输出超时，npc:go=单次工具执行；调大总时长会静默松掉 10min 无输出保护；症状词：卡住；真上限见 [CNB 2h 硬顶](tools/cnb-pipeline-2h-hard-cap.md)
- [守卫判据锚「写法」必被换写法绕过](pitfalls/guard-criteria-anchored-to-spelling-always-escape.md) — 四连逃逸实证；静态判结构、渲染占位交运行时几何门、变异集裁定强弱
- [fork 同步上游会静默覆盖本仓定制](pitfalls/fork-sync-force-update-wipes-local-customizations.md) — 同步=force update（重写历史）；定制行带标记+清单，同步后逐项 grep 复核再补回；⛔ 20261023 更正：apigogo/x 并未删除（20261019 已重建，实测带密钥 imports+4 核 runner）⇒ 现行派单入口 = @apigogo/x(中书令)；原理仍适用
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
- [Tauri 非 tauri:// 来源的 invoke 被 ACL 拦而非对象缺失](pitfalls/tauri-remote-url-has-no-ipc.md) — 坏的是 invoke 被 ACL 拒，非对象缺失；症状词：没反应
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
- [跨 shell 送文本的转义坑合集](pitfalls/ssh-heredoc-delimiter-must-be-quoted.md) — 定界符不加引号 `$VAR` 提前展开；`commit -m` 反引号被命令替换（消息静默变空且禁 force push 改不回）；多层嵌套引号断链⇒写文件再 scp；转义串锚点在两层解释器里错位⇒按行匹配
- [管道子 shell 会吞掉退出码](pitfalls/pipeline-subshell-swallows-exit-code.md) — cmd | tee 里 exit 1 不传播，systemd/CI 把失败报成成功；主体包函数用 return + PIPESTATUS[0]
- [容器 /tmp 与宿主 /tmp 不是同一个](pitfalls/container-host-file-and-exec-boundary.md) — 跨边界产物要 docker cp；stop 后 exec 直接失败，改容器 DB 走 bind-mount 宿主路径
- [TOML 双引号内嵌双引号会提前闭合](pitfalls/toml-double-quote-nesting.md) — tomllib 报 Expected newline 且行号指向语句起点；改写措辞或用单引号串
- [scope 白名单硬编码时加 key 无效](pitfalls/scope-whitelist-hardcoded-switch-auth-path.md) — 403 insufficient scope 先查源码白名单；同端点换认证路径做 A/B，走 JWT/会话取全权
- [vite 产物名与 scope id 随源码行尾全图变化](pitfalls/vite-build-output-names-track-source-eol.md) — CRLF↔LF 改 data-v-* 再级联改全部 chunk 哈希名；git 归一看不见；对拍勿误判「构建过期」
- [「只有浏览器成功」先查凭据失效再谈 TLS 指纹](pitfalls/browser-only-success-check-credential-first.md) — 同一 token 浏览器 200、curl/python/TLS伪装全 401 ⇒ 先页内裸 token 复测+指纹比对+新鲜凭据重放；实测真因=改密码吊销+cookie 轮换，WAF 假设是死凭据喂出来的
- [ZCode provider_config 的 group 只收 standard-personal](pitfalls/zcode-provider-config-group-enum-standard-personal.md) — config.group 是内部枚举，写成站点组名整份配置拒载、UI 全空；站点分组隔离靠令牌；排障走 [provider-config] 日志 ZodError path
- [新增宿主网关端口先放行白名单再固化开机重放](pitfalls/host-gateway-port-allowlist-before-relay-onboarding.md) — 绑网桥 IP 的服务白名单外被静默 DROP：直连 200、经容器网关 i/o timeout；iptables 一次性规则重启即丢，必须写进维护链的开机脚本
- [同批同错先验同源再计数](pitfalls/same-error-across-batch-is-one-incident.md) — N 条相同错误 ≠ N 次故障；四验：锚点 ID/耗时=总时长÷N/时间戳齐发/原文逐字同；同源按「1 次事件、影响 N 个对象」叙述
- [纳号类请求超时 ≠ 失败](pitfalls/batch-account-onboarding-timeout-verify-before-retry.md) — 纳号/入池类 POST 客户端读超时后服务端常已完成；先只读核对池文件（在不在/令牌落没落）再决定重试；「回包成功」也不等于已落盘
- [外层失败文案 ≠ 子操作失败](pitfalls/run-level-failure-text-is-not-sub-operation-failure.md) — 「Auto-compaction failed」是 run 级聚合文案，同日志 3 次压缩其实全部 succeeded；判"机制失效"要按层核对 attempt 级结算，配额墙真因常在溢出次数而非单次大小

- [整份配置加载失败先查"指向文件"的键](pitfalls/config-load-failure-check-file-refs-and-schema.md) — 文件存在≠合法，还要合该 build 的 schema；第三方工具先写引用后落盘会竞态；表现为设置页改不了/沙盒装不上
- ["不可行"必须先做探针](pitfalls/negative-feasibility-claims-need-a-probe.md) — 机制推断出的否定结论最容易错、代价最大；探针要摘掉混淆变量（IP+SNI 直连 / 假服务记录请求）；停服游戏"离线版"三类探针：配置域名存活 / 资源清单是否全在包内 / 有无第三方 SDK 登录依赖
- [上游升级的行尾噪声与锚点补丁](pitfalls/upstream-merge-crlf-noise-and-anchor-patches.md) — 整文件级 diff 多为 CRLF 噪声（`--ignore-cr-at-eol` 判真伪）；合并后归一 LF 再跑锚点补丁；补丁脚本写盘须 `newline=\"\n\"`；落后 fork 按 SHA 挑单点
- [Windows 硬件保留内存归因：核显 UMA 切分与独显直连无关](pitfalls/windows-hardware-reserved-memory-attribution.md) — 大头=BIOS 划给核显的固定显存；**首选解法=AMD Software→内存优化器→产能档**（实测 4.255→0.755GiB）；**512MB=终局地板（四轮互证：用户态白名单/驱动掩码{1,2}/固件无选项表/AmdSetup 字段级直写实测不生效——16G 极端值+安全模式双刀判决；256 不可达）**；游戏档=4GB 非 2G；总量=SMBIOS 求和−可见量，dxdiag/qwMemorySize 定位；独显直连只管输出路径不释放它；**跨机型固件字段表用前必做同构性校验**
- [含空格路径不加引号的怪文件事故](pitfalls/windows-unquoted-path-redirect-accidents.md) — C:\Program 类残留=重定向在空格处被截断；三步排查（读内容→创建时间/属主→Prefetch 与应用日志对账）；处置=核对后删除，弹窗自然消失

- [转义经补丁管道会变控制字符 ⇒ 校验代码会静默失效](pitfalls/escaping-through-patch-pipelines-needs-positive-control.md) — 「反斜杠 b」被写成退格后正则静默失效（表面还通过）；**凡写正则/转义必配正反对照**；用不含反斜杠的等价写法（[^A-Za-z0-9_] 代替词边界、[ ]* 代替空白、chr(10) 代替换行），写完机检控制字符
- [success 不是「没被中止」的证据](pitfalls/success-status-is-not-no-abort-evidence.md) — 同一 exit 137 两种结局：临死前推完=success、没推完=error；判据读原始日志的 exit 137 与时长；用反例证伪假设必须挖到机制层；两次独立事件时刻相差几秒=硬边界强证据
- [二选一的错误文案不能当单一结论](pitfalls/binary-error-text-needs-branch-evidence.md) — 「A，或 B」只是候选清单；必须用终点可观测物取证落在哪支（容器是否存在/exit 137/时刻）；文案里的数字不等于上限来源
- [易变状态必须带时效标记与复核命令](pitfalls/volatile-state-must-carry-expiry-and-recheck.md) — 原理与状态分层；「已删除/已失效/现行=」须带实测证据+失效条件+复核命令；状态复制到多处会变「真理」；description 要覆盖状态主题；体检跑 `--audit-volatile` 逐条实测

## workflow/ 流程与协作

- [跨工具技能目录语义各异](workflow/cross-agent-skill-dir-semantics.md) — ~/.agents/skills 是共享约定但支持不一；各工具装法跟着语义走；装前先看本机惯例再搜文档，未实测不断言
- [接手半途任务先 diff 部署面与版本面](workflow/diff-deployed-vs-vcs-before-reimplementing.md) — 新实现常写在部署目录没回流仓库；找到现成版做回流别重写，丢注释里的踩坑修正是重写最大代价
- [多工具共享脚本用硬链接统一](workflow/hardlink-unify-shared-scripts-across-tools.md) — 留一个真相源其余同 inode；**仓库 scripts/ ↔ ~/.agents/kb/tools/ 副本必须双向同步（跨项目使用，两处不能硬链）**；git 会断链、校验器按内容兜底；改配置指向换不掉副本漂移
- [哨兵（后台监查进程）](workflow/sentinel-background-watch.md) — 起后台进程轮询并自己判终态 exit；响≠好消息
- [最小改动与不越界三铁律](workflow/minimal-change-and-no-scope-creep.md) — 按字面范围改、闭环即止、不做表面修补；症状词：往返、回撤、返工
- [「本地同步到最新」= 运行时同步，不只是 git](workflow/local-sync-means-runtime-not-just-workspace.md) — 验收面是打开软件看到最新：镜像重建+容器重启+health 实测 version 三件套；只 pull 开发区会让他误判"什么都没做"
- [线上是运营态、全量扫描双扫对齐](workflow/online-is-authoritative-dual-scan.md) — 漂移以线上为权威先问再修；只扫本地不算全量
- [上游异常先查现状再动手](workflow/research-upstream-before-fixing.md) — 免费源脆弱；是否已切换以 DB/API 实测为准
- [子代理编排实战细节](workflow/subagent-orchestration-lessons.md) — 契约先行+文件不相交才并行；失败先续跑勿重派
- [Jev 与 KB 的适用场景及 DSH 清单核验](workflow/use-jev-and-kb-deliberately.md) — Jev 做类型化判断、KB 做检索沉淀
- [日志全量通读方法论](workflow/log-full-read-not-just-errors.md) — 只筛 error 会漏显示假象与产品缺陷
- [平台操作优先 CLI 而非浏览器](workflow/cli-over-browser-automation.md) — 先读文档用命令/API；浏览器只留扫码与一次性 token
- [ZCode 内嵌浏览器（IAB）web 自动化能力边界](pitfalls/zcode-iab-web-automation-capability-boundary.md) — 能做：DOM 读写/受控表单/需用户激活的交互用 cua 真实点击（坐标=截图栅格）/同源 iframe；⛔ 不能做：文件选择器与 window.open 弹窗（真实点击也不够）⇒ 上传与弹窗类必须真浏览器；用 aria-expanded/value 验证是否真生效；症状词：没反应
- [凭据卫生](workflow/token-and-secrets-hygiene.md) — token 不内联命令行、公开内容零敏感痕迹
- [git 操作先核对仓库归属](workflow/git-remote-ownership-check.md) — 先 remote -v 认角色；默认分支=ls-remote --symref；过期缓存可清：`git remote set-head <r> --auto/--delete`（别只忍着污染值）
- [数值结论必须带基准与主语](workflow/numeric-claims-need-baseline-and-subject.md) — 数字全真但表述错也会被读成离谱结论
- [AI 使用披露一致性](workflow/ai-disclosure-consistency.md) — 支撑材料与声明逐项对齐、禁缩水披露
- [用户手工调过的产物即最终稿](workflow/deliver-user-tuned-artifact.md) — 改文字给可粘贴纯文本；改版式只报重建代价
- [交付前本机文本自检](workflow/pre-delivery-text-selfcheck.md) — 不联网查重复/AI 痕迹：10 字窗口重合、句长 CV
- [缺陷定位方法论](workflow/defect-localization-methodology.md) — 根因分层排除+对照实验；对照组须含基线身份
- [OpenClaw 真实上游实弹验证](workflow/openclaw-real-upstream-fire.md) — 直连→最小回合→工具回合；CF 要浏览器 UA
- [交付格式规范优先级](workflow/spec-priority-official-first.md) — 官方规范>模板默认>通用知识库；未规定的保持默认
- [任务书要写「性质」而非「我猜的手段」](workflow/taskbook-write-the-property-not-your-guessed-mechanism.md) — 写死手段会逼执行方两难；写性质+已满足则回报
- [SRC 挖洞前先查驳回标准](workflow/src-prehunt-check-rejection-standard.md) — 先读无效范围/分级/降级规则；拿不准就放弃
- [账号池/渠道汇报用用户可认的称呼](workflow/account-pool-friendly-naming.md) — 用手机尾号/系列+序号/**渠道源名**称呼，禁内部 ID、裸序号与**内部渠道号**（ch176 之类；渠道名取第一对【】内容，写清洗函数复用 + 交付前 grep `ch\d+` 自检）

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
- [动手前先只读盘点现状](workflow/survey-before-acting-on-own-project.md) — 连续迭代自有项目功能常早已存在；先列"已有什么vs缺什么"再决定动什么；连续踩墙2次→回到只读盘点；症状词：忘了吗、说过很多次、不是说了
- [子代理的"已关闭/已不存在/最新版"断言要抽查](workflow/subagent-absence-and-security-claims-need-selfcheck.md) — 三类转述错误：策略读错路径反向、Test-Path 遇带引号路径报假孤儿、winget 无驱动项≠无新版；进用户可见结论前自己跑一条命令；子代理>1h 未完成就停掉自己跑精简版
- [PowerShell 子串匹配当删除条件的误伤](workflow/powershell-substring-match-bulk-delete-hazard.md) — `-match "ACC"` 连删 ACCESSIBILITY 与 ACCESS_TOKEN（含 GitHub PAT）；精确用 -eq/-ceq，先打印清单再删＋动手前 reg export/复制快照
- [关掉某个对象时优先最小作用域原生开关](workflow/prefer-narrow-native-switch-over-broad-global-or-plugin.md) — 逐对象状态机 → prompt 软约束 → 全局开关 → 自写插件，找到第一档就停；全局 allow-list 会误伤
- [派单前先查在跑面（重复派单）](workflow/check-inflight-work-before-dispatch.md) — 派单/开 issue 前三查（开放 PR / 远端分支 / 最近构建）；命中即不派，改为收窄在跑的那支；与「台账会腐烂」互补=两个核对面
- [批准范围不做类推扩展](workflow/approval-is-explicit-not-analogous.md) — 点名批准只做那几项；关 issue/台账前先查背后有无在跑的流程（评审/返工挂它回奏）；可逆≠可以顺手做
- [批量纳号必须一号一登并逐条核对](workflow/batch-account-onboarding-one-per-login.md) — 同一浏览器登录态会把多条待授权 state 全部授权成同一账号（串号是静默的）；多号须换号/无痕 + 按返回体昵称/uid 逐条核对

- [规格先读上游再实测，别盲探](workflow/read-upstream-specs-before-probing.md) — 参数规格（上下文/输出上限/档位）先读源码/`gh release view`/PR/目录元数据；实测只作验收且要有判别力；上游不可达时用 AST 断言+符号检查做证据链
- [工具与产物的位置纪律](workflow/no-new-artifacts-in-c-root.md) — 工具装正规位（C:\Software / C:\Program Files(x86)，别丢 temp）；产物不许给 C 盘卫生添乱（工作区/项目位、一次性 temp 随手清）；已散落=搬家→更新引用→删原位

## tools/ 环境与平台

- [Electron 渲染进程 JS 堆耗尽：判读与兜底治理](tools/electron-renderer-heap-oom-governance.md) — 先读 v8-oom 注解：有 4096MB main-cage ⇒ `--max-old-space-size` 无效；Mark-Compact reduce 回收 0 字节 = 真泄漏；崩溃点≠泄漏点；用产品自带计数器做跨进程对照排除；兜底形状=早期 `--expose-gc`＋低档抓堆快照＋软档释放&GC＋硬档优雅 reload＋崩溃自恢复；附 `tsc -b` 污染 src 与 bundle 默认 mac 目标两个构建坑
- [WSL 里的 Docker 按需启动（不装 Desktop）](tools/wsl-docker-on-demand-startup.md) — Windows 侧无 docker 命令须 wsl.exe 转发带 MSYS_NO_PATHCONV；按需启走 -u root（不手搓 dockerd）；VM 中途重启清场法 / 基础镜像先 pull / build 进度看 /proc cmdline（20261012 四连坑）
- [Git Bash 的 `&` 会拆掉 gh auth login 参数](tools/git-bash-ampersand-breaks-gh-auth-login.md) — 管道送 stdin；Fine-grained 全选=完全权限但删不了库
- [GitHub 大陆双向通路（下载+推送）](tools/github-china-network-workarounds.md) — 下载用 jsdelivr/curl 续传；推送须探测+hosts 一体；`github-push-ip-retry.py` DoH 源已扩（阿里/腾讯×2 + UDP 电信/联通/百度/360/CNNIC，2026-10-06 实测国外 DoH 被墙）
- [git 传输死时走 Git Data API 构造提交](tools/github-git-data-api-push-without-git-transport.md) — 零 git 二进制建分支推提交；须本地 SHA1 预验证
- [细粒度 PAT 缺 PR 写权限 → 403](tools/github-fine-grained-pat-pr-write-403.md) — 能推≠能开 PR；先 GET /pulls 分辨权限 vs 不存在
- [直连云环境里的 AI Agent（CNB 工作区）](tools/cnb-workspace-agent-direct-channel.md) — 附**可执行脚本** `tools/cnb-workspace-agent-cli.py`（reply/history/sessions/keepalive/**watch**） — SSH 进容器 + `POST :8688/api/v1/sessions/{id}/reply` 发消息（⛔ 必带 `x-codebuddy-request: 1`）；⭐20261016 新增：**CLI 打通=继承 serve 进程注入环境（含 CNB_TOKEN 本库令牌，~7 天过期）**、**保活硬门槛=「进页面」（创建后 10 分钟内未进 VS Code 页面即回收，SSH 不算）**（旧「SSH 即心跳」已更正）；附「工作区 start 不能指定模型」「Dockerfile 构建期无 git 凭据」等相邻事实；关闭取证看 backup_status/commit_count/备份自述（file_count 非未提交口径）、平台全量日志不含对话、对话关闭后不可追
- [CNB NPC 派单要点](tools/cnb-npc-dispatch-essentials.md) — ⭐需求单开在**目标仓**（官方：流水线跑在 Issue 所属仓，不是 NPC 注册仓）；⏰入口=**`@apigogo/x(中书令)`**（2026-10-23 实测；10-16『已删』系误记，用前 `get-by-id` 复核）——跨根态B 真人首棒；评论链路无我方密钥（personal-envs 只覆盖云开发）⇒ 真凭据活走 api_trigger_npc 直派/云开发；大任务书走 argv 会截断；workMode 嵌 npc 内
- [CNB 约 2h 流水线硬顶](tools/cnb-pipeline-2h-hard-cap.md) — 真值 `CNB_PIPELINE_MAX_RUN_TIME=7200000`，与 `.cnb.yml` timeout 无关（声明 6h 照样 137）；取证：prepare 日志 `maxPipelineRunTime: 2h` + runner 日志环境变量；api_trigger_npc 固定 2h，issue.comment@npc 档位动态（重发可回 4h）；对策=单命令有界+增量推送
- [CNB 配额 / 自托管 Runner / CLI 坑](tools/cnb-quota-runner-cli-notes.md) — 构建 160 vs 云开发 1600 核时/月独立；省配额三招及代价；Runner 不开 Docker/不计核时/仅构建；`build/start` 缺 title 报 401、Windows 用 `cnb.cmd`、`patch-pull --state closed` 关闭不合并；「请了裁≠免责」
- [CNB token 用量统计方法](tools/cnb-token-usage-audit.md) — 正解=逐构建 get-build-ai-audit 累加；credit 是额度≠token（免费期 0 credit 照记 token）；charge_type_token 是平台 bug；截止时刻默认北京时间
- [CNB issue 附件下载坑](tools/cnb-issue-attachment-download.md) — asset_link 是 Cookie 鉴权路由；200 可能是假 SPA
- [LLM 网关排障优先级](tools/llm-gateway-triage-priorities.md) — 8 条：429 切渠道致缓存全 miss、system 前缀增长作废缓存、cache_creation 恒 0 非 bug、模型别名映射、改历史=毁前缀缓存
- [ZCode 平台实测事实](tools/zcode-platform-verified-facts.md) — 资源落点 + hooks 默认关与 trust 门控 + 后台任务重启后成孤儿（进程活但新实例不列管 ⇒ 停孤儿+重拉；要抗重启改独立进程）
- [ZCode 删会话是软删：状态与正文分两个库](tools/zcode-session-delete-is-soft-delete-two-dbs.md) — 17 条：删除/归档纯软删、状态在 tasks-index、正文在 cli/db 无删除标记；排查前先认清分层
- [数模论文图与摘要视觉基线](tools/mathmodel-paper-visual-baseline.md) — 高级图型清单、rcParams 固化、摘要按方法→数值
- [stdio MCP 安装验收法](tools/mcp-stdio-install-smoke-test.md) — 装前必实测 initialize+tools/list
- [MCP 多密钥池化代理](tools/mcp-multikey-keypool-proxy.md) — 单 key 官方 server 的多密钥正解=逐 key 子进程+stdio 代理（故障转移+冷却自愈）；含 npx 缓存残缺（zod v3/v4 缺失→秒退且零日志）取证法
- [浏览器扩展取证：profile + LevelDB](tools/browser-extension-forensics-profile-leveldb.md) — 判启停/权限读 Secure Preferences（userScripts 须 granted+active 都有）；LevelDB 锁定用 FileShare.ReadWrite 读；location=4 解包扩展删源即失效但注册项须 UI 删；油猴脚本可能依赖本机 RPC 端口（PanLinker→16800 无监听＝不可用）
- [跨浏览器迁扩展：先确认机制再动手](tools/browser-extension-migration-mechanism-first.md) — ego-lite 只认自家安装（外部塞文件/注册会被删）；Chrome 与 Edge 商店同一扩展 ID 不同，按 ID 做差集必误判；chrome://extensions 快照是异步渲染不能当证据，判装没装看 Extensions 目录 + Secure Preferences
- [ego-browser 表单站自动化：弹窗与产物取证](tools/ego-browser-form-automation-dialogs-and-cache.md) — `Input.dispatchMouseEvent` 超时但 `mouse.move`/`evaluate` 正常 ⇒ 是浏览器级权限气泡挡的，改走 DOM `.click()`；DOM 点击"没反应"先列出所有可见 `.ui-dialog` 的按钮文案（EM 确认键=Proceed / Proceed without ORCID iD，只点 Close 等于没做）；EM 上传拒重名须先删后传；`fileDownload.asp` 不带 `authVer=true` 返回旧版成品；`pdftotext -layout` 会把表格封面错读成字段错位，必须渲染成图
- [MCP 有没有用看 handler 返回什么](tools/mcp-prompt-template-servers-add-no-capability.md) — 别读 description 宣称，读 handler 返回什么
- [CNB 密钥库导入与消费链路](tools/cnb-secret-repo-imports.md) — 密钥库拒一切令牌、只能网页编辑；`.cnb.yml` 顶层键须是分支名；Prepare 秒失败无日志的取证手法；NPC 镜像无 `python` 只有 `python3`；应用不读 env 时须加翻译步骤
- [CNB 云开发环境：注入层与 settings 快照](tools/cnb-clouddev-env-injection-snapshot.md) — 注入在主进程 env 非 ssh shell（读 `/proc/<pid>/environ` 且别 head 截断）；bootstrap 须在带注入 env 的进程跑；settings 是建环境那刻的密钥库快照（改库不回流）；跨套错配 401 不等于 key 无效；Prepare success ≠ 变量已注入
- [OpenClaw typed hook 目录](tools/openclaw-hook-catalog.md) — 拦工具调用叫 before_tool_call
- [present_files 传 URL 即开侧栏浏览器](tools/workbuddy-present-files-url-opens-sidebar-browser.md) — URL→侧栏浏览器、本地 .html→预览面板
- [无 sourcemap 时复原前端 bundle 全量与 API 面](tools/frontend-bundle-recovery-without-sourcemap.md) — 入口只有 runtime 别判失败；对齐 chunk 清单
- [出版级中文配图：HTML/CSS 卡片 + 无头浏览器元素截图](tools/html-playwright-figure-pipeline.md) — 设计型中文图别用 matplotlib/AI 生图
- [html-to-docx 在 Windows 的 venv 布局坑](tools/html-to-docx-windows-venv-layout.md) — 插件按 bin/python 判，uv 建 Scripts/ ⇒ 反复重建
- [electron-builder NSIS 静默安装兜底](tools/electron-builder-nsis-silent-install-fallback.md) — /D 必崩、/S 会崩；须 7z 解包 + pylnk3 建快捷方式
- [UAC 与 Windows 更新策略的真实注册表位置](tools/windows-uac-and-windows-update-policy-real-paths.md) — EnableLUA 在 `CurrentVersion\Policies\System`（`Policies\...` 同名路径为空＝读错会反向）；NoAutoUpdate 在 `WindowsUpdate\Automatic Updates`；同键不同值别互推
- [Windows 更新恢复与"不自动重启"操作手册](tools/windows-update-resume-and-no-auto-reboot-playbook.md) — 搜索 0 项先查 UX\Settings 的 Pause*（能被设到 2053）而不是 NoAutoUpdate；防自动重启三件套；CU 历史码 0x80242014=已装待重启；新版本按机器分批推送搜不到≠没有
- [rustup update 被缺失的 msvc rust-std 组件卡死](tools/rustup-update-fails-when-stale-msvc-std-component-missing.md) — `failure removing component` 且目标三元组≠主机＝指纹；旁路＝装新版本号工具链→default→验证→卸旧 stable，重试无用
- [NPC 迭代：把红的原文回传](tools/npc-iterate-by-sending-failure-text-back.md) — 别自己改；给断言原文+失败行+期望语义；既有用例回归单标必修
- [Windows 用户目录清理：可删的 vs 陷阱](tools/windows-home-cleanup-safe-vs-traps.md) — `*updater*`/缓存/解包暂存可删；⛔ `%APPDATA%\npm` 是全局 CLI 入口不是缓存；孤儿 MSI 记录单清
- [ESP32 编译烧录链路（本机 arduino-cli）](tools/esp32-arduino-cli-flash-workflow.md) — 工具链落点 + FQBN 必带 huge_app + sketch 目录同名硬约束 + ELF 体积分析法；附 GFX/ST7789 三坑与"参考图别手绘"

- [WARP 分隧道：外网走隧道、大陆直连](tools/warp-split-tunnel-china-direct.md) — 消费版只能"排除"，故排除大陆 v4+v6 网段；DNS 必须随隧道走故勿用 mode proxy；裸 Python 测国内站点会误判超时
- [Chromium 代理实测：SOCKS4/SOCKS5 与 PAC](tools/chromium-proxy-behavior-socks4-vs-socks5-and-pac.md) — 系统代理 socks= 与 PAC 的 SOCKS 令牌都是 SOCKS4（本地解析、读 hosts），SOCKS5 才远端发域名；用探针 SOCKS 服务看 ATYP 判定
- [Codex hooks 与 Claude 同构](tools/codex-hooks-are-claude-compatible.md) — 事件名与 stdin/stdout 协议一致、脚本可原样复用；用户级只能写 config.toml [hooks]；解析失败只 warning 不报错；桥接 .cmd 需 CRLF、路径用正斜杠绝对路径、改后必复测（fail-open 吞错）
- [Tencent BrowserSkill（bsk）：接入与使用](tools/tencent-browser-skill-setup.md) — 三件套安装（CLI/扩展/技能）+ 收割型宿主 daemon 托管启动（run_in_background + --foreground + BSK_AUTO_START=0）+ upload 需扩展「允许访问文件 URL」+ instance_id 重装即变勿写死（20261014 实测）
- [WSL2 内存账目核对法](tools/windows-wsl2-memory-accounting.md) — 三层取证：.wslconfig 上限（memory/swap/vmIdleTimeout，autoMemoryReclaim 默认不回收）、WSL 内 free -m + docker stats、宿主 vmmemWSL 工作集/提交；WSLg 是第二个隐藏 VM（guiApplications=false 可关）；改配置须 wsl --shutdown；**2026-10-18 补：gradual 无效，`dropcache` 实测空闲 2.5GB→0.41-0.50GB（压测 7.7GB 后 90 秒回落），需 wsl --shutdown，网关自动恢复**
- [NVIDIA 升级"拒绝访问"=服务键被安全软件禁改放删](tools/nvidia-driver-update-denied-by-service-key-lock.md) — UserPnp 20003 返回值 5 即卡点；ACL 清白+SYSTEM 也拒=内核过滤（实测火绒禁改放删）；退出火绒→sc delete 两个容器服务→重装即成；在用驱动包删不掉属保护；**改启动类型可绕开：sc config 仍拒但直写注册表 Services\<svc>\Start=3 立即生效（sc stop 也放行）**（2026-10-17 补）
- [Windows 用户态读写 UEFI 变量四件套](tools/windows-uefi-variable-read-write.md) — 特权 argtypes 假失败/GUID 规范序坑（枚举小端存序）/attr 保留写入+回读验证；枚举条目 NextEntryOffset 布局；carveout-re/uefi-*.py 可复用
- [Windows 内存大户基线：输入体验/搜索/Everything](tools/windows-memory-hogs-ui-hosts-and-everything.md) — TextInputHost 久跑 500MB+ 可安全重启（~250MB 重生）；SearchHost ~150MB 正常；Everything ≈100-130B/条，排除用 -add-exclude-folders（ini exclude_folders 逗号分隔，实测 235.7→117.8MB）；TextInputHost 无官方上限：彻底禁用（改名 SystemApps exe，失触摸/手写/表情，中文输入不受影响）或守护任务 >350MB 自动重启（已落地；SYSTEM 任务须写 powershell 全路径、并关"电池不启动"）（2026-10-18 补）
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
- [Web自动化优先调页面函数与服务端接口](pitfalls/web-automation-call-page-functions-not-dom-clicks.md) — element.click()/UI模拟时灵时不灵；从onclick属性和源码reverse出页面函数与完成接口直接调用是确定性方案；iframe递归遍历/字体混淆用截图读/SPA切换后reload/验证看服务器快照
- [Codex hook 命令必须是合法 PowerShell](pitfalls/codex-hook-command-must-be-valid-in-powershell.md) — Windows 上 hook 走 pwsh，「"a.exe" "b.py"」双引号串写法 ParserError 且发生在进程创建前（日志无痕，易误判成没调度）；改用无空格 .cmd 桥或加 & 调用符；~/.agents 不是 hook 配置源
- [「同步到最新」要打到用户拿到东西的那一层](pitfalls/local-sync-must-reach-user-visible-layer.md) — 启动器每次 pull 会覆盖本地镜像，改本地等于没改；gitignore 的旧 dist 把「源码编译不过」藏了一整天；验证要回拉制品库 digest + 走用户入口
- [接外部工具集：判据是「模型自己做不到」](tools/external-tool-integration-criteria-and-gotchas.md) — 工具数是反向指标（1894 个多是 convert_*/calculate_* 微函数）；握手超时先怀疑客户端（curl 0.47s vs CLI 60s）；URL 里可能要 ASCII slug
- [「阶段」与「执行单元」必须分开](pitfalls/semantic-unit-vs-execution-unit-must-be-separate.md) — 两者压成一个概念会逼出变体爆炸（写作技能 10 个=笛卡尔积）与身份撞车（skill_name 当主键）；修法是加语义层不动执行层 + 零语义漂移（一次性回填/只在多单元阶段渲染/只在声明时序列化）；最易漏的是创建路径（老数据正常、新建全丢）
- [派单前核三方等值 + 载荷先入仓 + 产物落项目内](pitfalls/dispatch-requires-three-way-equality-and-artifact-hygiene.md) — 「我上次核过」在派单语境一律无效（执行者 87 秒就能推进目标仓 ⇒ 三方分叉）；执行者要用的载荷必须先入仓（签名 URL 是旁路）；产物唯一落点 = 项目内 `_tmp/`（先确认 gitignore）
- [含正则元字符的检索词作证据必须加 -F](pitfalls/regex-anchor-literal-search-false-zero-hit.md) — `rg '$FORMAT'` 里 `$` 是行尾锚点⇒恒零命中，会被当成「全仓无消费点」写进审计结论；凡把命中数（尤其 0）当证据，pattern 含 `$ ( ) [ ] . *` 即切 `-F` 并在证据行注明模式
