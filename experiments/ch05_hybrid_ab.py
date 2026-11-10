# -*- coding: utf-8 -*-
"""对照词面余弦、BM25 与 RRF 混合召回；命中按 chunk 判定。"""
import re, math
from pathlib import Path
from collections import Counter
from pypdf import PdfReader

pdf = Path("data/raw/窗式空调安装说明书.pdf")
pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
lines = []

CHUNK, MIN = 300, 20
chunks = []
for i, t in enumerate(pages):
    if len(t.strip()) < MIN:
        continue
    for s in range(0, len(t), CHUNK):
        chunks.append({"id": len(chunks), "page": i + 1,
                       "text": t[s:s + CHUNK]})
lines.append("chunks_after_gate: " + str(len(chunks)))

CJK = r"[\u4e00-\u9fff]+"
ALNUM = r"[A-Za-z0-9./()\-]{2,}"

def mixed_tokens(s):
    out = []
    for m in re.finditer(ALNUM + "|" + CJK, s):
        seg = m.group()
        if re.match(r"[A-Za-z0-9]", seg):
            low = seg.lower()
            out.append(low)
            out += re.findall(r"[a-z]{2,}|\d+", low)
        else:
            out += [seg[j:j+2] for j in range(len(seg)-1)]
    return out

docs = [mixed_tokens(c["text"]) for c in chunks]
N = len(docs)

def cos(a, b):
    ca, cb = Counter(a), Counter(b)
    dot = sum(ca[k]*cb[k] for k in ca.keys() & cb.keys())
    na = math.sqrt(sum(v*v for v in ca.values()))
    nb = math.sqrt(sum(v*v for v in cb.values()))
    return dot/(na*nb) if na and nb else 0.0

df = Counter()
for d in docs:
    df.update(set(d))
avgdl = sum(len(d) for d in docs) / N
K1, B = 1.5, 0.75

def bm25(q, i):
    d = docs[i]
    tf, dl = Counter(d), len(d)
    s = 0.0
    for t in set(mixed_tokens(q)):
        if df[t] == 0:
            continue
        idf = math.log(1 + (N - df[t] + 0.5)/(df[t] + 0.5))
        s += idf * (tf[t]*(K1+1))/(tf[t] + K1*(1 - B + B*dl/avgdl))
    return s

def rrf(rank_lists, k=60):
    score = Counter()
    for rl in rank_lists:
        for rank, cid in enumerate(rl):
            score[cid] += 1.0/(k + rank + 1)
    return sorted(score, key=lambda x: -score[x])

QUERIES = [
    ("KCD-46型窗机电加热额定功率是多少瓦?", "3600"),
    ("空调器与可燃表面间的最小间隙是多少?", "1.5"),
    ("本机使用哪种制冷剂?", "R410A"),
    ("能用手机App或WiFi控制吗?", None),
    ("保修期是几年?", None),
]

def rank_cos(q):
    return sorted(range(N), key=lambda i: -cos(mixed_tokens(q), docs[i]))

def rank_bm(q):
    return sorted(range(N), key=lambda i: -bm25(q, i))

def rank_hybrid(q):
    return rrf([rank_cos(q), rank_bm(q)])

def evaluate(name, ranker):
    lines.append("=== " + name + " ===")
    for q, gold in QUERIES:
        order = ranker(q)
        top3 = [(chunks[i]["page"], chunks[i]["id"],
                 (gold in chunks[i]["text"]) if gold else False)
                for i in order[:3]]
        lines.append("Q: " + q)
        lines.append("  top3(page,chunk_id,has_gold)=" + str(top3))
        if gold is None:
            lines.append("  NOTE: 语料中无此问题的答案；top1 仅作观察")
            continue
        ranks = [r for r, i in enumerate(order) if gold in chunks[i]["text"]]
        mrr = 1.0/(ranks[0]+1) if ranks else 0.0
        lines.append("  gold=" + str(gold)
                     + " hit@1=" + str(gold in chunks[order[0]]["text"])
                     + " hit@3=" + str(any(gold in chunks[i]["text"] for i in order[:3]))
                     + " MRR=" + str(round(mrr, 3)))

evaluate("A cosine(mixed-token)", rank_cos)
evaluate("B bm25(k1=1.5,b=0.75)", rank_bm)
evaluate("C RRF(k=60) hybrid", rank_hybrid)
lines.append("NOTE: 命中按 chunk 判定，不按页判定。")
lines.append("NOTE: 融合用 RRF，因 cosine 与 BM25 量纲不同，不做分数归一化。")

out = Path("logs/ch05_hybrid_ab.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")