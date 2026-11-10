# -*- coding: utf-8 -*-
"""检查 PDF 文本层覆盖率与关键标识所在页。"""
from pathlib import Path
from pypdf import PdfReader

pdf = Path("data/raw/窗式空调安装说明书.pdf")
out = Path("logs/ch03_probe.txt")
lines = []

if not pdf.exists():
    lines.append("MISSING: " + str(pdf))
else:
    r = PdfReader(str(pdf))
    lines.append("pages: " + str(len(r.pages)))
    texts = []
    for i, p in enumerate(r.pages):
        t = p.extract_text() or ""
        texts.append(t)
        lines.append("page " + str(i + 1) + ": chars=" + str(len(t)))
    all_text = "\n".join(texts)
    for tok in ["KCD-46", "3600", "1.5", "三包", "包修卡", "R410A"]:
        lines.append("token " + repr(tok) + ": count=" + str(all_text.count(tok)))
    p2 = texts[1] if len(texts) > 1 else ""
    a, b = p2.find("KCD-46"), p2.find("3600")
    d = abs(a - b) if a >= 0 and b >= 0 else -1
    lines.append("page2: KCD-46@" + str(a) + ", 3600@" + str(b) + ", distance=" + str(d))
    lines.append("--- page2 first 400 chars ---")
    lines.append(p2[:400].replace("\n", " | "))
    if len(all_text.strip()) < 200:
        lines.append("WARN: text layer nearly empty -> scanned PDF, parse-layer bad case")
    if all_text.count("三包") == 0:
        lines.append("WARN: Chinese text not extractable -> font/encoding issue, parse-layer bad case")

out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("[ok] wrote", out, len(lines), "lines (UTF-8)")