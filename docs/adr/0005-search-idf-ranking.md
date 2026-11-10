# ADR-0005: 检索叠加 IDF，保留命中词数优先

- Status: Accepted
- Date: 2026-11-10
- Deciders: ACHEN

## Context

检索原来只按字段权重排序：INDEX 钩子×3、description×2、正文×1。
“配置”“更新”这类高频词会压低精确条目的相对权重；
但纯 BM25 又会改变“命中词数优先”的既有行为，影响症状词检索。

## Decision

- 保留字段权重与“命中词数优先”排序。
- 叠加 IDF：`idf = ln(1 + (N - df + 0.5) / (df + 0.5))`，稀有词权重更高。
- 仍使用子串匹配（含正文症状词），不引入分词器或向量库。
- 排序键：先 `matched`（命中关键词数），再 `score`（字段权重 × IDF）。

## Consequences

- 稀有词（如具体错误码、专有名词）更容易排到前面。
- 高频词不会完全压死精确条目，但仍是软 AND，不会因缺词直接出局。
- 298 条规模下线性扫描足够快，不需要索引服务。
- 新增检索测试锁定“命中数优先”和 IDF 稀有词权重。

## Alternatives considered

- **纯 BM25**：会改变既有排序与测试契约，已否决。
- **向量检索**：违背零依赖与可 grep 原则，已否决。
- **SQLite FTS5**：可作为未来规模化方案，但当前收益低，暂不引入。

## References

- `hooks/kb_search.py`
- `tests/test_kb_search.py`