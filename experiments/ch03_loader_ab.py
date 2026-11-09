# -*- coding: utf-8 -*-
"""ch03 A/B: naive chunks vs loader quality gate. UTF-8 log, ASCII-only print."""
import re
from pathlib import Path
from pypdf import PdfReader

pdf = Path("data/raw/窗式空调安装说明书.pdf")
pages = [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]
lines = []
PRINTED = re.compile(r"-(\d+)-")

def printed_page(t):
    m = PRINTED.search(t)
    return int(m.group(1)) if m else None

CHUNK = 300

# A: naive fixed-length, every page enters retrieval
a = []
for i, t in enumerate(pages):
    for s in range(0, len(t), CHUNK):
        a.append({"pdf_page": i + 1, "text": t[s:s + CHUNK]})
lines.append("=== A naive fixed-length ===")
lines.append("total_chunks: " + str(len(a)))
lines.append("low_quality_chunks_entering_retrieval: "
             + str(sum(1 for c in a if len(c["text"].strip()) < 20)))

# B: loader quality gate + page-id normalization
b, skipped = [], []
for i, t in enumerate(pages):
    if len(t.strip()) < 20:
        skipped.append(i + 1)
        continue
    pp = printed_page(t)
    for s in range(0, len(t), CHUNK):
        b.append({"pdf_page": i + 1, "printed_page": pp, "text": t[s:s + CHUNK]})
lines.append("=== B loader quality gate ===")
lines.append("total_chunks: " + str(len(b)))
lines.append("skipped_low_text_pages: " + ",".join(map(str, skipped)))
lines.append("chunks_with_printed_page: "
             + str(sum(1 for c in b if c["printed_page"])) + "/" + str(len(b)))

# page-id correction evidence
for i, t in enumerate(pages):
    if "3600" in t:
        lines.append("token 3600 -> pdf_page=" + str(i + 1)
                     + " printed_page=" + str(printed_page(t)))
        lines.append("  sample: " + t[:200].replace("\n", " | "))

QUERIES = [
    ("空调器与可燃表面间的最小间隙是多少?", ["1.5"]),
    ("KCD-46型窗机电加热额定功率是多少瓦?", ["3600"]),
    ("能用手机App或WiFi控制吗?", []),
    ("保修期是几年?", []),
]
def naive(tokens):
    hits = [c for c in a if any(k in c["text"] for k in tokens)]
    return ("answered pdf_page=" + str(hits[0]["pdf_page"])) if hits \
        else "answered_with=first_chunk -- NO EVIDENCE, NO REFUSAL"
def gated(tokens):
    hits = [c for c in b if any(k in c["text"] for k in tokens)]
    if hits:
        return ("answered pdf_page=" + str(hits[0]["pdf_page"])
                + " printed_page=" + str(hits[0]["printed_page"]))
    return "REFUSED: no supporting chunk (low-text pages gated out)"

lines.append("=== query behavior A vs B ===")
for q, toks in QUERIES:
    lines.append("Q: " + q)
    lines.append("  A: " + naive(toks))
    lines.append("  B: " + gated(toks))

out = Path("logs/ch03_loader_ab.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")