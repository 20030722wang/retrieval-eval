# -*- coding: utf-8 -*-
"""ch03 A/B: pypdf vs pymupdf on the same PDF. UTF-8 log, ASCII-only print."""
from pathlib import Path

pdf = Path("data/raw/窗式空调安装说明书.pdf")
lines = []

def report(tag, texts):
    all_text = "\n".join(texts)
    lines.append("=== " + tag + " ===")
    lines.append("pages: " + str(len(texts)))
    lines.append("total_chars: " + str(len(all_text)))
    for tok in ["KCD-46", "3600", "1.5", "三包", "包修卡", "R410A"]:
        pages = [str(i + 1) for i, t in enumerate(texts) if tok in t]
        lines.append("token " + repr(tok) + ": count=" + str(all_text.count(tok))
                     + " pages=" + (",".join(pages) or "NONE"))
    low = [str(i + 1) for i, t in enumerate(texts) if len(t.strip()) < 20]
    lines.append("low_text_pages(<20): " + (",".join(low) or "NONE"))
    return all_text

from pypdf import PdfReader
r = PdfReader(str(pdf))
report("pypdf", [p.extract_text() or "" for p in r.pages])

try:
    import pymupdf as mupdf
except ImportError:
    import fitz as mupdf
d = mupdf.open(str(pdf))
mt = [p.get_text() or "" for p in d]
report("pymupdf", mt)

# print a sample of the page that contains 3600, if any
for i, t in enumerate(mt):
    if "3600" in t:
        lines.append("--- pymupdf page " + str(i + 1) + " first 300 ---")
        lines.append(t[:300].replace("\n", " | "))
        break

out = Path("logs/ch03_parser_ab.txt")
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")