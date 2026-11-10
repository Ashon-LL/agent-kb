# 🧠 agent-kb — Agent 全局经验知识库

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow)](#)
[![Tests](https://img.shields.io/badge/tests-unittest%20suite-brightgreen)](#)
[![Adapters](https://img.shields.io/badge/adapters-10%20adapters-orange)](#)
[![Products](https://img.shields.io/badge/products-12-lightgrey)](#)
[![Non-blocking](https://img.shields.io/badge/non--blocking-exit%200-critical)](#)
[![Format](https://img.shields.io/badge/storage-markdown-blueviolet)](#)

[![Trae](https://img.shields.io/badge/Trae-hook-blueviolet?style=flat-square)](#)
[![ZCode](https://img.shields.io/badge/ZCode-hook-blueviolet?style=flat-square)](#)
[![Codex](https://img.shields.io/badge/Codex-hook-blueviolet?style=flat-square)](#)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-hook-orange?style=flat-square)](#)
[![Kimi Code](https://img.shields.io/badge/Kimi%20Code-hook-4169E1?style=flat-square)](#)
[![Qoder](https://img.shields.io/badge/Qoder-hook-ff6a00?style=flat-square)](#)
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-skill-yellowgreen?style=flat-square)](#)
[![CodeBuddy](https://img.shields.io/badge/CodeBuddy-hook%20legacy-lightgrey?style=flat-square)](#)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-plugin-cyan?style=flat-square)](#)
[![OpenCode](https://img.shields.io/badge/OpenCode-plugin-8A2BE2?style=flat-square)](#)
[![Hermes](https://img.shields.io/badge/Hermes-unverified-lightcoral?style=flat-square)](#)
[![PI](https://img.shields.io/badge/PI-unverified-ff69b4?style=flat-square)](#)

> 让你的 AI Agent **不再重复踩坑**。跨项目、跨平台、零阻塞的经验沉淀与检索系统。

## 你是不是也……

- 同一个坑，上周刚踩过，今天 Agent 又踩了一遍，还踩得一模一样？
- 明明上一轮自己说过「这个要记住」，下一轮翻遍上下文，它像失忆一样？
- 换了个项目、换了个平台，之前积累的经验全部归零，从零开始教？
- 项目专属记忆散落在聊天记录、临时笔记、不同工具的私有数据库里，想找找不到？

> 😤 **Agent 不是不聪明，是记不住。**
> 记忆不在它的脑子里，那就在你的库里 —— 一份纯 Markdown、能 git、能 grep 的库。

## 一句话

**Hook / Skill / Plugin 自动提醒 → Skill 统一规程 → Markdown 格式库 → 多平台适配**。写一次，Agent 终身受益。

### TL;DR

```bash
# 装（仓库自带安装器，无 pip 包）
.\scripts\install.ps1 -Platform trae      # Windows
./scripts/install.sh -p trae              # macOS / Linux
```

装好后用斜杠命令：`/kb <关键词>` 检索，`/kb add <一条经验>` 写入。

- 📄 存的是 **纯 Markdown** —— 人类 `cat` 就能读
- 🪝 自动提醒 **非阻塞**（Hook / Skill / Plugin）—— 任何异常 `exit 0`，绝不拖慢你的 Agent
- 🌍 **不绑平台** —— Trae / ZCode / Codex / Claude Code … 一次沉淀，处处可用

| 没有 agent-kb | 有 agent-kb |
|---|---|
| 同一个坑被坑 3 次 | 踩一次、沉淀一次、终身复用 |
| "之前好像见过这个问题" → 翻历史消息 | `grep ~/.agents/kb/` 一秒命中 |
| 项目专属记忆散落在各处 | 跨项目可复用的经验统一收集在一个库 |

> 🛡️ 核心就一句：**经验是资产，资产得存在你手里。** 存在向量库里是租的，存在 md 里是你的。

## 文档地图

| 文档 | 回答的问题 |
|---|---|
| `README.md` | 怎么用、支持哪些平台、安装与测试入口 |
| `skill/SKILL.md` | 写入/检索/收割的**操作规程**（唯一权威） |
| `docs/adr/README.md` | **为什么这样设计**、替代方案与后果 |
| `tests/` | 可执行的行为契约与回归 |
| 工作区 `AGENTS.md` | 跨项目强制边界与命令 |
| 工作区 `references/decision-changelog.md` | 规则旧值 → 新值 |

## 🆚 agent-kb vs 其他记忆方案

Agent 记忆这块，方案不少。差别不在「记不记得住」，而在 **记忆归谁、存在哪、能不能被人看见**。

| 维度 | agent-kb | Mem0 / LangGraph Memory | OpenCode Memory | Claude Code 项目记忆 | Dify 记忆 |
|---|---|---|---|---|---|
| **存储格式** | 纯 Markdown | 向量数据库 | 内部数据库 | 会话历史 | 向量数据库 |
| **谁来写** | Hook/Skill/Plugin + 手动 | Agent 自动 | Agent 自动 | Agent 自动 | Agent 自动 |
| **人类可读？** | ✅ 直接 cat | ❌ 向量不可读 | ❌ | ❌ | ❌ |
| **跨项目共享** | ✅ ~/.agents/kb | ❌ 单租户 | ❌ | ❌ | ❌ |
| **跨平台 Agent** | ✅ 12 平台（含 skill-only / plugin） | ❌ 绑定框架 | ❌ 绑定平台 | ❌ 绑定平台 | ❌ 绑定框架 |
| **零阻塞** | ✅ exit 0 | ⚠️ 可能超时 | ⚠️ | ⚠️ | ⚠️ |
| **需要部署** | ❌ 安装器装完就跑 | ✅ 向量数据库 | ❌ | ❌ | ✅ |
| **能进 Git** | ✅ 就是 md 文件 | ❌ | ❌ | ❌ | ❌ |

其他方案是让 Agent「记住」，agent-kb 是让 Agent **学会**。记住会忘，学会不会。

## 架构（四层）

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hook / Skill / Plugin 层（适配器）              │
│  Trae/Codex hooks.json · ZCode cli/config.json hooks.events         │
│  WorkBuddy: ~/.workbuddy/skills/kb（skill-only，无 hook）           │
│  OpenCode/OpenClaw: JS/TS 插件桥                                    │
│               kb_core.py  ←  平台无关核心逻辑                      │
│  SessionStart → 开工提醒 · UserPromptSubmit → 沉淀规程 · Stop → 收尾 │
└─────────────────────────────────────────────────────────────────┘
                          │ 引用
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Skill 层（SKILL.md）                        │
│  唯一权威 — 何时检索、何时写入、分类规则、frontmatter 格式       │
└─────────────────────────────────────────────────────────────────┘
                          │ 引用
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      命令层（commands/*.md）                      │
│  /kb <关键词>          直接检索                                   │
│  /kb add <经验>        直接写入                                   │
│  /kb-harvest [路径]    会话库+工作区+memory 收割                 │
└─────────────────────────────────────────────────────────────────┘
                          │ 产出
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      库层（~/.agents/kb/）                        │
│  INDEX.md + tools/ + workflow/ + pitfalls/                      │
│  纯 Markdown，零依赖，人类 Agent 都能读                          │
└─────────────────────────────────────────────────────────────────┘
```

### Hook 注入链路（三段式）

```
① 平台回调点          ② 执行载体               ③ 平台消费
   hook_event_name  →   Python 子进程  →    stdout JSON 字段
                        (stdin 读 JSON)      ├─ hookSpecificOutput (Trae/ZCode)
                                              └─ systemMessage     (Codex)
                        任何异常 → exit 0，绝不阻塞
```

### 设计亮点

| 点 | 说明 |
|---|---|
| **自过滤式 Hook** | `TRIGGER_PATTERN` 正则补位平台 matcher，避免 false positive |
| **规程驱动** | Skill 是唯一权威，Hook 和 Command 都引用它。改一处全链路生效 |
| **零阻塞承诺** | 所有 hook 异常静默 exit 0，保证 Agent 不因 kb 挂掉卡壳 |
| **适配器模式** | `kb_core.py` 平台无关，各平台只写一个薄适配器 |
| **两层记忆分工** | 全局 kb（跨项目复用） vs 项目本地文档/项目 memory（项目专属） |
| **决策可追溯** | 架构决策写入 `docs/adr/`，README 只留索引，避免结论与理由散落 |

---

## 平台支持

| 平台 | 接入形态 | 实现 / 事件 | stdin 事件字段 | stdout / 发现方式 | 核实状态 |
|---|---|---|---|---|---|
| Trae | Hook | trae_zcode_adapter.py · SessionStart / UserPromptSubmit | `hook_event_name` | `hookSpecificOutput.additionalContext` | ✅ |
| ZCode | Hook | kb_hooks.py · SessionStart / UserPromptSubmit / Stop | `hook_event_name` | `hookSpecificOutput.additionalContext` | ✅ |
| Codex CLI | Hook | codex_adapter.py · SessionStart / UserPromptSubmit | **`event`** | **`systemMessage`** | ✅ |
| Claude Code / Desktop | Hook | claude_adapter.py · SessionStart / UserPromptSubmit | `hook_event_name` | `hookSpecificOutput.additionalContext` | ✅ |
| Qoder | Hook | qoder_adapter.py · SessionStart / UserPromptSubmit | `hook_event_name` | `hookSpecificOutput.additionalContext` | ✅ |
| Kimi Code | Hook | kimi_adapter.py · SessionStart / UserPromptSubmit | `hook_event_name` | 纯文本（追加进上下文） | ✅ |
| WorkBuddy | **Skill only** | `SKILL.md` → `~/.workbuddy/skills/kb` | — | 平台自动发现 `~/.workbuddy/skills` | ✅ |
| CodeBuddy | Hook（legacy） | workbuddy_adapter.py · SessionStart / UserPromptSubmit | `hook_event_name` | `hookSpecificOutput.additionalContext` | ⚠️ 已卸载，无活跃消费者 |
| OpenClaw | **Plugin bridge** | openclaw_adapter.py · `session_start` / `before_prompt_build` | `hook_event_name` | 插件 `api.on(...)` | ✅ |
| OpenCode | **Plugin bridge** | opencode_adapter.py · `session.created` / `tui.prompt.append` | 嵌套 `event.type` + `event.properties` | 插件桥 | ✅ |
| Hermes | Hook（未核实） | hermes_adapter.py · 占位 | `hook_event_name` | `hookSpecificOutput.additionalContext` | ⚠️ 未找到官方文档 |
| PI (Perplexity) | Hook（未核实） | pi_adapter.py · 占位 | `hook_event_name` | `hookSpecificOutput.additionalContext` | ⚠️ 未找到官方文档 |

> **每个适配器的文件头**都写清了：平台名、hook 官方文档链接、
> stdin 字段映射表、stdout 格式说明。改平台差异只需动对应文件一处。
>
> **配置载体差异**：
> - Trae / Codex / Hermes / PI → 独立 `hooks.json`
> - ZCode（新版）→ `~/.zcode/cli/config.json` 的 `hooks.events`（merge 型，保留其他键与事件）
> - Claude / Qoder / CodeBuddy → 合并进已有 **`settings.json`** 的 `hooks` 子树（保留其他键）
> - WorkBuddy → **无 hook 配置**：`SKILL.md` 放 `~/.workbuddy/skills/kb`，由平台自动发现（skill-only）
> - Kimi → **TOML** `~/.kimi-code/config.toml` 的 `[[hooks]]` 数组（手工注册）
> - OpenCode / OpenClaw → **JS/TS 插件桥**，Python 脚本作为子进程被 shell 调用（手工注册）
>
> **桥接说明**：OpenCode、OpenClaw 原生扩展点是 JS/TS 插件，本项目的 Python 适配器作为
> 子进程桥供插件 shell 调用；其余 hook 平台为原生 stdin/stdout；WorkBuddy 为 skill-only，无 hook。

## 环境变量

所有 10 个适配器统一支持（由 `hooks/adapter_base.py` 集中实现）：

| 变量 | 取值 | 语义 |
|---|---|---|
| `AGENT_KB_PATH` | 目录路径 | 覆盖默认 `~/.agents/kb`。**优先级最高**，高于 `sys.argv[1]` |
| `AGENT_KB_DEBUG` | `1` 开启 | 向 **stderr** 输出 `[agent-kb debug] 事件=xxx prompt_len=xx kb_path=...` |

kb 路径解析优先级（高 → 低）：`AGENT_KB_PATH` → `sys.argv[1]` → `~/.agents/kb`（运行时求值）。

debug 输出走 stderr —— 各平台只读 stdout / 退出码，因此调试信息不会污染注入内容。

```bash
# 例：把库换到别处，并打开调试
export AGENT_KB_PATH="$HOME/my-kb"
export AGENT_KB_DEBUG=1
```

另有 `AGENT_KB_TRIGGER`（分号分隔的正则片段），用于扩充沉淀触发词，与内置触发词取并集。

---

## 安装

两个安装脚本功能对称，覆盖 12 个平台名、10 个适配器文件（trae/zcode 共用；CodeBuddy 复用 workbuddy_adapter；WorkBuddy 为 skill-only）。

### Windows（PowerShell）

```powershell
git clone https://github.com/<your-org>/agent-kb.git
cd agent-kb

.\scripts\install.ps1 -List                 # 先看支持哪些平台、装到哪
.\scripts\install.ps1 -Platform trae        # 安装（默认 trae）
.\scripts\install.ps1 -Platform claude -Force   # 覆盖/合并已存在配置
```

参数：`-Platform`（平台名）/ `-KbPath`（库目录，默认 `~/.agents/kb`）/ `-Force` / `-List`。

### macOS / Linux（bash）

```bash
git clone https://github.com/<your-org>/agent-kb.git
cd agent-kb

./scripts/install.sh -l                # 平台清单
./scripts/install.sh -p trae           # 安装（默认 trae）
./scripts/install.sh -p claude -f      # 覆盖/合并已存在配置
```

参数：`-p`（平台名）/ `-k`（库目录）/ `-f`（force）/ `-l`（列表）/ `-h`（帮助）。
脚本 `set -euo pipefail`，任一步失败即中止。

### 支持平台

`trae` `zcode` `codex` `claude` `qoder` `workbuddy` `codebuddy` `hermes` `pi`
`kimi` `opencode` `openclaw`

安装器会：把适配器 + `kb_core.py` + `adapter_base.py` 拷进该平台的 hooks 目录，
生成或合并 hook 配置，并在 `~/.agents/kb` 不存在时铺一份空库模板。
`claude` / `qoder` / `codebuddy` 为 **merge 型**：只替换 `settings.json` 的 `hooks` 子树，
其余键原样保留，并留 `.bak` 备份。`workbuddy` 是 **skill-only**：只装
`~/.workbuddy/skills/kb/SKILL.md`，不生成 hook 配置。

### 测试

```bash
# Linux / CI（python:3.11-slim）
python3 -m unittest discover tests/

# Windows 本机：先开 UTF-8 模式，避免 subprocess 用 GBK 解码中文输出
set PYTHONUTF8=1 && python -m unittest discover tests/
```

### 手动安装

见 `scripts/install.ps1` 的 3 个步骤：Skill → Hooks → 库模板。
`scripts/install.sh` 与 PowerShell 版功能对称，参数见上节。

---

## 使用

三种沉淀入口，共用同一份 SKILL 规程与校验器：

| 入口 | 触发 | 是否写库 |
|---|---|---|
| `/kb add` | 用户明确要求沉淀 | 是：按规程写入并跑 `kb_validate` |
| `/kb-harvest` | 定期/手动批量收割 | 先出候选，用户确认后写 |
| kb hooks | SessionStart / UserPromptSubmit / Stop | 否：只注入提醒与规程 |

| 操作 | 命令 | 示例 |
|---|---|---|
| 检索 | `/kb <关键词>` | `/kb CNB` |
| 写入 | `/kb add <内容>` | `/kb add 从 Python spawn npm CLI 必须用 .cmd` |
| 收割 | `/kb-harvest [路径]` | `/kb-harvest`（ZCode 会话库 + 当前工作区；项目 memory 可选） |
| 审计 | 直接运行脚本 | `python ~/.agents/kb/kb_audit.py`（只读报告） |

**非命令时**：Skill 的 description 里写明了"开始非平凡任务前先检索、踩坑闭环后沉淀"，Agent 会在合适的时机主动触发。

---

## 库结构

```
~/.agents/kb/
├── INDEX.md                 # 唯一入口，每次会话被 hook 扫视
├── pitfalls/                # 失败教训与反模式
│   └── tempdir-not-persistent.md
├── workflow/                # 流程与协作方法
│   └── summarize-on-task-close.md
└── tools/                   # 环境与工具链
    └── cli-name-platform-diff.md
```

单条目格式（`schema/entry.md`）：

```markdown
---
name: kebab-case-slug
description: 一句话摘要（检索靠它）
type: tool | workflow | pitfall
source: 来源项目或事件
date: YYYY-MM-DD
---

**经验**：直接说怎么做。
**Why**：（可选）不这样做会怎样。
**How to apply**：（可选）什么场景、如何应用。
```

---

## 仓库结构

```
agent-kb/
├── skill/SKILL.md               # 核心 Skill（唯一权威）
├── hooks/
│   ├── kb_core.py               # 平台无关逻辑（文案与触发词唯一真相源）
│   ├── adapter_base.py          # 适配器公共契约（stdin/stdout、路径解析、事件归一）
│   ├── trae_zcode_adapter.py    # Trae / ZCode 适配器
│   ├── codex_adapter.py         # Codex CLI 适配器
│   ├── claude_adapter.py        # Claude Desktop 适配器
│   ├── qoder_adapter.py         # Qoder 适配器
│   ├── hermes_adapter.py        # Hermes 适配器（emit 待核实）
│   ├── pi_adapter.py            # PI (Perplexity) 适配器（emit 待核实）
│   ├── opencode_adapter.py      # OpenCode 适配器（TS 插件桥）
│   ├── openclaw_adapter.py      # OpenClaw 适配器（TS 插件桥）
│   ├── workbuddy_adapter.py     # CodeBuddy CLI 适配器（WorkBuddy 为 skill-only）
│   ├── kimi_adapter.py          # Kimi Code 适配器
│   ├── kb_hooks.py              # ZCode 钩子适配器（只做协议转换）
│   ├── kb_jev.py                # kb 自带 Jev 客户端（多端点冗余）
│   ├── kb_search.py             # 全文检索
│   ├── kb_validate.py           # 库校验（含触发词副本一致性）
│   ├── kb_lock.py               # 跨平台写入锁
│   ├── kb_trigger_miner.py      # 触发词挖掘器
│   ├── kb_harvest.py            # 只读收割候选生成器
│   ├── kb_audit.py              # 只读库审计（重复/零入链/过期）
│   └── kb_validate_selftest.py  # 校验器自测
├── commands/                    # 斜杠命令（Trae 由 Skill description 触发）
│   ├── kb.md
│   └── kb-harvest.md
├── library-template/            # 空库模板 + 3 条示例
├── library/                     # 仓库内镜像库（当前 298 条）
├── schema/
│   ├── entry.md                 # 条目格式模板
│   └── INDEX-template.md
├── templates/                   # 各平台 hooks 模板（11 份，含占位符）
├── scripts/
│   ├── install.ps1              # Windows 一键安装
│   ├── install.sh               # macOS / Linux 一键安装
│   ├── smoke_test.py            # 冒烟测试
│   └── push_with_ip_retry.py    # GitHub mirror 推送（恢复维护后）
├── tests/                       # unittest 套件
├── docs/
│   ├── adr/                     # 架构决策记录（ADR）
│   └── ...                      # 本地视频素材（不入库）
└── .cnb.yml                     # CI + NPC 派单 + 云开发环境
```

---

## 测试

零第三方依赖，Python 自带 `unittest` 即可跑：

```bash
# 全部单测（以命令实测输出为准）
python3 -m unittest discover tests/

# Windows 本机：先开 UTF-8 模式，避免 subprocess 用 GBK 解码中文输出
set PYTHONUTF8=1 && python -m unittest discover tests/

# 冒烟测试：起 subprocess 真喂 stdin 给适配器，校验 stdout 契约
python3 scripts/smoke_test.py
# [PASS] 3/3
```

`smoke_test.py` 覆盖三个场景：SessionStart 注入开工钩子（并核对 INDEX.md 条目数）、
UserPromptSubmit 带触发词注入沉淀钩子、UserPromptSubmit 不带触发词静默放行。

CI 已在 `.cnb.yml` 注册 push / PR 门禁（`unit tests` + `smoke test`），任一 Stage 不过即红灯。

> CI 跑在 `python:3.11-slim` 镜像上。缺省镜像不含 `python3`，
> 若改成不指定 `docker.image`，脚本会以 `sh: python3: command not found`（退出码 127）挂掉。

---


## 适配新平台

1. 在 `hooks/` 下写一个 `<platform>_adapter.py`，import `kb_core`，按平台要求的 stdout 格式包装返回值
2. 在 `templates/` 下写 `<platform>-hooks.json`，注册两个事件：`SessionStart` 和 `UserPromptSubmit`
3. 在 README "安装" 节加一行说明

就这么简单。

---

## 架构决策记录（ADR）

完整背景、替代方案与后果见 [`docs/adr/README.md`](docs/adr/README.md)。README 只留索引。

| ADR | 决策 | 状态 |
|---|---|---|
| [0001](docs/adr/0001-three-write-channels.md) | 三条沉淀通道：手动 / 批量 / 自动 | Accepted |
| [0002](docs/adr/0002-platform-adapter-matrix.md) | 平台接入形态矩阵：hook / skill / plugin / unverified | Accepted |
| [0003](docs/adr/0003-zcode-config-location.md) | ZCode 配置落点：`hooks.events` | Accepted |
| [0004](docs/adr/0004-harvest-readonly-pipeline.md) | 收割是只读候选管线 | Accepted |
| [0005](docs/adr/0005-search-idf-ranking.md) | 检索叠加 IDF，保留命中词数优先 | Accepted |
| [0006](docs/adr/0006-readonly-library-audit.md) | 库审计只读 | Accepted |
| [0007](docs/adr/0007-markdown-zero-dependency.md) | 纯 Markdown + 标准库，零第三方依赖 | Accepted |
| [0008](docs/adr/0008-runtime-deployment-sync.md) | 仓库是源，运行时副本按安装器同步 | Accepted |
| [0009](docs/adr/0009-documentation-layers.md) | 文档分层：README / SKILL / ADR / 契约 / 变更日志 | Accepted |

规则变更（旧值 → 新值）记录在工作区 `references/decision-changelog.md`，不写进 ADR。

---

## License

MIT
