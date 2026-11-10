# -*- coding: utf-8 -*-
"""对照两种 token 化方式；不下载模型，日志以 UTF-8 落盘。"""
import re, math
from pathlib import Path
from collections import Counter
from pypdf import PdfReader

pdf = Path("data/raw/窗式空调安装说明书.pdf")
pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
lines = []

# 与 loader_ab.py 相同的低文本页门禁
CHUNK, MIN = 300, 20
chunks = []
for i, t in enumerate(pages):
    if len(t.strip()) < MIN:
        continue
    for s in range(0, len(t), CHUNK):
        chunks.append({"page": i + 1, "text": t[s:s + CHUNK]})
lines.append("chunks_after_gate: " + str(len(chunks)))

CJK = r"[\u4e00-\u9fff]+"
ALNUM = r"[A-Za-z0-9./()\-]{2,}"

def toks_a(s):
    s = re.sub(r"\s+", "", s)
    return [s[j:j + 2] for j in range(len(s) - 1)]

def toks_b(s):
    out = []
    for m in re.finditer(ALNUM + "|" + CJK, s):
        seg = m.group()
        if re.match(r"[A-Za-z0-9]", seg):
            low = seg.lower()
            out.append(low)
            out += re.findall(r"[a-z]{2,}|\d+", low)
        else:
            out += [seg[j:j + 2] for j in range(len(seg) - 1)]
    return out

def cos(a, b):
    ca, cb = Counter(a), Counter(b)
    dot = sum(ca[k] * cb[k] for k in ca.keys() & cb.keys())
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (na * nb) if na and nb else 0.0

QUERIES = [
    ("KCD-46型窗机电加热额定功率是多少瓦?", "3600"),
    ("空调器与可燃表面间的最小间隙是多少?", "1.5"),
    ("本机使用哪种制冷剂?", "R410A"),
    ("能用手机App或WiFi控制吗?", None),
    ("保修期是几年?", None),
]

for name, tokf in [("A char-bigram", toks_a), ("B mixed-token", toks_b)]:
    lines.append("=== " + name + " ===")
    for q, gold in QUERIES:
        sc = sorted(((cos(tokf(q), tokf(c["text"])), c) for c in chunks),
                    key=lambda x: -x[0])
        top = [c["page"] for _, c in sc[:3]]
        hit1 = gold is not None and gold in sc[0][1]["text"]
        hit3 = gold is not None and any(gold in c["text"] for _, c in sc[:3])
        lines.append("Q: " + q)
        lines.append("  top3_pages=" + str(top) + " top1_score=" + str(round(sc[0][0], 3)))
        lines.append("  gold=" + str(gold) + " hit@1=" + str(hit1) + " hit@3=" + str(hit3))
        if gold is None:
            lines.append("  NOTE: 语料中无此问题的答案")

out = Path("logs/ch04_tokenizer_ab.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")