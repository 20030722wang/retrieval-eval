# -*- coding: utf-8 -*-
"""打印 Q3 在两路召回里的 rank 与 RRF 分项。"""
import re, math, importlib.util
from pathlib import Path
from collections import Counter

spec = importlib.util.spec_from_file_location("m", "experiments/ch05_hybrid_ab.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

q = "本机使用哪种制冷剂?"
a, b = m.rank_cos(q), m.rank_bm(q)
lines = ["query: " + q, "RRF k=60, rank1=1/61, rank2=1/62"]
for cid in [5, 14, 12, 9, 22, 4, 7]:
    ra = a.index(cid) + 1 if cid in a else 999
    rb = b.index(cid) + 1 if cid in b else 999
    sa = 1.0/(60+ra) if ra < 999 else 0.0
    sb = 1.0/(60+rb) if rb < 999 else 0.0
    lines.append("chunk " + str(cid)
                 + " rank_cos=" + str(ra) + " rank_bm25=" + str(rb)
                 + " rrf=" + str(round(sa+sb, 6))
                 + " has_gold=" + str("R410A" in m.chunks[cid]["text"]))
out = Path("logs/ch05_rrf_diagnose.txt")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out)