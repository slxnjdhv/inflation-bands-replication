"""Second digitisation check: read the historical (actual) CPI line drawn in each fan chart,
convert with the same axis map, and compare with quarterly averages of monthly y-o-y CPI
inflation (latest vintage, from the illustration data file). Differences combine digitisation
error and data revisions/vintage differences, so they bound rather than measure the error.
Usage: python -I code/06_check_actual_line.py <fanchart_dir> <inflation_csv>
Writes data_raw/actual_line_check.csv
"""
import sys, json, csv
from pathlib import Path
import pymupdf
root = Path(sys.argv[1]); sys.path.insert(0, str(root / "code"))
from fan_pages import FAN
meta = json.load(open(root / "code/chart_meta.json"))
bands = list(csv.DictReader(open(root / "data_raw/bands_raw.csv")))

mon = {}
for r in csv.DictReader(open(sys.argv[2])):
    mon[r["month"]] = float(r["headline_yoy"])
qavg = {}
for mth, v in mon.items():
    y, mm = int(mth[:4]), int(mth[5:7]); q = f"{y}Q{(mm - 1) // 3 + 1}"
    qavg.setdefault(q, []).append(v)
qavg = {q: sum(v) / len(v) for q, v in qavg.items() if len(v) == 3}

def qadd(q, k):
    y, n = int(q[:4]), int(q[5]) - 1 + k
    return f"{y + n // 4}Q{n % 4 + 1}"

out = []
for key, (pi, ch) in FAN.items():
    m = meta[key]; y0, v0, y1, v1 = m["y_axis"]
    toval = lambda y: v0 + (y - y0) * (v1 - v0) / (y1 - y0)
    br = [b for b in bands if b["issue"] == key and b["band"] == "90"]
    xq = {float(b["x_pt"]): b["target_quarter"] for b in br}
    xs = sorted(xq); step = (xs[-2] - xs[0]) / (len(xs) - 2) if len(xs) > 2 else None
    wid = {float(b["x_pt"]): float(b["width90"]) for b in br}
    zero = [x for x in xs if wid[x] < 0.02]
    first_wide = min([x for x in xs if wid[x] >= 0.02], default=xs[-1])
    zero = [x for x in zero if x < first_wide]
    origin_x = max(zero) if zero else xs[0]
    origin_q = xq[origin_x]
    page = pymupdf.open(root / f"data_raw/pdf/MPR_{key}.pdf")[pi]
    best = None
    for dr in page.get_drawings():
        c = dr.get("color")
        if dr["type"] != "s" or not c or len(c) != 3 or not (c[0] > 0.8 and c[1] < 0.5 and c[2] < 0.5):
            continue
        pts = []
        for it in dr["items"]:
            if it[0] == "l":
                pts += [(it[1].x, it[1].y), (it[2].x, it[2].y)]
        lo_y, hi_y = min(y0, y1), max(y0, y1)
        pts = [p for p in pts if origin_x - 20 * step <= p[0] <= origin_x + 1 and lo_y - 1 <= p[1] <= hi_y + 1]
        on_grid = {round((p[0] - origin_x) / step) for p in pts if abs((p[0] - origin_x) - round((p[0] - origin_x) / step) * step) < 1.5}
        if len(on_grid) >= 3 and (best is None or len(on_grid) > best[0]):
            best = (len(on_grid), pts)
    if not best or not step:
        continue
    best = best[1]
    seen = {}
    for x, y in best:
        k = round((x - origin_x) / step)
        if abs((x - origin_x) - k * step) < 1.5:
            seen[k] = y
    for k, y in sorted(seen.items()):
        q = qadd(origin_q, k)
        if q in qavg:
            out.append(dict(issue=key, quarter=q, chart_value=round(toval(y), 3), data_value=round(qavg[q], 3),
                            diff=round(toval(y) - qavg[q], 3)))
with open(root / "data_raw/actual_line_check.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
import statistics as st
for key in FAN:
    d = [o["diff"] for o in out if o["issue"] == key]
    if d:
        print(key, "n", len(d), "mean diff", round(st.mean(d), 3), "median", round(st.median(d), 3), "max|d|", round(max(map(abs, d)), 3))
    else:
        print(key, "no actual line matched")
