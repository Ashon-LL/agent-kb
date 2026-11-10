# ADR-0007: 纯 Markdown + 标准库，零第三方依赖

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

经验库需要跨项目、跨平台、可读、可审计、可迁移。
向量数据库或 SaaS 记忆服务会绑定平台/租户，且不可直接 grep。
但纯 Markdown 检索能力有限，需要接受规模与语义检索的取舍。

## Decision

- 存储：纯 Markdown + frontmatter；分类 `tools/` `workflow/` `pitfalls/`；索引 `INDEX.md`。
- 运行时：Python 标准库，零第三方依赖；安装只走 `scripts/install.*`，无 pip 包。
- 检索：关键词/症状词/IDF 排序；不引入向量库。
- 跨平台：适配器只做协议转换，共享 `kb_core.py` 唯一真相源。

## Consequences

- 人类可直接 `cat`，Git 可 diff，迁移只需拷贝目录。
- 没有语义相似检索；同义改写可能漏召回，需要触发词与 `--similar` 补位。
- 298 条规模下性能足够；更大规模需重新评估 FTS5/向量方案。
- 依赖平台能力时要写适配器，不能假设所有平台同一套 hook。

## Alternatives considered

- **向量数据库**：不可读、需部署、绑定平台，已否决。
- **SQLite/FTS5**：可作为规模化选项，但当前收益低，暂不引入。
- **SaaS 记忆服务**：数据不在用户手里，已否决。

## References

- `hooks/kb_core.py`
- `hooks/kb_search.py`
- `skill/SKILL.md`