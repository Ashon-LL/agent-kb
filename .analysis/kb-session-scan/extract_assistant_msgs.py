# -*- coding: utf-8 -*-
"""提取 assistant 消息文本（全会话分析的第二半）。

user 已提取（user_msgs.jsonl 4129 条 real_user）。
本脚本提取 assistant 的 text part，供「全会话」口径的漏沉淀检测。
输出：assistant_msgs.jsonl（s/t/x 同结构）
"""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path.home() / ".zcode/cli/db/db.sqlite"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assistant_msgs.jsonl")

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
cur = con.cursor()

keep = set()
n_all = 0
for mid, data in cur.execute("SELECT id, data FROM message"):
    try:
        d = json.loads(data)
    except Exception:
        continue
    if d.get("role") != "assistant":
        continue
    n_all += 1
    keep.add(mid)
print(f"assistant 消息 {n_all} 条")

texts = {}
for mid, data in cur.execute("SELECT message_id, data FROM part"):
    if mid not in keep:
        continue
    try:
        d = json.loads(data)
    except Exception:
        continue
    if d.get("type") == "text" and d.get("text"):
        texts.setdefault(mid, []).append(d["text"])

times, sess = {}, {}
for mid, sid, data in cur.execute("SELECT id, session_id, data FROM message"):
    if mid not in keep:
        continue
    sess[mid] = sid
    try:
        times[mid] = (json.loads(data).get("time") or {}).get("created", 0)
    except Exception:
        times[mid] = 0

n_w = n_c = 0
with open(OUT, "w", encoding="utf-8") as f:
    for mid, chunks in texts.items():
        text = "\n".join(chunks).strip()
        if not text:
            continue
        f.write(json.dumps({"s": sess.get(mid, ""), "t": times.get(mid, 0),
                            "x": text}, ensure_ascii=False) + "\n")
        n_w += 1
        n_c += len(text)
print(f"写出 {n_w} 条 / {n_c:,} 字符 -> {OUT}")
con.close()
