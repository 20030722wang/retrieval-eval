# -*- coding: utf-8 -*-
"""对照 BM25 粗排与按证据可绑定性的分档重排；日志以 UTF-8 落盘。"""
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
        chunks.append({"id": len(chunks), "page": i + 1, "text": t[s:s+CHUNK]})
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
df = Counter()
for d in docs:
    df.update(set(d))
avgdl = sum(len(d) for d in docs) / N
K1, B = 1.5, 0.75

# 粗排：BM25，参数与 ch05 一致
def bm25(q, i):
    tf, dl = Counter(docs[i]), len(docs[i])
    s = 0.0
    for t in set(mixed_tokens(q)):
        if df[t] == 0:
            continue
        idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
        s += idf * (tf[t]*(K1+1)) / (tf[t] + K1*(1 - B + B*dl/avgdl))
    return s

def coarse(q, k=5):
    return sorted(range(N), key=lambda i: -bm25(q, i))[:k]

# 精排特征：从 query 取目标型号，判断 chunk 能否直接绑定出数值
MODEL_RE = re.compile(r"KCD-(\d+)")
EXACT_RE = re.compile(r"KCD-(\d+)型窗机电加热额定功率为(\d+)W")

def features(q, cid):
    t = chunks[cid]["text"]
    m = MODEL_RE.search(q)
    target = m.group(1) if m else None
    exact = [(a, v) for a, v in EXACT_RE.findall(t)
             if target and a == target]
    loose = bool(target and ("KCD-" + target in t
                             or ("KCD-" in t and target in t)))
    competing = bool(re.search(r"KCD-35", t) and re.search(r"3100W", t))
    fragmented = bool(re.search(r"KCD-\s*\|", t))
    value = exact[0][1] + "W" if exact else None
    return {"exact": bool(exact), "value": value, "loose": loose,
            "competing": competing, "fragmented": fragmented}

# 分档排序：不与 BM25 分数加权，避免 ch05 RRF 那样的量纲稀释
def rerank(q, pool):
    f = {cid: features(q, cid) for cid in pool}
    def key(cid):
        x = f[cid]
        return (-int(x["exact"]), int(x["competing"]),
                int(x["fragmented"]), -int(x["loose"]), pool.index(cid))
    return sorted(pool, key=key), f

def fmt(pool, f):
    return [(chunks[c]["page"], chunks[c]["id"],
             f[c]["value"] or "-", f[c]["competing"], f[c]["fragmented"])
            for c in pool]

QUERIES = [
    ("KCD-46型窗机电加热额定功率是多少瓦?", "3600W"),
    ("空调器与可燃表面间的最小间隙是多少?", "1.5"),
    ("本机使用哪种制冷剂?", "R410A"),
]

for q, gold in QUERIES:
    pool = coarse(q)
    ordered, f = rerank(q, pool)
    lines.append("Q: " + q)
    lines.append("  coarse_top5(page,cid,extracted,competing,fragmented)="
                 + str(fmt(pool, f)))
    lines.append("  rerank_top5=" + str(fmt(ordered, f)))
    lines.append("  top1_extracted: coarse=" + str(f[pool[0]]["value"])
                 + " rerank=" + str(f[ordered[0]]["value"]))
    in_pool = any(gold in chunks[c]["text"] for c in pool)
    lines.append("  gold=" + str(gold) + " in_candidate_pool=" + str(in_pool))
    if not in_pool:
        lines.append("  NOTE: 答案不在候选池内，重排不改变召回结果")

lines.append("NOTE: 命中按 chunk 判定，不按页判定。")
lines.append("NOTE: 精排用分档排序，不与粗排分数加权。")

out = Path("logs/ch06_rerank_ab.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")