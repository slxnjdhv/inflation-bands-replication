"""Survey each MPR PDF: find the CPI inflation fan chart, its caption, page, whether it is vector
or raster, and the text sentences giving central projections and confidence intervals.
Usage: python -I code/03_survey.py <fanchart_dir>
Writes data_raw/survey.txt and data_raw/survey.csv
"""
import sys, re, csv
from pathlib import Path
import pymupdf
sys.stdout.reconfigure(encoding="utf-8")
root = Path(sys.argv[1]); raw = root / "data_raw"
out = open(raw / "survey.txt", "w", encoding="utf-8")
rows = []
for fn in sorted((raw / "pdf").glob("MPR_*.pdf")):
    d = pymupdf.open(fn)
    found = []
    for i, p in enumerate(d):
        t = p.get_text()
        for m in re.finditer(r"Chart\s+I\.(\d+)\s*:\s*([^\n]*)", t):
            cap = m.group(2)
            if re.search(r"Projection of (Headline )?CPI|CPI Inflation", cap, re.I) and re.search(r"Projection|Fan", cap, re.I):
                found.append((i, f"I.{m.group(1)}", cap.strip()))
    print(fn.name, d.page_count, found, file=out)
    for i, chart, cap in found[:1]:
        p = d[i]
        ndraw = len(p.get_drawings()); nimg = len(p.get_images())
        fills = {}
        for dr in p.get_drawings():
            if dr.get("fill") and dr["type"] == "f":
                c = tuple(round(x, 3) for x in dr["fill"])
                fills[c] = fills.get(c, 0) + 1
        print("  page", i, chart, cap, "drawings", ndraw, "images", nimg, file=out)
        print("  fill colours", sorted(fills.items(), key=lambda kv: -kv[1])[:8], file=out)
        rows.append(dict(file=fn.name, page_index=i, page_label=d[i].get_label() or "", chart=chart, caption=cap, drawings=ndraw, images=nimg))
    # sentences with confidence intervals and the projection paragraph
    full = " ".join(p.get_text() for p in d[:40])
    full = re.sub(r"\s+", " ", full)
    for m in re.finditer(r"[^.]*(confidence interval|per cent and the 70 per cent)[^.]*\.[^.]*\.", full):
        print("  CI:", m.group(0).strip()[:700], file=out)
    for m in re.finditer(r"[^.]*(CPI|Headline) inflation is (projected|expected)[^.]*\.", full):
        print("  PROJ:", m.group(0).strip()[:700], file=out)
    print(file=out)
with open(raw / "survey.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
