---
name: zcode-session-context-pruning-sqlite
description: ZCode 会话超上下文时直接改 cli/db/db.sqlite 的 part 表裁剪；活跃上下文=最后一次 completed compaction 之后的 part；tool metadata 常比 output 大；改前备份受影响行，改后重启 ZCode
type: tool
source: 本机实测 sess_3b1515a6（2026-11-16，输入 1.2M tokens 超限，compaction 连续 failed；裁剪后 tail 8.99MB→1.50MB）
date: 2026-11-16
verified: 2026-11-16
topic: zcode, llm
---

# ZCode 会话超上下文：直接裁剪 db.sqlite

## 经验

- 会话正文在 `~/.zcode/cli/db/db.sqlite`，三张表：`session` / `message` / `part`。
  文本、工具调用与输出都在 `part.data` 的 JSON 里；`message.data` 只是角色/模型/用量等元数据。
- **活跃上下文 = 最后一次 `timelineStatus='completed'` 的 compaction 的 `message.sequence` 之后的 parts**。
  `failed` / `interrupted` 的 compaction 不重置边界；compaction 失败时 ZCode 会继续拿全量 tail 重试，形成死循环。
- tail 里 **tool 的 `state.metadata` 可能远大于 `state.output`**：实测 703 条 tool part 中 metadata 5.18MB、output 仅 1.26MB。只裁 output 效果有限，必须同时处理 metadata。
- 可行的激进裁剪（仅 tail）：
  - `state.output` → 前 200 字符 + `...[tool output pruned to fit context: original N chars]...`
  - `state.metadata` → `{}`
  - `reasoning.text` → 一行 `[reasoning pruned to fit context: original N chars]`
  - 保留 `text`（用户/助手正文）、`step-*`、`timeline`
  实测 tail 8.99MB → 1.50MB，`pragma quick_check` = ok，message/part 行数不变。
- ZCode 的 token/字符比约为 **8 chars/token**（实测 tail 8.99MB ↔ 1,118,172 tokens），不要按 4 chars/token 估算裁剪量。

## Why

compaction 请求本身已经超过模型上限时（如 1.2M > 1.05M），压缩永远无法成功；必须先让原始 tail 降到上限以下，compaction 才有机会跑完。直接删会话会丢历史，所以最小侵入是原地裁剪 part 内容。

## How to apply

1. 定位会话与边界：
   ```sql
   select id,title from session where id='sess_xxx';
   select p.time_created,m.sequence,json_extract(p.data,'$.timelineStatus')
   from part p join message m on m.id=p.message_id
   where p.session_id='sess_xxx'
     and json_extract(p.data,'$.type')='compaction'
   order by p.time_created;
   ```
   取最后一个 `timelineStatus='completed'` 的 `sequence`。
2. 统计 tail 各 type 的 output/input/metadata 大小，确认大头（通常 tool metadata）。
3. 把要改的 `part` 行 `id,data` 导出 JSON 备份；回滚按 `id` UPDATE `part.data`。
4. 在事务里 UPDATE `part.data`（保持 JSON 结构，只替换字符串字段），提交后 `pragma quick_check`。
5. **重启 ZCode / 重开该会话**，上下文从 DB 重建；重启前不要在该会话发新消息，否则可能用内存旧上下文再失败。

相关：[[zcode-session-delete-is-soft-delete-two-dbs]]、[[zcode-session-db-real-user-extraction]]、[[renderer-reload-is-not-context-loss]]。
