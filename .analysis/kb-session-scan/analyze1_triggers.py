# -*- coding: utf-8 -*-
"""分析第一步：现有 TRIGGER_PATTERN 在全部历史用户消息上的表现。

输出：
  1) 总体命中率
  2) 命中样本（看是否误报）
  3) 未命中但含 kb 相关词的样本（看是否漏报）
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents/kb"))
from kb_core import TRIGGER_PATTERN  # 用生产正本，避免两份拷贝漂移

MSGS = Path(sys.argv[1] if len(sys.argv) > 1 else "user_msgs.jsonl")

# 宽预筛：任何可能与 kb/沉淀相关的词（用来找出「该触发但没触发」的候选）
WIDE = re.compile(
    r"kb|经验|知识库|教训|沉淀|记住|记录|笔记|归档|存|复盘|坑|最佳实践|引以为戒|"
    r"下次注意|别再|不要再|以后别|学到|总结|入库|收录|提升|改进|优化|规范|规矩|纪律",
    re.I)

hits, wide_only = [], []
n = 0
for line in open(MSGS, encoding="utf-8"):
    o = json.loads(line)
    t = o["x"]
    n += 1
    if TRIGGER_PATTERN.search(t):
        hits.append(t)
    elif WIDE.search(t):
        wide_only.append(t)

print(f"总消息 {n}")
print(f"现有 TRIGGER_PATTERN 命中: {len(hits)} 条（{len(hits)/n:.1%}）")
print(f"未命中但含宽相关词: {len(wide_only)} 条")
print()

print("=" * 70)
print("命中样本（最多 40 条，检查误报）")
print("=" * 70)
for t in hits[:40]:
    print("  ·", t.replace("\n", " ⏎ ")[:150])

print()
print("=" * 70)
print(f"宽预筛未命中样本（{len(wide_only)} 条，前 60 条）")
print("=" * 70)
for t in wide_only[:60]:
    print("  ·", t.replace("\n", " ⏎ ")[:150])
