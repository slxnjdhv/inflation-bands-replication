"""Build bands.csv, compute coverage of RBI CPI fan-chart bands, write table and figure.
Usage: python -I code/07_evaluate.py <fanchart_dir> <inflation_csv>
"""
import sys, json, csv, math
from pathlib import Path
from scipy.stats import binomtest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(sys.argv[1]); sys.path.insert(0, str(root / "code"))
from fan_pages import FAN
meta = json.load(open(root / "code/chart_meta.json"))
stated = json.load(open(root / "code/stated_values.json"))
raw = list(csv.DictReader(open(root / "data_raw/bands_raw.csv")))
val = list(csv.DictReader(open(root / "data_raw/validation.csv")))
idx = {r["issue"]: r for r in csv.DictReader(open(root / "data_raw/mpr_index.csv", encoding="utf-8"))
       for _ in [0]} if False else {}
for r in csv.DictReader(open(root / "data_raw/mpr_index.csv", encoding="utf-8")):
    t = r["title"].split(); idx[f"{t[-1]}_{t[-2][:3]}"] = r
prov = {r["file"]: r for r in csv.DictReader(open(root / "data_raw/pdf_provenance.csv", encoding="utf-8"))}
wb = {l.split()[0]: l.split()[1] for l in open(root / "data_raw/wayback_captures.txt")}

# ---------- outturns: quarterly average of monthly y-o-y headline CPI ----------
mon = {r["month"]: float(r["headline_yoy"]) for r in csv.DictReader(open(sys.argv[2]))}
qv = {}
for m, v in mon.items():
    q = f"{m[:4]}Q{(int(m[5:7]) - 1) // 3 + 1}"; qv.setdefault(q, []).append(v)
