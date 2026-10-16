# -*- coding: utf-8 -*-
"""量化：候选触发词在全部真用户消息上的覆盖情况。

对每个候选表达统计：
  - 出现该表达的消息数
  - 其中「现有 TRIGGER_PATTERN 未命中」的数量（= 新增该词能多覆盖的）
并抽样打印漏网消息，人工确认是否真沉淀意图。
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".agents/kb"))
from kb_core import TRIGGER_PATTERN

MSGS = Path.home() / ".zcode/workspace/kb-analysis/user_msgs.jsonl"

# 候选表达（用户真实用词整理）
CANDIDATES = {
    # A 组：疑似高置信
    "纳入.*(kb|KB|知识库|记忆)": "纳入KB/记忆",
    "记入": "记入",
    "订正记忆": "订正记忆",
    "更新记忆": "更新记忆",
    "值得一记": "值得一记",
    "教训": "泛化教训",
    "经验(记录|沉淀|纳入)": "经验记录/沉淀",
    "记录(下来|一下)": "记录下来/一下",
    "写入(指南|kb|KB|记忆)": "写入指南/kb",
    "沉淀": "沉淀(已有)",
    "复盘": "复盘(已有)",
    "总结": "泛化总结",
    "跟进": "跟进(对照组·应非沉淀)",
    "纳入": "泛化纳入(对照组·含纳入号)",
    "回撤|撤回": "回撤/撤回(对照组)",
    "漏了|忘了|没记": "漏了/忘了(对照组)",
}

def is_top(sid: str) -> bool:
    return bool(re.match(r"^sess_[0-9a-f]{8}-", sid or ""))

rows = []
for line in open(MSGS, encoding="utf-8"):
    o = json.loads(line)
    if is_top(o["s"]):
        rows.append(o["x"])

print(f"真用户消息 {len(rows)} 条\n")
print(f"{'候选':28} {'命中':>5} {'其中未触发':>8}")
print("-" * 50)
samples = defaultdict(list)
for pat, label in CANDIDATES.items():
    rx = re.compile(pat, re.I)
    hit = [t for t in rows if rx.search(t)]
    missed = [t for t in hit if not TRIGGER_PATTERN.search(t)]
    print(f"{label:28} {len(hit):>5} {len(missed):>8}")
    samples[label] = missed

# 打印最值得看的新增覆盖样本
print("\n" + "=" * 70)
print("新增覆盖样本（A 组，每词最多 8 条）")
print("=" * 70)
for label in ("纳入KB/记忆", "记入", "订正记忆", "更新记忆", "值得一记", "经验记录/沉淀", "写入指南/kb"):
    ms = samples.get(label, [])
    if not ms:
        continue
    print(f"\n--- {label}（{len(ms)} 条）")
    for t in ms[:8]:
        print("   ·", t.replace("\n", " ⏎ ")[:140])

# 对照组：确认这些词不该进触发词
print("\n" + "=" * 70)
print("对照组（检查误报风险）")
print("=" * 70)
for label in ("泛化纳入(对照组·含纳入号)", "跟进(对照组·应非沉淀)", "泛化教训", "泛化总结"):
    ms = samples.get(label, [])
    print(f"\n--- {label}（未触发 {len(ms)} 条）")
    for t in ms[:6]:
        print("   ·", t.replace("\n", " ⏎ ")[:130])
