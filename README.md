# agent-kb — Agent 全局经验知识库

> 让你的 AI Agent **不再重复踩坑**。跨项目、跨平台、零阻塞的经验沉淀与检索系统。

## 一句话

**Hook 自动提醒 → Skill 统一规程 → Markdown 格式库 → 多平台适配**。写一次，Agent 终身受益。

---

## 为什么需要它？

| 没有 agent-kb | 有 agent-kb |
|---|---|
| 同一个坑被坑 3 次 | 踩一次、沉淀一次、终身复用 |
| "之前好像见过这个问题" → 翻历史消息 | `grep ~/.agents/kb/` 一秒命中 |
| 项目专属记忆散落在各处 | 跨项目可复用的经验统一收集在一个库 |

## 架构（四层）

```
┌─────────────────────────────────────────────────────────────────┐
│                         Hook 层（适配器）                         │
│  Trae/ZCode hooks.json ───┐   Codex .codex/hooks.json ───┐      │
│                           │                               │      │
│               kb_core.py  ←  平台无关核心逻辑  ──────────┘      │
│  SessionStart   → 注入开工提醒                                   │
│  UserPromptSubmit → 命中"记住/沉淀"时注入写入规程                │
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
│  /kb-harvest [路径]    跨项目扫描晋升                             │
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
| **两层记忆分工** | 全局 kb（跨项目复用） vs 项目 memory（项目专属状态） |

---

## 平台支持

| 平台 | Hook 适配器 | 状态 |
|---|---|---|
| Trae | trae_zcode_adapter.py | ✅ |
| ZCode | trae_zcode_adapter.py | ✅ |
| Codex CLI | codex_adapter.py | ✅ |
| Claude Desktop | claude_adapter.py | ✅ 派单 #1 |
| Qoder | qoder_adapter.py | ✅ 派单 #1 |
| Hermes | hermes_adapter.py | ✅ 派单 #2 |
| PI | pi_adapter.py | ✅ 派单 #2 |
| OpenCode | opencode_adapter.py | ✅ 派单 #2 |
| OpenClaw | openclaw_adapter.py | ✅ 派单 #2 |
| WorkBuddy | workbuddy_adapter.py | ✅ 派单 #2 |
| Kimi Code | kimi_adapter.py | ✅ 派单 #2 |

> **emit 格式来源**：每个适配器文件头都注明该平台 hook 输出格式的官方文档链接。
> 已核实：Claude Desktop、Qoder、Kimi Code、WorkBuddy/CodeBuddy、OpenClaw（TS 插件桥接）、OpenCode（TS 插件桥接）。
> 未核实（骨架待补）：Hermes、PI —— 文件头标 `# TODO: emit format not verified`。
>
> **桥接说明**：OpenCode、OpenClaw 原生扩展点是 JS/TS 插件，本项目的 Python 适配器作为
> 子进程桥供插件 shell 调用；其余平台为原生 stdin/stdout hook。

---

## 安装

### Windows 一键安装（推荐）

```powershell
# 克隆仓库
git clone https://github.com/<your-org>/agent-kb.git
cd agent-kb

# 安装到 TraeWork（默认）
.\scripts\install.ps1 -Platform trae

# 安装到 ZCode
.\scripts\install.ps1 -Platform zcode

# 安装到 Codex CLI
.\scripts\install.ps1 -Platform codex
```

可选参数：
- `-KbPath ~/.my-kb` 自定义库路径（默认 `~/.agents/kb`）
- `-Force` 覆盖已存在文件

### 手动安装

见 `scripts/install.ps1` 的 3 个步骤：Skill → Hooks → 库模板。

### macOS / Linux

`scripts/install.sh` （WIP，结构同 PowerShell 版），或直接按 PowerShell 脚本里的步骤手动操作。

---

## 使用