outturn = {q: sum(v) / 3 for q, v in qv.items() if len(v) == 3}
with open(root / "data_raw/outturns_quarterly.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["quarter", "cpi_yoy_qavg"])
    for q in sorted(outturn): w.writerow([q, round(outturn[q], 3)])

# ---------- digitisation error per issue ----------
err = {}
for v in val:
    e = float(v["error"])
    if not math.isnan(e):
        err.setdefault(v["issue"], []).append(abs(e))
ERR = {k: max(v) for k, v in err.items()}

# ---------- bands.csv ----------
bands = []
for r in raw:
    if float(r["width90"]) < 0.02:  # historical / origin quarter, no band
        continue
    k = r["issue"]; L = int(r["band"]); q = r["target_quarter"]
    st = stated.get(k, {}).get(f"ci{L}", {}).get(q)
    stc = stated.get(k, {}).get("central", {}).get(q)
    pdf = idx[k]["pdf"]
    pv = prov.get(f"MPR_{k}.pdf")
    wbu = pv["wayback_url"] if pv else f"https://web.archive.org/web/{wb[pdf]}/{pdf}"
    bands.append(dict(
        issue=k.replace("_", " "), pub_date=r["pub_date"], pub_quarter=r["pub_quarter"], chart=r["chart"],
        pdf_page=int(r["page_index"]) + 1, target_quarter=q, horizon=int(r["horizon"]), band_level=L,
        lower=st[0] if st else float(r["lower"]), upper=st[1] if st else float(r["upper"]),
        central=float(r["central"]) if r["central"] != "nan" else "",
        source_type="numeric (MPR text)" if st else "digitised (PDF vector paths)",
        lower_digitised=float(r["lower"]), upper_digitised=float(r["upper"]),
        central_stated=stc if stc is not None else "",
        digitisation_error=round(ERR.get(k, float("nan")), 3),
        official_pdf=pdf, archived_copy=wbu))
with open(root / "bands.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(bands[0])); w.writeheader(); w.writerows(bands)

# ---------- evaluation sample ----------
MAIN_ISSUES = [k.replace("_", " ") for k in FAN if k != "2016_Apr"]  # MPC era, Oct 2016 onward
IMPUTED = {"2020Q2", "2021Q2"}       # Apr-May 2020 indices imputed; base effect in 2021Q2
NEWBASE = lambda q: q >= "2026Q1"     # outturn on CPI base 2024=100
def period(q):
    return "2016Q4-2020Q1" if q <= "2020Q1" else ("2020Q2-2022Q4" if q <= "2022Q4" else "2023Q1-2026Q3")

obs = []
for b in bands:
    if b["issue"] not in MAIN_ISSUES or b["target_quarter"] not in outturn:
        continue
    y = outturn[b["target_quarter"]]
    for kind, lo, hi in (("main", b["lower"], b["upper"]), ("digitised", b["lower_digitised"], b["upper_digitised"])):
        o = dict(b); o["kind"] = kind; o["y"] = y
        o["inside"] = lo <= y <= hi
        o["miss"] = "" if o["inside"] else ("above" if y > hi else "below")
        tol = max(0.05, b["digitisation_error"]) if b["source_type"].startswith("digitised") else 0.05
        o["borderline"] = min(abs(y - lo), abs(y - hi)) <= tol
        obs.append(o)
with open(root / "data_raw/evaluation_obs.csv", "w", newline="") as f:
    keys = ["issue", "target_quarter", "horizon", "band_level", "lower", "upper", "y", "inside", "miss", "borderline", "source_type", "kind"]
    w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(obs)

def summarise(sel, label):
    n = len(sel); k = sum(o["inside"] for o in sel)
    res = dict(sample=label, n=n, inside=k)
    if n == 0:
        return res
    L = sel[0]["band_level"] / 100
    bt = binomtest(k, n, L)
    ci = bt.proportion_ci(confidence_level=0.95, method="exact")
    res.update(coverage=round(k / n, 3), cp_low=round(ci.low, 3), cp_high=round(ci.high, 3),
               p_exact=round(bt.pvalue, 4), above=sum(o["miss"] == "above" for o in sel),
               below=sum(o["miss"] == "below" for o in sel), borderline=sum(o["borderline"] for o in sel),
               targets=f"{min(o['target_quarter'] for o in sel)}..{max(o['target_quarter'] for o in sel)}")
    return res

results = []
for h in (0, 1, 2, 3, 4):
    for L in (50, 70, 90):
        base = [o for o in obs if o["horizon"] == h and o["band_level"] == L]
        for label, filt in [
            ("all", lambda o: True),
            ("excl. imputation-affected (2020Q2, 2021Q2)", lambda o: o["target_quarter"] not in IMPUTED),
            ("excl. COVID targets 2020Q2-2021Q4", lambda o: not ("2020Q2" <= o["target_quarter"] <= "2021Q4")),
            ("excl. new-base targets (>=2026Q1)", lambda o: not NEWBASE(o["target_quarter"])),
            ("period 2016Q4-2020Q1", lambda o: period(o["target_quarter"]) == "2016Q4-2020Q1"),
            ("period 2020Q2-2022Q4", lambda o: period(o["target_quarter"]) == "2020Q2-2022Q4"),
            ("period 2023Q1-2026Q3", lambda o: period(o["target_quarter"]) == "2023Q1-2026Q3"),
        ]:
            for kind in ("main", "digitised"):
                sel = [o for o in base if o["kind"] == kind and filt(o)]
                r = summarise(sel, label)
                r.update(horizon=h, band=L, bands_source="numeric where stated, else digitised" if kind == "main" else "all digitised")
                results.append(r)
cols = ["horizon", "band", "sample", "bands_source", "n", "inside", "coverage", "cp_low", "cp_high", "p_exact", "above", "below", "borderline", "targets"]
with open(root / "coverage_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(results)

# does using text-stated values ever change a classification?
flips = []
for o in obs:
    if o["kind"] == "main":
        d = [p for p in obs if p["kind"] == "digitised" and p["issue"] == o["issue"] and p["target_quarter"] == o["target_quarter"] and p["band_level"] == o["band_level"]][0]
        if d["inside"] != o["inside"]:
            flips.append((o["issue"], o["target_quarter"], o["band_level"]))
print("classification differences numeric vs digitised:", flips)

# ---------- LaTeX table ----------
def get(h, L, s="all", kind="main"):
    return [r for r in results if r["horizon"] == h and r["band"] == L and r["sample"] == s and r["bands_source"].startswith("numeric" if kind == "main" else "all")][0]
lines = [r"\begin{tabular}{@{}llrrcrr r@{}}", r"\toprule",
         r"Horizon & Band & $n$ & Inside & Coverage [95\% CI] & $p$ & Above & Below \\",
         r"\midrule"]
for h in (1, 2, 4):
    for L in (50, 70, 90):
        r = get(h, L)
        lab = f"{h}q" if L == 50 else ""
        lines.append(f"{lab} & {L}\\% & {r['n']} & {r['inside']} & {r['coverage']:.2f} [{r['cp_low']:.2f}, {r['cp_high']:.2f}] & {r['p_exact']:.2f} & {r['above']} & {r['below']} \\\\")
    if h != 4: lines.append(r"\addlinespace")
lines += [r"\midrule", r"\multicolumn{8}{@{}l}{\emph{Excluding target quarters affected by the 2020 CPI imputation (2020Q2, 2021Q2)}}\\"]
for h in (1, 2, 4):
    for L in (50, 70, 90):
        r = get(h, L, "excl. imputation-affected (2020Q2, 2021Q2)")
        lab = f"{h}q" if L == 50 else ""
        lines.append(f"{lab} & {L}\\% & {r['n']} & {r['inside']} & {r['coverage']:.2f} [{r['cp_low']:.2f}, {r['cp_high']:.2f}] & {r['p_exact']:.2f} & {r['above']} & {r['below']} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(root / "table_fanchart.tex").write_text(
    "% RBI MPR CPI fan charts, Oct 2016 - Apr 2026 issues; generated by revision/fanchart/code/07_evaluate.py\n"
    "% Horizon h = target quarter minus the calendar quarter of publication. Coverage = share of\n"
    "% quarterly-average y-o-y CPI outturns inside the band; 95% CI Clopper-Pearson; p = exact two-sided\n"
    "% binomial test against the nominal level. Observations overlap across issues and horizons.\n"
    + "\n".join(lines) + "\n", encoding="utf-8")

# ---------- figure ----------
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 7, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
shade = {90: "#f6c9c4", 70: "#e98a80", 50: "#c8443a"}
fig, axes = plt.subplots(3, 1, figsize=(174 / 25.4, 150 / 25.4), sharex=True)
allq = sorted(outturn)
qi = lambda q: int(q[:4]) + (int(q[5]) - 1) / 4
for ax, h in zip(axes, (1, 2, 4)):
    sel = [b for b in bands if b["issue"] in MAIN_ISSUES and b["horizon"] == h]
    for L in (90, 70, 50):
        for b in [s for s in sel if s["band_level"] == L]:
            x = qi(b["target_quarter"])
            ax.add_patch(plt.Rectangle((x - 0.09, b["lower"]), 0.18, b["upper"] - b["lower"], color=shade[L], lw=0, zorder=1))
    xs = [qi(q) for q in allq if "2016Q3" <= q <= "2026Q3"]
    ax.plot(xs, [outturn[q] for q in allq if "2016Q3" <= q <= "2026Q3"], color="#555555", lw=0.8, zorder=2)
    for b in [s for s in sel if s["band_level"] == 70 and s["target_quarter"] in outturn]:
        y = outturn[b["target_quarter"]]; inside = b["lower"] <= y <= b["upper"]
        ax.plot(qi(b["target_quarter"]), y, marker="o", ms=4, zorder=3,
                mfc="#1b1b1b" if inside else "white", mec="#1b1b1b", mew=0.9)
    for q in IMPUTED:
        ax.axvspan(qi(q) - 0.125, qi(q) + 0.125, color="#dddddd", zorder=0, lw=0)
    ax.axvline(qi("2026Q1") - 0.125, color="#999999", lw=0.6, ls=":", zorder=0)
    ax.set_ylabel("Per cent")
    ax.set_title(f"Horizon {h} quarter{'s' if h > 1 else ''} after the publication quarter", loc="left")
    ax.set_ylim(-1, 10.5); ax.grid(axis="y", color="#eeeeee", lw=0.5); ax.set_axisbelow(True)
axes[-1].set_xlim(2016.6, 2026.9)
axes[-1].set_xticks(range(2017, 2027)); axes[-1].set_xlabel("Target quarter")
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
hand = [Patch(color=shade[50], label="50% band"), Patch(color=shade[70], label="70% band"), Patch(color=shade[90], label="90% band"),
        Line2D([], [], color="#555555", lw=0.8, label="CPI inflation, quarterly avg. y-o-y"),
        Line2D([], [], marker="o", ls="", mfc="#1b1b1b", mec="#1b1b1b", label="Outturn inside 70% band"),
        Line2D([], [], marker="o", ls="", mfc="white", mec="#1b1b1b", label="Outturn outside 70% band"),
        Patch(color="#dddddd", label="Imputation-affected quarter")]
fig.legend(handles=hand, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.005))
fig.tight_layout(rect=(0, 0.075, 1, 1))
fig.savefig(root / "fig_fanchart_backtest.pdf"); fig.savefig(root / "fig_fanchart_backtest.png", dpi=300)

for h in (1, 2, 4):
    for L in (50, 70, 90):
        r = get(h, L); r2 = get(h, L, "excl. imputation-affected (2020Q2, 2021Q2)")
        print(f"h={h} {L}%: {r['inside']}/{r['n']} = {r['coverage']} [{r['cp_low']},{r['cp_high']}] p={r['p_exact']} above={r['above']} below={r['below']} border={r['borderline']} | exclImp {r2['inside']}/{r2['n']} p={r2['p_exact']}")
