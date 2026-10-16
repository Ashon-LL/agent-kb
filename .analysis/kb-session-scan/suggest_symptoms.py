# -*- coding: utf-8 -*-
"""① 症状词 → 条目 映射建议（2026-10-16）。

判定：症状词在条目 description 或正文出现（说明该条确实讲这个症状），
但 INDEX 钩子未包含它 ⇒ 检索层漏命中，建议补进钩子。
"""
import re
from pathlib import Path

KB = Path.home() / ".agents/kb"
SYMPTOMS = ["我以为", "应该是", "忘了吗", "又错", "搞错", "说过很多次", "不是说了",
            "越做越错", "失望", "不聪明", "卡住", "挂了", "没反应", "对不上",
            "往返", "回撤", "没用"]

idx = (KB / "INDEX.md").read_text(encoding="utf-8")
hooks = {}
for line in idx.splitlines():
    m = re.match(r"^\s*[-*]\s+\[([^\]]*)\]\(([^)]+)\)\s*[—-]?\s*(.*)$", line)
    if m:
        hooks[m.group(2).strip().replace("\\", "/")] = m.group(3)

suggestions = {}
for d in ("pitfalls", "tools", "workflow"):
    for f in sorted((KB / d).glob("*.md")):
        body = f.read_text(encoding="utf-8")
        rel = f"{d}/{f.name}"
        hook = hooks.get(rel, "")
        # description 单独取（权重高）
        dm = re.search(r"^description:\s*(.*)$", body, re.M)
        desc = dm.group(1) if dm else ""
        for w in SYMPTOMS:
            if w in hook:
                continue
            in_desc = w in desc
            n_body = body.count(w)
            if in_desc or n_body >= 2:
                suggestions.setdefault(w, []).append(
                    (rel, "desc" if in_desc else f"正文×{n_body}"))

print("=== 症状词 → 建议补钩子的条目 ===")
for w in SYMPTOMS:
    items = suggestions.get(w, [])
    if not items:
        print(f"\n{w}：（无建议）")
        continue
    print(f"\n{w}（{len(items)} 条）:")
    for rel, why in items[:6]:
        print(f"    {rel}   [{why}]")
