---
name: kb
description: "全局经验知识库（默认 ~/.agents/kb）。命令用法：`/kb <关键词>` 检索库内经验（底层 python ~/.agents/kb/kb_search.py，支持症状词与 topic 过滤）；`/kb add <一条经验>` 按规范写入；`/kb-harvest` 从各项目 memory 收割跨项目可复用经验。**写入后必须跑 `python ~/.agents/kb/kb_validate.py`，看到 [PASS] 才算完**。非命令时：开始非平凡任务前先检索本库相关经验避免重复踩坑；任务闭环、修复踩坑、总结教训、复盘、发现值得记或引以为戒的内容，以及用户说'记住这个/沉淀经验/晋升到全局/以后别再犯/下次注意/这个坑记一下/写进知识库/长点记性/做个笔记/纳入kb/纳入记忆/记入/订正记忆/修正kb/值得一记/我希望/不希望'等一切表达沉淀意图、需求或约束时（含「…纳入kb了吗/修正kb了吗」这类确认疑问句），把可复用教训写入本库。跨项目可复用经验入本库，项目专属记忆留各项目 memory。关键词：经验、教训、最佳实践、沉淀、记住、全局、复盘、踩坑、值得记、引以为戒、记性、笔记、备忘、存起来、写进知识库。"
---

# kb — 全局经验知识库

> 本文档是 **agent-kb** 项目的核心 Skill 说明。所有 Hook 和 Command 都引用本文件作为唯一权威。
> 项目仓库：`github.com/<your-org>/agent-kb`

**本库的三层目的**（用户定，缺一不可——用它校准一切 kb 相关工作）：

1. **纳入**：犯错/教训/经验一事实一文件结构化入库；
2. **不再犯（核心）**：教训必须在**下一次做同类事之前**被端到 agent 面前——开工检索命中、
   按 How to apply 执行、收尾回流。**存了但执行时想不起来 = 白存**；
3. **多 Agent 平台兼容**：一套库服务所有工具（接入形态因平台而异，记忆同一份）。

> ⚠️ 机制护栏（校验器/触发词）只是手段；判断 kb 工作做得好不好，看这三层——尤其第 2 层。

## 库位置

默认 `~/.agents/kb/`，索引文件 `INDEX.md`。分类目录：

| 目录 | 内容 |
|---|---|
| `tools/` | 环境与工具链经验（装软件、配 PATH、CLI 行为） |
| `workflow/` | 流程与协作方法（改代码、验收标准、跨平台链路） |
| `pitfalls/` | 失败教训与反模式（踩过的坑、静默失败、假阳性） |

配套脚本（**与库同目录，`kb_validate.py` 平铺 import `kb_core.py`，三个必须一起移动**）：

| 文件 | 作用 | 谁调用 |
|---|---|---|
| `kb_core.py` | 消息文本与触发词的**唯一真相源**；索引解析、库路径解析 | 只被 `kb_validate.py` 与 `kb_hooks.py` import |
| `kb_validate.py` | 写入后校验 schema/topic/双链/索引一致性/触发词副本 | 写入规程第 5 步，手动跑 |
| `kb_search.py` | 关键词/症状词/topic 全文检索 + `--similar` 写入前查重 | 检索（Recall）与写入规程第 2 步 |
| `kb_lock.py` | 跨平台写入锁（多会话并发写库时互斥，防读-改-写丢条目） | 写入规程第 3 步前 `with kb_write_lock():` |
| `kb_trigger_miner.py` | 触发词挖掘器（扫新会话 → Jev 判定沉淀意图 → 产候选词报告） | 定期跑，人工过目后扩词表 |
| `kb_jev.py` | **kb 自带**的 Jev 客户端（TypeSafe System One 决策模型，多端点冗余） | 挖掘器等需要「高频小判断」的工具 |
| `kb_hooks.py` | ZCode 钩子适配器，只做协议转换，**不存文案或触发词副本** | ZCode `config.json` 的 hooks.events |

⚠️ 钩子若 import 失败，退化成一句极短提示，**绝不退回旧文案副本**（退回副本等于重新引入漂移）。

### Jev 能力（kb 自带，无需另装技能）

部分 kb 工具需要「高频小判断」（如挖掘器判一条消息是否表达沉淀意图）。
该能力由 `kb_jev.py` **内联**提供——**只装 agent-kb 即可用**，不需要额外安装其他技能。

配置（按优先级）：环境变量 `KB_JEV_KEY`（+ 可选 `KB_JEV_ENDPOINT`/`KB_JEV_MODEL`），
或密钥文件 `~/.agents/kb/jev.key`（单行密钥；兼容读 `~/.jev/{tokenrhythm,apigogo,zen}.key`）。
默认多端点冗余：tokenrhythm → apigogo → opencode zen，前一个失败自动切下一个。
自检：`python ~/.agents/kb/kb_jev.py`（打印各端点可用性，**不打印密钥**）。

⛔ 密钥绝不入库（`.gitignore` 已排除 `*.key` / `jev.key`）。

## 何时检索（Recall）

开始以下任务前，先读 `INDEX.md`，命中相关条目则读全文再动手：

