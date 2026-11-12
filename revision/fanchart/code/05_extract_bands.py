"""Extract 50/70/90 per cent band edges from the vector (PDF path) fan charts of the RBI MPRs.

Method. Each fan chart is drawn as filled polygons in three shades of red. Polygons are
classified by shade (green channel: <0.42 = 50% band, 0.42-0.66 = 70%, >0.66 = 90%).
Degenerate (zero-area) polygons and rectangles (legend keys) are dropped. Polygon vertices sit
at quarterly x positions; vertices are clustered in x and each cluster is one quarter.
At each quarter, the edges of the L% band are the min/max y over all polygons of shade <= L
(nested bands). y is converted to per cent with the linear value-axis map in chart_meta.json.
The 'central' path is the middle boundary when the set of distinct polygon boundaries at that
quarter has odd size (the fans are built from symmetric quantile pairs around the median).

Usage: python -I code/05_extract_bands.py <fanchart_dir>
Writes data_raw/bands_raw.csv and data_raw/validation.csv
"""
import sys, json, csv, math
from pathlib import Path
import pymupdf

root = Path(sys.argv[1]); sys.path.insert(0, str(root / "code"))
from fan_pages import FAN
meta = json.load(open(root / "code/chart_meta.json"))
stated = json.load(open(root / "code/stated_values.json"))

def is_red(c):
    return c and len(c) == 3 and c[0] > 0.9 and c[1] < 0.9 and abs(c[1] - c[2]) < 0.15 and c[1] > 0.05

def level(c):
    g = c[1]
    return 50 if g < 0.42 else (70 if g < 0.66 else 90)

def area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2

def qadd(q, k):
    y, n = int(q[:4]), int(q[5]) - 1 + k
    return f"{y + n // 4}Q{n % 4 + 1}"

def qdiff(a, b):
    return (int(a[:4]) * 4 + int(a[5])) - (int(b[:4]) * 4 + int(b[5]))

rows, vrows = [], []
for key, (pi, chart) in FAN.items():
    m = meta[key]
    doc = pymupdf.open(root / f"data_raw/pdf/MPR_{key}.pdf"); page = doc[pi]
    y0, v0, y1, v1 = m["y_axis"]
    toval = lambda y: v0 + (y - y0) * (v1 - v0) / (y1 - y0)
    polys = []
    for dr in page.get_drawings():
        c = dr.get("fill")
        if dr["type"] not in ("f", "fs") or not is_red(c):
            continue
        if all(it[0] == "re" for it in dr["items"]):
            continue
        pts = []
        for it in dr["items"]:
            if it[0] == "l":
                pts += [(it[1].x, it[1].y), (it[2].x, it[2].y)]
            elif it[0] == "c":
                pts += [(it[1].x, it[1].y), (it[4].x, it[4].y)]
        pts = [p for p in pts if m["x_min"] <= p[0] <= m["x_max"]]
        if len(pts) < 3 or area(pts) < 1.0:
            continue
        polys.append((level(c), pts))
    xs = sorted(p[0] for _, pts in polys for p in pts)
    clusters = []
    for x in xs:
        if clusters and x - clusters[-1][-1] < 3.0:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    centers = [sum(c) / len(c) for c in clusters]
    gaps = [b - a for a, b in zip(centers, centers[1:])]
    med = sorted(gaps)[len(gaps) // 2]
    bad = [round(g / med, 2) for g in gaps if not 0.8 < g / med < 1.25]
    if bad:
        print("WARNING spacing", key, bad, "(only the last gap may be irregular)")
    nC = len(centers)
    for i, xc in enumerate(centers):
        q = qadd(m["last_q"], i - (nC - 1))
        ys = {50: [], 70: [], 90: []}
        bounds = []
        for lev, pts in polys:
            yy = [p[1] for p in pts if abs(p[0] - xc) < 1.5]
            if yy:
                ys[lev] += yy
                bounds += yy
        edges = {}
        for L in (50, 70, 90):
            pool = [y for l2 in (50, 70, 90) if l2 <= L for y in ys[l2]]
            if pool:
                edges[L] = (toval(max(pool)), toval(min(pool)))  # (lower value, upper value)
        ub = sorted(bounds)
        uniq = []
        for y in ub:
            if not uniq or y - uniq[-1] > 0.15:
                uniq.append(y)
        central = toval(uniq[len(uniq) // 2]) if len(uniq) % 2 == 1 else float("nan")
        width90 = edges[90][1] - edges[90][0] if 90 in edges else 0
        for L in (50, 70, 90):
            if L not in edges: continue
            rows.append(dict(issue=key, pub_date=m["pub"], pub_quarter=m["pubq"], chart=chart, page_index=pi,
                             target_quarter=q, horizon=qdiff(q, m["pubq"]), band=L,
                             lower=round(edges[L][0], 3), upper=round(edges[L][1], 3),
                             central=round(central, 3), n_boundaries=len(uniq), width90=round(width90, 3),
                             x_pt=round(xc, 2)))
    # validation against stated text values
    st = stated.get(key, {})
    byq = {(r["target_quarter"], r["band"]): r for r in rows if r["issue"] == key}
    for q, v in st.get("central", {}).items():
        r = byq.get((q, 50))
        if r: vrows.append(dict(issue=key, quarter=q, item="central", stated=v, extracted=r["central"], error=round(r["central"] - v, 3)))
    for L in (50, 70):
        for q, (lo, hi) in st.get(f"ci{L}", {}).items():
            r = byq.get((q, L))
            if r:
                vrows.append(dict(issue=key, quarter=q, item=f"ci{L}_lower", stated=lo, extracted=r["lower"], error=round(r["lower"] - lo, 3)))
                vrows.append(dict(issue=key, quarter=q, item=f"ci{L}_upper", stated=hi, extracted=r["upper"], error=round(r["upper"] - hi, 3)))

with open(root / "data_raw/bands_raw.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open(root / "data_raw/validation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(vrows[0])); w.writeheader(); w.writerows(vrows)
import statistics as s
for key in FAN:
    e = [abs(v["error"]) for v in vrows if v["issue"] == key and not math.isnan(v["error"])]
    ec = [v["error"] for v in vrows if v["issue"] == key and v["item"] == "central" and not math.isnan(v["error"])]
    eb = [v["error"] for v in vrows if v["issue"] == key and v["item"] != "central"]
    print(key, "n", len(e), "max|err|", round(max(e), 3) if e else None, "central errs", ec, "band errs", eb)
