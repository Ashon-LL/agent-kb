# -*- coding: utf-8 -*-
"""提取 ZCode 全部真实用户消息（含已删/已归档会话）到 JSONL。

数据源：~/.zcode/cli/db/db.sqlite（全部正文，无删除标记——软删只在 tasks-index）
过滤：message.role=='user' 且 semantics.origin=='real_user'（排除子代理/系统注入）
输出：每行 {"s": session_id, "t": 时间戳, "x": 文本}
只读打开，不写源库。
"""
import json
import sqlite3
import sys
from pathlib import Path

DB = Path.home() / ".zcode/cli/db/db.sqlite"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("user_msgs.jsonl")

con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
cur = con.cursor()

# 先收集 real_user 的 message id 集合（role=user 且 origin=real_user）
keep = set()
skipped_origin = {}
total_user = 0
for mid, data in cur.execute("SELECT id, data FROM message"):
    try:
        d = json.loads(data)
    except Exception:
        continue
    if d.get("role") != "user":
        continue
    total_user += 1
    origin = (d.get("semantics") or {}).get("origin", "?")
    if origin == "real_user":
        keep.add(mid)
    else:
        skipped_origin[origin] = skipped_origin.get(origin, 0) + 1

print(f"user 消息 {total_user} 条；real_user {len(keep)} 条")
print(f"按 origin 跳过: {skipped_origin}")

# 提取正文（part.type=='text'），按 message 聚合
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

# 时间戳
times = {}
for mid, data in cur.execute("SELECT id, data FROM message"):
    if mid not in keep:
        continue
    try:
        t = json.loads(data).get("time") or {}
        times[mid] = t.get("created", 0)
    except Exception:
        times[mid] = 0

# 会话归属
sess = {}
for mid, sid in cur.execute("SELECT id, session_id FROM message"):
    if mid in keep:
        sess[mid] = sid

n_written = 0
n_chars = 0
with open(OUT, "w", encoding="utf-8") as f:
    for mid, chunks in texts.items():
        text = "\n".join(chunks).strip()
        if not text:
            continue
        f.write(json.dumps({"s": sess.get(mid, ""), "t": times.get(mid, 0), "x": text},
                           ensure_ascii=False) + "\n")
        n_written += 1
        n_chars += len(text)

print(f"已写出 {n_written} 条 / {n_chars:,} 字符 -> {OUT}")
con.close()