| 操作 | 命令 | 示例 |
|---|---|---|
| 检索 | `/kb <关键词>` | `/kb CNB` |
| 写入 | `/kb add <内容>` | `/kb add 从 Python spawn npm CLI 必须用 .cmd` |
| 收割 | `/kb-harvest [路径]` | `/kb-harvest`（扫当前工作区）或 `/kb-harvest C:\projects` |

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
│   ├── kb_core.py               # 平台无关逻辑
│   ├── trae_zcode_adapter.py    # Trae / ZCode 适配器
│   ├── codex_adapter.py         # Codex CLI 适配器
│   ├── claude_adapter.py        # Claude Desktop 适配器
│   ├── qoder_adapter.py         # Qoder 适配器
│   ├── hermes_adapter.py        # Hermes 适配器（emit 待核实）
│   ├── pi_adapter.py            # PI (Perplexity) 适配器（emit 待核实）
│   ├── opencode_adapter.py      # OpenCode 适配器（TS 插件桥）
│   ├── openclaw_adapter.py      # OpenClaw 适配器（TS 插件桥）
│   ├── workbuddy_adapter.py     # WorkBuddy / CodeBuddy 适配器
│   └── kimi_adapter.py          # Kimi Code 适配器
├── commands/                    # ZCode 风格命令（Trae 由 Skill description 触发）
│   ├── kb.md
│   └── kb-harvest.md
├── library-template/            # 空库模板 + 3 条示例
│   ├── INDEX.md
│   ├── pitfalls/
│   ├── workflow/
│   └── tools/
├── schema/
│   ├── entry.md                 # 条目格式模板
│   └── INDEX-template.md
├── templates/                   # 各平台 hooks 模板（含占位符）
│   ├── trae-hooks.json
│   ├── zcode-hooks.json
│   ├── codex-hooks.json
│   ├── claude-hooks.json
│   ├── qoder-hooks.json
│   ├── hermes-hooks.json
│   ├── pi-hooks.json
│   ├── opencode-hooks.json
│   ├── openclaw-hooks.json
│   ├── workbuddy-hooks.json
│   └── kimi-hooks.json          # Kimi 为 TOML 占位，见文件内 _toml_template
├── scripts/
│   ├── install.ps1              # 一键安装
│   └── smoke_test.py            # 冒烟测试：真跑适配器校验 hook 输出契约
├── tests/
│   ├── test_kb_core.py          # 核心逻辑单测（触发词 / INDEX 统计 / 路径求值）
│   └── test_trae_zcode_adapter.py  # 适配器端到端 stdin/stdout 契约测试
└── docs/
    └── architecture.md          # 架构详文（WIP）
```

---

## 测试

零第三方依赖，Python 自带 `unittest` 即可跑：

```bash
# 全部单测（28 项）
python -m unittest discover tests/
# 或
python -m pytest tests/

# 冒烟测试：起 subprocess 真喂 stdin 给适配器，校验 stdout 契约
python scripts/smoke_test.py
# [PASS] 3/3
```

`smoke_test.py` 覆盖三个场景：SessionStart 注入开工钩子（并核对 INDEX.md 条目数）、
UserPromptSubmit 带触发词注入沉淀钩子、UserPromptSubmit 不带触发词静默放行。

CI 已在 `.cnb.yml` 注册 push / PR 门禁（`unit tests` + `smoke test`），任一 Stage 不过即红灯。

> CI 跑在 `python:3.11-slim` 镜像上。缺省镜像不含 `python3`，
> 若改成不指定 `docker.image`，脚本会以 `sh: python3: command not found`（退出码 127）挂掉。

---

## 环境变量

所有适配器统一生效（解析逻辑收在 `hooks/adapter_base.py`）：

| 变量 | 取值 | 语义 |
|---|---|---|
| `AGENT_KB_PATH` | 目录路径 | 覆盖默认库路径。**优先级最高**，高于 `sys.argv[1]` |
| `AGENT_KB_DEBUG` | `1` 开启 | 向 **stderr** 输出 `[agent-kb debug] ...` 诊断行（不污染注入内容） |
| `AGENT_KB_TRIGGER` | 分号分隔的正则片段 | 追加自定义触发词，与内置触发词取并集。例：`归档;复盘` |

`AGENT_KB_TRIGGER` 示例：

```bash
export AGENT_KB_TRIGGER="归档;复盘;[Ss]ave.thi"
```

非法正则片段会被忽略并回退到内置触发词 —— 环境变量写坏不会把 hook 拖挂。

---

## 适配新平台

1. 在 `hooks/` 下写一个 `<platform>_adapter.py`，import `kb_core`，按平台要求的 stdout 格式包装返回值
2. 在 `templates/` 下写 `<platform>-hooks.json`，注册两个事件：`SessionStart` 和 `UserPromptSubmit`
3. 在 README "安装" 节加一行说明

就这么简单。

---

## 设计决策记录

| 决策 | 选择 | 理由 |
|---|---|---|
| 库格式 | 纯 Markdown + frontmatter | 零依赖，人类和 Agent 都能直接读写 |
| 钩子时机 | SessionStart + UserPromptSubmit | 开工前提醒，收工时拦截沉淀意图 |
| 触发方式 | 正则自过滤 | 平台 matcher 对自定义触发词不友好 |
| 钩子输出 | 适配器决定 JSON 格式 | 各平台消费格式不同 |
| 错误处理 | 静默 exit 0 | 钩子是"增强"不是"必须"，绝不能阻塞主会话 |

---

## License

MIT
