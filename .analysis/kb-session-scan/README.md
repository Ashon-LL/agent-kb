# kb 会话全量扫描（2026-10-16）

用户任务：「全量扫描所有会话文件（含删除/归档/还在的），根据会话内容尤其是我所说的，
优化 agent-kb 的匹配词 / 优化 agent-kb」。

## 数据源与方法

- **源**：`~/.zcode/cli/db/db.sqlite`（906MB / 53924 条消息）。
  「全量」天然成立：ZCode 的删除/归档是纯软删（状态只在 `v2/tasks-index.sqlite`），
  正文库**没有任何删除标记**，已删/已归档/在用的会话全在里面。
- **真用户消息过滤**（两条件）：
  1. `message.data.semantics.origin == 'real_user'`（排除 agent_runtime/system 注入）
  2. `session_id` 匹配 `^sess_[0-9a-f]{8}-`（**顶层会话**）
     ⛔ 必须剔 `sess_dwf-*`（工作流 actor）与 `sess_subagent*`——子代理任务书
     也被标为 real_user（"你在分析经验库…"这类），不剔会污染分析。
- 结果：**real_user 4029 条**（去重 1208）、**assistant 25782 条**。

## 关键发现

1. **触发词缺口已修**（+52% 覆盖、零误报）：新增 纳入…kb/记忆、记入、订正记忆、
   修正kb、值得一记、记录下来、经验记录、教训（泛化）、状态确认疑问句（"…了吗"）、
   我希望/不希望（需求与约束声明）。
2. **更深的缺口在执行侧**：用户反复抱怨的主题（臆测不核实、跨项目忘同步、遗忘已定决定）
   kb 里**全都有条目** ⇒ 缺的不是「沉淀」而是「执行时吸取」（三层目的的第 2 层）。
3. **项目记忆 → kb 晋升通道断裂**（真案例）：「改仓库脚本必须同步 kb/tools 副本」
   （用户多次强调"跨项目使用"）此前只在项目记忆里躺着，从未进 kb——项目记忆只在
   单个项目的会话注入，所以跨会话永远"说了没生效"。已并入 hardlink 条目。

## 产物

| 文件 | 说明 |
|---|---|
| `extract_user_msgs.py` | 从会话库提取 real_user 消息 → `user_msgs.jsonl` |
| `extract_assistant_msgs.py` | 提取 assistant 文本 → `assistant_msgs.jsonl` |
| `analyze1_triggers.py` | 旧触发词在全量消息上的命中/漏报统计 |
| `analyze2_candidates.py` | 沉淀意图候选预筛（分四组）→ `candidates.txt` |
| `analyze3_coverage.py` | 候选词量化覆盖（新增覆盖 vs 误报对照） |
| `analyze4_complaints.py` | 抱怨/纠正聚类（找"该沉淀但没生效"的信号） |
| `*.jsonl` / `*.txt` | 数据文件（gitignore，可由脚本重建） |

## 复现

```bash
python extract_user_msgs.py user_msgs.jsonl
python extract_assistant_msgs.py assistant_msgs.jsonl
python analyze1_triggers.py user_msgs.jsonl   # 需要 ~/.agents/kb/kb_core.py 在位
python analyze3_coverage.py
```

## 局限

- 片段级"已覆盖/未覆盖"判定是 4-gram 粗匹配，被 kb 元对话污染（如 agent 讨论 kb 本身的
  消息），只能做线索不能做结论。
- 抱怨聚类含重复消息，计数看趋势不看绝对值。
