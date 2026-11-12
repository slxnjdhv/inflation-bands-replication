"""Diagnostics for each vector fan chart: colour classes of band polygons, vertex x positions,
candidate y-axis tick marks and numeric tick-label text. Output used to write chart_meta.json.
Usage: python -I code/04_probe.py <fanchart_dir> [key]
"""
import sys, json, re
from pathlib import Path
import pymupdf
sys.stdout.reconfigure(encoding="utf-8")
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "code"))
from fan_pages import FAN
only = sys.argv[2] if len(sys.argv) > 2 else None

def is_red(c):
    return c and len(c) == 3 and c[0] > 0.9 and c[1] < 0.9 and abs(c[1] - c[2]) < 0.15 and c[1] > 0.05

for k, (pi, ch) in FAN.items():
    if only and k != only: continue
    d = pymupdf.open(root / f"data_raw/pdf/MPR_{k}.pdf"); p = d[pi]
    drs = p.get_drawings()
    polys = [dr for dr in drs if dr["type"] in ("f", "fs") and is_red(dr.get("fill")) and dr["rect"].height > 3]
    bb = polys[0]["rect"]
    for dr in polys[1:]: bb |= dr["rect"]
    cols = {}
    xs = []
    for dr in polys:
        c = tuple(round(v, 2) for v in dr["fill"]); cols[c] = cols.get(c, 0) + 1
        for it in dr["items"]:
            for pt in it[1:]:
                if isinstance(pt, pymupdf.Point): xs.append(round(pt.x, 1))
    xs = sorted(set(xs))
    print(f"== {k} page {pi} chart {ch} fan bbox {[round(v,1) for v in bb]}")
    print("  colours", sorted(cols.items()))
    print("  vertex x", xs)
    # horizontal short segments (ticks) and long ones (gridlines) in stroke paths near the plot
    region = pymupdf.Rect(bb.x0 - 200, bb.y0 - 80, bb.x1 + 40, bb.y1 + 80)
    hs = []
    vlines = []
    for dr in drs:
        if dr["type"] not in ("s", "fs"): continue
        for it in dr["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if not (region.contains(a) and region.contains(b)): continue
                if abs(a.y - b.y) < 0.05 and abs(a.x - b.x) > 1:
                    hs.append((round(min(a.x, b.x), 1), round(max(a.x, b.x), 1), round(a.y, 2)))
                if abs(a.x - b.x) < 0.05 and abs(a.y - b.y) > 40:
                    vlines.append((round(a.x, 1), round(min(a.y, b.y), 1), round(max(a.y, b.y), 1)))
    print("  long vertical lines", vlines[:6])
    print("  horizontal segs", sorted(set(hs), key=lambda t: t[2])[:40])
    words = [w for w in p.get_text("words") if region.contains(pymupdf.Rect(w[:4])) and re.fullmatch(r"-?\d+(\.\d+)?", w[4])]
    print("  numeric words", [(w[4], round((w[1] + w[3]) / 2, 2), round(w[0], 1)) for w in words][:40])