- 非平凡任务（多步、涉及不熟悉的工具/环境、有既往踩坑可能的领域）
- 用户提到"之前遇到过""上次说好的""别再犯"
- 你即将执行的操作与某个已知坑同类（装软件、改 PATH、网络下载、跨工具配置）

检索方式：优先 `python ~/.agents/kb/kb_search.py <关键词...> [--topic 领域]`——全文检索，症状词（挂了/卡死/不生效/黑窗）直达正文；`/kb <关键词>` 底层即它。无脚本环境退回 `grep -ri "关键词" ~/.agents/kb/`。
应用方式：命中的条目按 "How to apply" 执行；若条目与现状矛盾（环境已变），以实测为准并更新该条目。

## 何时写入（Capture）

满足任一条件即写入：

1. 任务闭环时总结，发现**换个项目也用得上**的教训或方法
2. 踩坑后找到根因与解法（尤其耗时 >10 分钟的）
3. 用户明确表达"记住""沉淀""晋升""以后这样做"
4. `/kb add <内容>` 命令直接要求写入

**不写入**的内容：项目专属状态（留项目 memory）、通用常识、可从代码/Git 推导的信息、一次性上下文。

## 写入规程

1. **判类**：工具链 → `tools/`，方法流程 → `workflow/`，教训反模式 → `pitfalls/`
2. **查重**：跑 `python ~/.agents/kb/kb_search.py --similar "<候选标题或一句话描述>"`，top5 同族候选里命中即**扩充它**而非新建（人肉读 INDEX 会漏——同族条目措辞往往互不重叠，2026-10-04 已有同族三副本的真实查重失败）
3. **并发写保护**：多会话/多 Agent 可能同时在写库（本机实测发生过）——写入前用
   `python -c "import sys;sys.path.insert(0,__import__('os').path.expanduser('~/.agents/kb'));from kb_lock import kb_write_lock;..."`
   或直接在脚本里 `from kb_lock import kb_write_lock` 然后 `with kb_write_lock():` 包住「读 INDEX → 改 → 写回」整段。
4. **新建文件**：`<目录>/<kebab-slug>.md`，frontmatter **七个必填字段一个都不能少**：

   | 字段 | 填法 |
   |---|---|
   | `name` | 与文件名同名的 kebab-slug |
   | `description` | 一句话摘要（检索全靠它）；只对某平台成立的结论要点名平台或加 `【作用域=X】` |
   | `type` | `tool` / `workflow` / `pitfall`，**必须与所在目录一致** |
   | `source` | 来源项目或事件 |
   | `date` | 写入日期 `YYYY-MM-DD` |
   | `verified` | 经验被实测确认的日期 `YYYY-MM-DD` |
   | `topic` | 领域，取受控词表之一（见下） |

   `topic` 受控词表（正交于 `type`；`type` 答"怎么用"，`topic` 答"属于哪个领域"）：
   `api-gateway` `agent-orchestration` `browser` `ci` `cnb` `container` `database`
   `sqlite` `delivery` `git` `llm` `mcp` `methodology` `office` `powershell`
   `preference` `python` `security` `tauri` `windows` `zcode`

   正文三段式：**经验**（直接说怎么做）/ **Why**（不这样做会怎样）/ **How to apply**（何时用）。
5. **更新 INDEX.md**：在对应分类下加一行 `- [标题](相对路径) — 一句话钩子`
6. **跑校验器（不可跳过）**：

   ```bash
   python ~/.agents/kb/kb_validate.py
   ```

   必须看到 `[PASS]` 才算写完。它查 frontmatter 七字段、`type` 与目录一致性、`topic` 是否在词表、
   `[[双链]]` 是否指向存在的条目、索引行数与磁盘文件数是否**双向**一致。
   报 `[FAIL]` 就按它列的行逐条修，**不要绕过、不要改校验器迁就条目**。
7. **写作风格**：直说怎么做，一事实一文件，条目 ≤ 30 行。与「同族扩充」的冲突裁决：
   同一事实的新证据/新反例 → 扩充现有条目（允许超行，过程性复盘移 CHANGELOG）；
   独立可检索的新事实 → 新建条目 + [[双链]] 互指，宁可同族多条也不塞成一篇。

## 合并既有条目（两条并一条时照此执行）

1. **保谁**：保留内容最全/最早的那条（文件名与 `name` 不变），另一条的独有内容全部并入后删除其文件
2. **字段并接**：`source` 追加并注明日期；`date` 取最早；`verified` 取最新实测日；`topic` 取并集（逗号多值）；`description` 重写为合并后的完整摘要
3. **正文**：并入段标注来源日期；被并条目的 [[出链]] 一并带过来；全库 grep 被并条目名，把引用改指保留条目
4. **收尾三件**：INDEX 删被并行、保留行钩子重写以覆盖合并后内容（检索全靠钩子行，漏改=检索降级）；CHANGELOG 记一条（谁并入谁、理由）；跑 kb_validate 见 [PASS]

## 与项目 memory 的分工

| | `~/.agents/kb/` | 项目 memory（平台相关） |
|---|---|---|
| 范围 | 全局，所有会话可见 | 仅该项目会话注入 |
| 收什么 | 跨项目可复用的经验/教训/方法 | 项目状态、进度、专属事实 |
| 晋升 | 由 `/kb-harvest` 从各项目 memory 提炼 | — |
