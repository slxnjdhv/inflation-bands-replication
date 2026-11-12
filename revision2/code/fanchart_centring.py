"""Centring and width diagnostics for the RBI fan-chart back-test.

Reads (read-only) revision/fanchart/bands.csv and illustration/output/data_inflation_series.csv
(the same inputs as revision/fanchart/code/07_evaluate.py; the outturn definition and the period
split are copied from that script). Writes revision2/output/fanchart_centring.csv.

For each horizon h and period: n, mean and median of (outturn - fan median), number of outturns
below / above the median, exact two-sided sign-test p-value, mean absolute error about the median,
mean half-width of the 50/70/90 per cent bands, and the coverage counts (re-derived, as a check
against coverage_results.csv).
Run:  python -I revision2/code/fanchart_centring.py
"""
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

PROJ = Path(__file__).resolve().parents[2]
FAN = PROJ / "revision" / "fanchart"
OUT = PROJ / "revision2" / "output"
OUT.mkdir(parents=True, exist_ok=True)

mon = {r["month"]: float(r["headline_yoy"]) for r in csv.DictReader(open(PROJ / "illustration/output/data_inflation_series.csv"))}
qv = {}
for m, v in mon.items():
    q = f"{m[:4]}Q{(int(m[5:7]) - 1) // 3 + 1}"
    qv.setdefault(q, []).append(v)
outturn = {q: sum(v) / 3 for q, v in qv.items() if len(v) == 3}


def period(q):
    return "2016Q4-2020Q1" if q <= "2020Q1" else ("2020Q2-2022Q4" if q <= "2022Q4" else "2023Q1-2026Q3")


b = pd.read_csv(FAN / "bands.csv")
b = b[(b.issue != "2016 Apr") & b.target_quarter.isin(list(outturn))]
w = b.pivot_table(index=["issue", "target_quarter", "horizon"], columns="band_level",
                  values=["lower", "upper", "central"], aggfunc="first")
d = pd.DataFrame({
    "central": w[("central", 50)],
    **{f"lo{L}": w[("lower", L)] for L in (50, 70, 90)},
    **{f"hi{L}": w[("upper", L)] for L in (50, 70, 90)},
}).reset_index()
d["y"] = d.target_quarter.map(outturn)
d["err"] = d.y - d.central
d["period"] = d.target_quarter.map(period)
for L in (50, 70, 90):
    d[f"in{L}"] = (d[f"lo{L}"] <= d.y) & (d.y <= d[f"hi{L}"])
    d[f"hw{L}"] = (d[f"hi{L}"] - d[f"lo{L}"]) / 2
d.to_csv(OUT / "fanchart_obs_wide.csv", index=False, float_format="%.4f")

rows = []
for h in (0, 1, 2, 3, 4):
    for per in ("all", "2016Q4-2020Q1", "2020Q2-2022Q4", "2023Q1-2026Q3"):
        s = d[(d.horizon == h) & ((d.period == per) if per != "all" else True)]
        if s.empty:
            continue
        n = len(s)
        nb, na = int((s.err < 0).sum()), int((s.err > 0).sum())
        r = dict(horizon=h, period=per, n=n, n_with_median=int(s.err.notna().sum()), mean_err=s.err.mean(), median_err=s.err.median(),
                 n_below_median=nb, n_above_median=na,
                 sign_p=binomtest(nb, nb + na, 0.5).pvalue if nb + na else np.nan,
                 mae=s.err.abs().mean(), rmse=float(np.sqrt((s.err ** 2).mean())))
        for L in (50, 70, 90):
            r[f"mean_halfwidth{L}"] = s[f"hw{L}"].mean()
            r[f"inside{L}"] = int(s[f"in{L}"].sum())
        r["mae_over_halfwidth50"] = r["mae"] / s.loc[s.err.notna(), "hw50"].mean()  # about 1.18 if Gaussian and calibrated
        rows.append(r)
res = pd.DataFrame(rows)
res.to_csv(OUT / "fanchart_centring.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(res.round(3).to_string(index=False))

# 8 of 9 check (h = 1, 2, 4; all targets)
cov = pd.read_csv(FAN / "coverage_results.csv")
cov = cov[(cov["sample"] == "all") & cov.bands_source.str.startswith("numeric") & cov.horizon.isin([1, 2, 4])]
cov["at_or_above"] = cov.coverage >= cov.band / 100
print(cov[["horizon", "band", "n", "inside", "coverage", "at_or_above"]].to_string(index=False))
print("cells at/above nominal:", int(cov.at_or_above.sum()), "of", len(cov))
