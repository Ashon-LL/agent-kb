---
description: 从 ZCode 会话库、当前工作区与其他平台 memory 收割跨项目经验；ZCode 项目记忆关闭时仍可用。
argument-hint: "[可选：指定扫描的项目路径或时间范围]"
---

执行一次全局经验收割。**只产出候选清单，未经用户确认不得写入。**

> 快速生成候选：`python ~/.agents/kb/kb_harvest.py --days 7`
> 报告默认写到 `~/.agents/kb/HARVEST-CANDIDATES.md`；该脚本只读，不写入库。

## 来源（按优先级）

1. **ZCode 会话库（主来源，项目记忆关闭时仍可用）**
   - 路径：`~/.zcode/cli/db/db.sqlite`，**只读**打开（`mode=ro`）。
   - 只取 `session_id` 匹配 `^sess_[0-9a-f]{8}-` 的顶层会话。
   - 只取 `message.data.semantics.origin == "real_user"` 的消息。
   - 排除 `sess_dwf-*`、`sess_subagent*` 与 agent 运行时注入。
   - 默认看最近 7 天；用户给了 `$ARGUMENTS` 时按指定范围/路径。
   - 先按 `message.time_created` 做时间过滤，再读对应 `part` 的 `text`，不要全表扫。
2. **当前工作区**
   - 以本会话工作目录为根，扫描文件名含「指南、手册、上手、给其他项目、交接、总结、复盘、教训」的 md。
   - 以及 `docs/`、`notes/`、`交付/`、`.analysis/` 等文档目录。
   - 当前目录为空沙箱时，停下问用户要路径，或让用户在 `$ARGUMENTS` 指定，不要瞎扫。
3. **其他平台项目记忆（可选）**
   - Trae：`~/.trae-cn/memory/projects/*/`；Claude：`~/.claude/` 等。
   - **ZCode 项目记忆已关闭**：`~/.zcode/cli/memories/projects/` 为空时不要把它当必需来源。

## 步骤

1. 先检查会话库是否存在、`message` / `part` 表是否可读；缺失或不可读时降级到来源 2/3，并明确告知用户。
2. 按 kb 收录标准筛选：**跨项目可复用**的经验/教训/方法才入选；项目专属状态（进度、布局、待办）剔除；已在 `INDEX.md` 存在的跳过。
3. 输出候选清单给用户过目，格式：`来源 | 拟入目录 | 标题 | 一句话理由`。到此为止，**不要未经确认直接写入**。
4. 用户确认后（可能只确认部分），逐条按 kb 写入规程落盘：
   - 判类：`tools/` / `workflow/` / `pitfalls/`
   - 查重：`python ~/.agents/kb/kb_search.py --similar "<候选标题或一句话描述>"`
   - 写条目：frontmatter **七字段齐全**（`name` `description` `type` `source` `date` `verified` `topic`），正文三段式（经验 / Why / How to apply）
   - 更新 `INDEX.md`
5. 全部落盘后跑校验器（写入当下硬门）：
   - 本机运行时：`python ~/.agents/kb/kb_validate.py`
   - 仓库内开发：`python hooks/kb_validate.py`（cwd = `agent-kb`）
   - Windows 先 `set PYTHONUTF8=1`；必须看到 `[PASS]` 才算完。
6. 若参数含 `--push` 且用户已逐条确认：全部写入 + 校验 PASS 后，按 `commands/kb.md` 的显式发布流程运行 `kb_publish.py`；没有 `--push` 一律不推送。
7. 汇报最终写入的条目路径、索引总行数、校验器输出、是否本地提交/推送。
8. ⛔ 不读密钥/凭据；不写会话库；不自动删除原项目 memory；不自动推送。