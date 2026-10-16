# -*- coding: utf-8 -*-
"""从顶层会话（真用户）消息里预筛「沉淀/经验管理意图」候选集。

输出两个文件：
  candidates.txt  —— 预筛命中的消息（供人工判读，带上下文）
  stats.txt       —— 各类命中计数
预筛故意放宽（宁可多捞），精确判断留给人读。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

MSGS = Path.home() / ".zcode/workspace/kb-analysis/user_msgs.jsonl"
OUT = Path.home() / ".zcode/workspace/kb-analysis"

def is_top(sid: str) -> bool:
    return bool(re.match(r"^sess_[0-9a-f]{8}-", sid or ""))

# 分组预筛（各自独立计数，一条消息可命中多组）
GROUPS = {
    "G1_直接沉淀指令": re.compile(r"记住|记下|记一下|记一笔|沉淀|入库|纳入|收录|归档到|写进|存起来|存进|记录下来"),
    "G2_教训复盘": re.compile(r"教训|复盘|总结一下|反思|引以为戒|下次注意|以后注意|别再犯|不要再犯|别再|以后别|学到"),
    "G3_kb直指": re.compile(r"\bkb\b|知识库|经验库|全局经验|INDEX", re.I),
    "G4_规范纪律": re.compile(r"规范|规矩|纪律|原则|约定|标准做法|最佳实践|值得记|要记"),
}

buckets = {k: [] for k in GROUPS}
n = 0
for line in open(MSGS, encoding="utf-8"):
    o = json.loads(line)
    if not is_top(o["s"]):
        continue
    n += 1
    t = o["x"]
    for k, rx in GROUPS.items():
        if rx.search(t):
            buckets[k].append((o["t"], t))

print(f"顶层会话消息 {n} 条")
with open(OUT / "stats.txt", "w", encoding="utf-8") as f:
    for k in GROUPS:
        print(f"  {k}: {len(buckets[k])} 条")
        f.write(f"{k}: {len(buckets[k])}\n")

# 全部候选去重写出（按时间排序）
seen = set()
with open(OUT / "candidates.txt", "w", encoding="utf-8") as f:
    for k in GROUPS:
        f.write(f"\n{'='*70}\n===== {k}（{len(buckets[k])} 条）\n{'='*70}\n")
        for t, text in sorted(buckets[k]):
            if text in seen:
                continue
            seen.add(text)
            f.write("\n---\n" + text.strip()[:600] + "\n")
print("候选已写出 -> candidates.txt（去重后 %d 条）" % len(seen))
