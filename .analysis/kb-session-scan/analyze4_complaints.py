# -*- coding: utf-8 -*-
"""全会话分析 · 方向 A：用户反复纠正/抱怨 = 该沉淀但没生效的信号。

从 user 消息里提取：
  1) 遗忘指责（忘了吗/不是说了/说过很多次）
  2) 重复犯错（又错/怎么还/你总是/第N次）
  3) 明确订正（我说的不是/搞错了/回撤）
对每条提取主题词，与 kb 库比对覆盖情况。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

KB = Path.home() / ".agents/kb"
OUT = Path.home() / ".zcode/workspace/kb-analysis"

# 载入 kb 全文（用于覆盖比对）
kb_text = ""
for d in ("pitfalls", "tools", "workflow"):
    for f in (KB / d).glob("*.md"):
        kb_text += f.read_text(encoding="utf-8")
kb_text += (KB / "INDEX.md").read_text(encoding="utf-8")
print(f"kb 全文 {len(kb_text):,} 字符（{len(list((KB/'pitfalls').glob('*.md'))+list((KB/'tools').glob('*.md'))+list((KB/'workflow').glob('*.md')))} 条）")

rows = []
for line in open(OUT / "user_msgs.jsonl", encoding="utf-8"):
    o = json.loads(line)
    if re.match(r"^sess_[0-9a-f]{8}-", o["s"] or ""):
        rows.append(o["x"])
uniq = list(dict.fromkeys(rows))

GROUPS = {
    "遗忘指责": r"忘了吗|忘了\?|不是说了|说过很多次|说了很多次|之前说过|我早说|不是说过",
    "重复犯错": r"又错|又失败|怎么还|你总是|又是这样|第[二三四五六七八九]次|又没|还是没",
    "明确订正": r"搞错了|你错了|不对吧|回撤|撤回|订正|不是这个意思|理解错",
    "失望不满": r"失望|不聪明|越做越错|一点都不|真没用|太失望",
}
buckets = {}
for label, pat in GROUPS.items():
    rx = re.compile(pat)
    buckets[label] = [t for t in uniq if rx.search(t)]

for label, items in buckets.items():
    print(f"\n{'='*68}\n【{label}】{len(items)} 条\n{'='*68}")
    for t in items[:14]:
        print("  ·", t.replace("\n", " ⏎ ")[:160])

# 主题词提取：这些抱怨里反复出现的名词（判断哪些领域反复出问题）
allbad = []
for items in buckets.values():
    allbad.extend(items)
cnt = Counter()
for t in allbad:
    for w in re.findall(r"[\u4e00-\u9fff]{2,4}", t):
        cnt[w] += 1
print("\n\n=== 抱怨消息里高频中文词 top 40（粗粒度主题信号）===")
interesting = [w for w, c in cnt.most_common(200) if c >= 3][:40]
print("  " + "  ".join(interesting))
