"""Referee comment R2: 3- and 6-month-ahead intervals for Indian headline CPI inflation.

Data, lag matrix, regimes and the food-shock indicator are taken unchanged from
illustration/code/run_illustration.py (its sections 1-2 are executed verbatim; nothing is written there).
Direct h-step forecasts: y_t is regressed on lags h..h+11 of headline and food inflation, with
training targets up to the forecast origin t-h only. Calibration for the conformal and
error-based intervals uses only errors observable at the origin (targets <= t-h). The
regime-conditional interval uses the food-shock label at the origin.
Evaluation targets: April 2018 to September 2026 for all horizons (common sample; h=6 needs 12 observed errors).
Writes revision/fix_v6/horizon/output/.  Run: python -I revision/fix_v6/horizon/run_horizon.py
"""
from pathlib import Path
import math, sys
import numpy as np, pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
OUTD = HERE / "output"; OUTD.mkdir(exist_ok=True)
ILL = HERE.parents[2] / "illustration" / "code" / "run_illustration.py"
src = ILL.read_text(encoding="utf-8")
cut = src.index("# 3. Point forecasters")
g = {"__file__": str(ILL), "__name__": "ill_data"}
data_src = src[:cut].replace('OUT / "data_inflation_series.csv"', 'str(Path(r"%s") / "data_inflation_series.csv")' % OUTD)
assert data_src != src[:cut]          # never write into illustration/output
exec(compile(data_src, str(ILL), "exec"), g)          # sections 1-2 only: data, X_all, shock
H, F, full, shock = g["H"], g["F"], g["full"], g["shock"]
ALPHA, REGIMES, FIRST_TARGET, EVAL_START, MIN_CAL = g["ALPHA"], g["REGIMES"], g["FIRST_TARGET"], g["EVAL_START"], g["MIN_CAL"]
NL = g["NLAGS"]
src2 = src[cut:src.index("# 4. Interval methods")]
exec(compile(src2.split("def point_forecasts")[0], str(ILL), "exec"), g)   # fit_ar, fit_en
fit_ar, fit_en = g["fit_ar"], g["fit_en"]
cq = None
exec(compile(src[src.index("def cq("):src.index("def build_intervals")], str(ILL), "exec"), g); cq = g["cq"]
z = stats.norm.ppf(1 - ALPHA / 2)
EVAL = pd.Period("2018-04", "M")   # common sample: first month all horizons have >= 12 observed errors


def lagged(h):
    cols = {}
    for L in range(h, h + NL):
        cols[f"h{L}"] = H.shift(L); cols[f"f{L}"] = F.shift(L)
    return pd.DataFrame(cols)


def forecasts(h):
    X = lagged(h); own = [f"h{L}" for L in range(h, h + NL)]
    first_tr = FIRST_TARGET + (h - 1)                  # first target with all h..h+11 lags
    last = H.dropna().index.max()
    recs = []
    t0 = first_tr + 11 + h                             # >= 12 training targets, as in the main illustration
    for t in pd.period_range(t0, last, freq="M"):
        tr = pd.period_range(first_tr, t - h, freq="M")  # targets observed at origin t-h
        y_tr = H.reindex(tr).values; X_tr = X.loc[tr].values
        assert not np.isnan(y_tr).any() and not np.isnan(X_tr).any(), t
        a, asd, _ = fit_ar(y_tr, X.loc[tr, own].values, X.loc[t, own].values)
        e, esd, _ = fit_en(X_tr, y_tr, X.loc[t].values)
        recs.append(dict(month=t, y=H[t], AR=a, AR_sd=asd, EN=e, EN_sd=esd))
    return pd.DataFrame(recs).set_index("month")


def intervals(pf, fc, h, W=36):
    res = pf.y - pf[fc]; out = {k: [] for k in ("Gaussian", "Gaussian, OOS errors", "Split conformal", "Regime-cond. SCP")}
    for t in [m for m in pf.index if m >= EVAL]:
        past = res[res.index <= t - h].dropna()           # errors known at the origin
        cal = past.iloc[-W:].abs().values
        assert len(cal) >= 12, (t, len(cal))
        yh, y = pf.loc[t, fc], pf.loc[t, "y"]
        add = lambda k, q: out[k].append(dict(month=t, y=y, lo=yh - q, hi=yh + q))
        add("Gaussian", z * pf.loc[t, f"{fc}_sd"])
        add("Gaussian, OOS errors", z * math.sqrt(np.mean(cal ** 2)))
        add("Split conformal", cq(cal, ALPHA)[0])
        s0 = shock.get(t - h + 1, np.nan)                 # label known at the origin t-h
        same = past[[shock.get(s - h + 1, -1) == s0 for s in past.index]]
        calg = cal if len(same) < MIN_CAL else same.iloc[-W:].abs().values
        add("Regime-cond. SCP", cq(calg, ALPHA)[0])
    return {k: pd.DataFrame(v).set_index("month") for k, v in out.items()}


def summ(d):
    miss = ~((d.lo <= d.y) & (d.y <= d.hi)); n, x = len(d), int(miss.sum())
    IS = ((d.hi - d.lo) + (2 / ALPHA) * ((d.lo - d.y) * (d.y < d.lo) + (d.y - d.hi) * (d.y > d.hi))).mean()
    return dict(n=n, misses=x, coverage=1 - x / n, width=(d.hi - d.lo).mean(), IS=IS,
                p_exact=stats.binomtest(x, n, ALPHA).pvalue)


rows = []
for h in (1, 3, 6):
    pf = forecasts(h)
    pf.to_csv(OUTD / f"point_forecasts_h{h}.csv")
    ev = pf[pf.index >= EVAL]
    for fc in ("AR", "EN"):
        rmse = math.sqrt(((ev.y - ev[fc]) ** 2).mean())
        for meth, d in intervals(pf, fc, h).items():
            masks = {"All": slice(None)}
            for r, (a, b) in REGIMES.items():
                masks[r] = (d.index >= a) & (d.index <= b)
            for cell, m in masks.items():
                rows.append(dict(h=h, forecaster=fc, rmse=rmse, method=meth, cell=cell, **summ(d[m])))
            d.to_csv(OUTD / f"paths_h{h}_{fc}_{meth.replace(' ', '_').replace(',', '').replace('.', '')}.csv")
res = pd.DataFrame(rows)
res.to_csv(OUTD / "results_horizons.csv", index=False)
wide = res[res.cell.isin(["All", "R2", "R3"])].pivot_table(index=["h", "forecaster", "method"], columns="cell",
                                                           values="coverage").round(3)
wide = wide.join(res[res.cell == "All"].set_index(["h", "forecaster", "method"])[["rmse", "width", "IS", "misses", "p_exact"]].round(3))
print(wide.to_string())
wide.to_csv(OUTD / "summary_horizons.csv")
