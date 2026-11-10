---
description: 检索或写入全局经验库（~/.agents/kb）。用法：/kb <关键词> 检索；/kb add <经验内容> 按规范写入。
argument-hint: "<关键词> 或 add <一条经验>"
---

操作全局经验知识库 `~/.agents/kb/`（先加载 kb 技能，按其中规程执行）。

用户输入：$ARGUMENTS

- 若以 `add ` 开头：把后面的内容作为一条经验，按 kb 技能的写入规程（判类、查重、frontmatter 七字段、更新 INDEX.md）写入 `~/.agents/kb/`，⛔ 然后**必须跑校验器**：

  ```bash
  python ~/.agents/kb/kb_validate.py
  ```

  看到 `[PASS]` 才算写完，回报时一并给出条目文件路径、索引行、校验器输出。报 `[FAIL]` 就按它列的行逐条修；⛔ 不要绕过、不要改校验器迁就条目、不要为了让它变绿而删条目。
- 否则视为检索关键词：读 `~/.agents/kb/INDEX.md` 并 grep 库内内容，返回最相关条目全文；没有命中就明确说无相关经验。