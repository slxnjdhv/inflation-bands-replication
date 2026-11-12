"""Empirical illustration (revision 2): coverage of prediction intervals for
Indian CPI inflation across regimes, at nominal 50/70/90 per cent, with an added
out-of-sample error-based Gaussian baseline.

Copy of illustration/code/run_illustration.py, extended:
  * nominal levels 0.50, 0.70, 0.90 (the 0.90 results of the existing methods are unchanged;
    this is checked against illustration/output/results_all.csv at the end);
  * new baseline "EB-Gauss W=36/60": yhat +/- z * RMSE of the most recent W out-of-sample
    errors (zero-mean, Reifschneider-Tulip / Clark-McCracken-Mertens style), using exactly the
    same error windows as the rolling conformal intervals; and "EB-Gauss-sd W=..": the same
    with the demeaned standard deviation (ddof=1) of those errors;
  * per-month interval paths with interval scores at every level (input to dm_tests.py).
The figure and LaTeX tables of the original script are not produced here (see fig1.py).

Run:  python -I revision2/code/run_illustration2.py
Reads only illustration/data_raw/ (and illustration/output/results_all.csv for the check),
writes only revision2/output/.  Deterministic.
"""
from __future__ import annotations

import json
import math
import random
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

random.seed(0)
np.random.seed(0)
warnings.filterwarnings("ignore", category=ConvergenceWarning)

PROJ = Path(__file__).resolve().parents[2]
RAW = PROJ / "illustration" / "data_raw"
ORIG_OUT = PROJ / "illustration" / "output"
OUT = PROJ / "revision2" / "output"
OUT.mkdir(exist_ok=True)

LOG_LINES: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    LOG_LINES.append(msg)


# --------------------------------------------------------------------------
# Settings (fixed before estimation)
# --------------------------------------------------------------------------
ALPHA = 0.10
ALPHAS = (0.10, 0.30, 0.50)   # nominal 90 / 70 / 50 per cent
LF_COMBINED = 0.5267          # MoSPI FAQ Q38; linked = old x LF (FAQ Q37)
NLAGS = 12
FIRST_TARGET = pd.Period("2015-01", "M")   # first month with 12 lags of y-o-y inflation
FIRST_OOS = pd.Period("2016-01", "M")      # first out-of-sample point forecast
EVAL_START = pd.Period("2017-01", "M")     # first interval evaluated
MIN_CAL = 9                                # ceil((n+1)*0.9) <= n  <=>  n >= 9
WINDOWS = (36, 60)
GAMMAS = (0.005, 0.02)
SHOCK_Q = 0.80
IMPUTED = [pd.Period("2020-04", "M"), pd.Period("2020-05", "M")]
IMPUTED_BASE = [pd.Period("2021-04", "M"), pd.Period("2021-05", "M")]
REGIMES = {
    "R1": (pd.Period("2017-01", "M"), pd.Period("2020-02", "M")),
    "R2": (pd.Period("2020-03", "M"), pd.Period("2021-12", "M")),
    "R3": (pd.Period("2022-01", "M"), pd.Period("2025-12", "M")),
    "R4": (pd.Period("2026-01", "M"), pd.Period("2099-12", "M")),
}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}


# --------------------------------------------------------------------------
# 1. Data
# --------------------------------------------------------------------------
def per(year, month) -> pd.Period:
    return pd.Period(year=int(year), month=MONTHS[month], freq="M")


def load_old():
    rows = []
    for f in sorted(RAW.glob("mospi_cpi_base2012_*_p*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d.get("data", []):
            if r["subgroup"] in ("General-Overall", "Consumer Food Price-Overall"):
                rows.append(dict(
                    period=per(r["year"], r["month"]),
                    series="gen" if r["subgroup"].startswith("General") else "food",
                    index=float(r["index"]),
                    pub_infl=None if r["inflation"] is None else float(r["inflation"]),
                    status=r["status"]))
    df = pd.DataFrame(rows).drop_duplicates(["period", "series"])
    return df


def load_new(pattern):
    rows = []
    for f in sorted(RAW.glob(pattern)):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d.get("data", []):
            if r.get("class") is not None:
                continue
            rows.append(dict(period=per(r["year"], r["month"]),
                             index=float(r["index"]),
                             pub_infl=None if r["inflation"] is None else float(r["inflation"])))
    return pd.DataFrame(rows).drop_duplicates("period").set_index("period").sort_index()


old = load_old()
og = old[old.series == "gen"].set_index("period").sort_index()
of = old[old.series == "food"].set_index("period").sort_index()
new_gen = load_new("mospi_cpi_base2024_current_*_general.json")
new_food = load_new("mospi_cpi_base2024_current_2026_foodgroup_p*.json")
back_gen = load_new("mospi_cpi_base2024_back_*_general.json")

log("=== DATA ===")
log(f"Old base (2012=100) General: {og.index.min()} to {og.index.max()} (n={len(og)})")
log(f"Old base (2012=100) CFPI   : {of.index.min()} to {of.index.max()} (n={len(of)})")
log(f"New base (2024=100) General: {new_gen.index.min()} to {new_gen.index.max()} (n={len(new_gen)})")
log(f"New base (2024=100) Food group (01.1): {new_food.index.min()} to {new_food.index.max()} (n={len(new_food)})")
log(f"Official back series General: {back_gen.index.min()} to {back_gen.index.max()} (n={len(back_gen)})")
log("Status flags != 'F' (General/CFPI): " + "; ".join(
    f"{p} {s}:{st}" for p, s, st in old.loc[old.status != "F", ["period", "series", "status"]].itertuples(index=False)))


def yoy(idx: pd.Series) -> pd.Series:
    s = idx.copy()
    lag = s.copy()
    lag.index = lag.index + 12
    return (100.0 * (s / lag.reindex(s.index) - 1.0)).dropna()


pi_old_gen = yoy(og["index"])
pi_old_food = yoy(of["index"])
d1 = (pi_old_gen - og["pub_infl"].reindex(pi_old_gen.index)).abs().dropna()
d2 = (pi_old_food - of["pub_infl"].reindex(pi_old_food.index)).abs().dropna()
log(f"Check: y-o-y computed from 2012-base indices vs published: max |diff| General {d1.max():.3f} pp, CFPI {d2.max():.3f} pp")

# Linking factor checks
chk = (back_gen["index"] - og["index"].reindex(back_gen.index) * LF_COMBINED).abs()
log(f"Check: official back series vs old x {LF_COMBINED}: max |diff| = {chk.max():.3f} index points "
    f"(back series is published to 1-2 decimals)")
gm_new = np.exp(np.log(new_gen.loc["2025-01":"2025-12", "index"]).mean())
gm_old = np.exp(np.log(og.loc["2025-01":"2025-12", "index"]).mean())
log(f"Check: geometric-mean ratio new/old over 2025 = {gm_new / gm_old:.4f} (MoSPI LF {LF_COMBINED})")

pi_new_gen = yoy(new_gen["index"])  # 2026 only (2025 is the first new-base year)
d3 = (pi_new_gen - new_gen["pub_infl"].reindex(pi_new_gen.index)).abs()
log(f"Check: 2026 y-o-y from 2024-base indices vs published: max |diff| {d3.max():.3f} pp")
# Cross-base y-o-y (2026 new index over linked 2025 old index), for comparison only
linked_2025 = og["index"].loc["2025-01":"2025-12"] * LF_COMBINED
cross = pd.Series({p: 100 * (new_gen.loc[p, "index"] / linked_2025.loc[p - 12] - 1) for p in pi_new_gen.index})
log("2026 headline y-o-y: official new-basket vs cross-base (new 2026 / linked old 2025), pp:")
for p in pi_new_gen.index:
    log(f"   {p}: official {pi_new_gen[p]:5.2f}  cross-base {cross[p]:5.2f}  diff {cross[p] - pi_new_gen[p]:+.2f}")

# Final series: headline = old y-o-y to 2025-12, new-basket y-o-y from 2026-01
headline = pd.concat([pi_old_gen, pi_new_gen]).sort_index()
food_ext = pd.concat([pi_old_food, new_food["pub_infl"].dropna()]).sort_index()  # spliced (features/indicator only)
food_2012 = pi_old_food.copy()                                                     # target (2012 base only)
assert headline.index.is_unique and food_ext.index.is_unique
full = pd.period_range(headline.index.min(), headline.index.max(), freq="M")
assert headline.reindex(full).notna().all() and food_ext.reindex(full).notna().all()
log(f"Headline inflation series: {headline.index.min()} to {headline.index.max()} (n={len(headline)})")
log(f"Food inflation series (CFPI to 2025-12, new-base Food group from 2026-01): {food_ext.index.min()} to {food_ext.index.max()}")

pd.DataFrame({"headline_yoy": headline, "food_yoy_spliced": food_ext,
              "cfpi_yoy_2012base": food_2012.reindex(headline.index)}).rename_axis("month").to_csv(
    OUT / "data_inflation_series.csv", float_format="%.4f")


# --------------------------------------------------------------------------
# 2. Lag matrix and observable food-shock indicator
# --------------------------------------------------------------------------
def lag_frame(h: pd.Series, f: pd.Series) -> pd.DataFrame:
    cols = {}
    for L in range(1, NLAGS + 1):
        cols[f"h{L}"] = h.shift(L)
        cols[f"f{L}"] = f.shift(L)
    return pd.DataFrame(cols)


H = headline.reindex(full)
F = food_ext.reindex(full)
X_all = lag_frame(H, F)

# Food-shock indicator, known at forecast time for month t:
# d_s = F_s - F_{s-3}; S_t = 1{ d_{t-1} > 80th pct of {d_s : s <= t-1} }
dF = (F - F.shift(3)).dropna()
shock = {}
for t in full:
    past = dF[dF.index <= t - 1]
    if len(past) < 12:
        continue
    thr = np.quantile(past.values, SHOCK_Q)
    shock[t] = int(past.iloc[-1] > thr)
shock = pd.Series(shock)


# --------------------------------------------------------------------------
# 3. Point forecasters (expanding window, re-estimated monthly)
# --------------------------------------------------------------------------
def fit_ar(y_tr: np.ndarray, lags_tr: np.ndarray, lags_t: np.ndarray):
    n = len(y_tr)
    pmax = int(min(NLAGS, max(1, n // 4)))
    best = None
    for p in range(1, pmax + 1):
        Z = np.column_stack([np.ones(n), lags_tr[:, :p]])
        b, *_ = np.linalg.lstsq(Z, y_tr, rcond=None)
        e = y_tr - Z @ b
        ssr = float(e @ e)
        k = p + 1
        bic = n * math.log(ssr / n) + k * math.log(n)
        if best is None or bic < best[0]:
            best = (bic, p, b, ssr, k)
    _, p, b, ssr, k = best
    yhat = float(b[0] + lags_t[:p] @ b[1:])
    sd = math.sqrt(ssr / max(n - k, 1))
    return yhat, sd, p


def fit_en(X_tr: np.ndarray, y_tr: np.ndarray, x_t: np.ndarray):
    n = len(y_tr)
    sc = StandardScaler().fit(X_tr)
    Xs = sc.transform(X_tr)
    splits = int(min(5, max(2, n // 8)))
    m = ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9, 1.0], alphas=50, cv=TimeSeriesSplit(n_splits=splits),
                     max_iter=100000, tol=1e-6, selection="cyclic")
    m.fit(Xs, y_tr)
    e = y_tr - m.predict(Xs)
    k = int(np.sum(m.coef_ != 0)) + 1
    sd = math.sqrt(float(e @ e) / max(n - k, 1))
    yhat = float(m.predict(sc.transform(x_t.reshape(1, -1)))[0])
    return yhat, sd, k - 1


def point_forecasts(target: pd.Series, name: str) -> pd.DataFrame:
    target = target.reindex(full)
    own = "h" if name == "headline" else "f"
    own_cols = [f"{own}{L}" for L in range(1, NLAGS + 1)]
    last = target.dropna().index.max()
    recs = []
    for t in pd.period_range(FIRST_OOS, last, freq="M"):
        tr = pd.period_range(FIRST_TARGET, t - 1, freq="M")
        y_tr = target.reindex(tr).values
        X_tr = X_all.loc[tr].values
        assert not np.isnan(y_tr).any() and not np.isnan(X_tr).any()
        x_t = X_all.loc[t].values
        ar_hat, ar_sd, ar_p = fit_ar(y_tr, X_all.loc[tr, own_cols].values, X_all.loc[t, own_cols].values)
        en_hat, en_sd, en_k = fit_en(X_tr, y_tr, x_t)
        recs.append(dict(month=t, y=target[t], AR=ar_hat, AR_sd=ar_sd, AR_p=ar_p,
                         EN=en_hat, EN_sd=en_sd, EN_nnz=en_k, n_train=len(tr)))
    return pd.DataFrame(recs).set_index("month")


# --------------------------------------------------------------------------
# 4. Interval methods
# --------------------------------------------------------------------------
def cq(scores: np.ndarray, a: float):
    """ceil((n+1)(1-a))-th smallest score; returns (q, flag) with flag in {ok, cap, zero}."""
    n = len(scores)
    k = math.ceil((n + 1) * (1 - a) - 1e-12)
    s = np.sort(scores)
    if k > n:
        return float(s[-1]), "cap"   # level beyond the sample: capped at the largest score
    if k < 1:
        return 0.0, "zero"
    return float(s[k - 1]), "ok"


def build_intervals(pf: pd.DataFrame, fc: str, a: float = ALPHA) -> dict[str, pd.DataFrame]:
    """Returns {method_name: DataFrame(month, y, yhat, lo, hi, extra...)} over the evaluation sample,
    for nominal coverage 1 - a.  With a = ALPHA this reproduces the original script exactly."""
    resid = (pf["y"] - pf[fc])
    months = [t for t in pf.index if t >= EVAL_START]
    out = {}
    z = stats.norm.ppf(1 - a / 2)
    # (i) Gaussian, in-sample residual standard deviation
    g = pd.DataFrame({"y": pf.loc[months, "y"], "yhat": pf.loc[months, fc]})
    g["lo"] = g.yhat - z * pf.loc[months, f"{fc}_sd"]
    g["hi"] = g.yhat + z * pf.loc[months, f"{fc}_sd"]
    g["scale"] = pf.loc[months, f"{fc}_sd"]
    out["Gaussian"] = g
    for W in WINDOWS:
        # (ii) rolling split conformal; (iii) ACI on top; (iv) regime-conditional;
        # (v) NEW: error-based Gaussian on the same window of out-of-sample errors
        sc_rows, rc_rows, eb_rows, ebsd_rows = [], [], [], []
        aci_state = {gm: a for gm in GAMMAS}
        aci_rows = {gm: [] for gm in GAMMAS}
        for t in months:
            past = resid[resid.index < t].dropna()
            win = past.iloc[-W:]
            cal = win.abs().values
            assert len(cal) >= MIN_CAL, (t, len(cal))
            yhat, y = pf.loc[t, fc], pf.loc[t, "y"]
            q, _ = cq(cal, a)
            sc_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - q, hi=yhat + q, ncal=len(cal)))
            rmse = math.sqrt(float(np.mean(win.values ** 2)))
            eb_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - z * rmse, hi=yhat + z * rmse,
                                scale=rmse, ncal=len(cal)))
            sdd = float(np.std(win.values, ddof=1))
            ebsd_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - z * sdd, hi=yhat + z * sdd,
                                  scale=sdd, ncal=len(cal)))
            for gm in GAMMAS:
                a_t = aci_state[gm]
                qa, flag = cq(cal, a_t)
                lo, hi = yhat - qa, yhat + qa
                err = int(not (lo <= y <= hi))
                aci_rows[gm].append(dict(month=t, y=y, yhat=yhat, lo=lo, hi=hi, alpha_t=a_t, flag=flag))
                aci_state[gm] = a_t + gm * (a - err)
            s_t = shock[t]
            same = past[[shock.get(s, -1) == s_t for s in past.index]]
            fb = len(same) < MIN_CAL
            calg = cal if fb else same.iloc[-W:].abs().values
            qg, _ = cq(calg, a)
            rc_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - qg, hi=yhat + qg, shock=s_t,
                                fallback=int(fb), ncal=len(calg)))
        out[f"SCP W={W}"] = pd.DataFrame(sc_rows).set_index("month")
        for gm in GAMMAS:
            out[f"ACI g={gm} W={W}"] = pd.DataFrame(aci_rows[gm]).set_index("month")
        out[f"RC-SCP W={W}"] = pd.DataFrame(rc_rows).set_index("month")
        out[f"EB-Gauss W={W}"] = pd.DataFrame(eb_rows).set_index("month")
        out[f"EB-Gauss-sd W={W}"] = pd.DataFrame(ebsd_rows).set_index("month")
    return out


# --------------------------------------------------------------------------
# 5. Metrics
# --------------------------------------------------------------------------
def interval_score(lo, hi, y, a=ALPHA):
    return (hi - lo) + (2 / a) * (lo - y) * (y < lo) + (2 / a) * (y - hi) * (y > hi)


def christoffersen(hits: np.ndarray, p=ALPHA):
    """hits = 1 for a miss. Returns p-values (uc, ind, cc)."""
    hits = np.asarray(hits, int)
    n, x = len(hits), hits.sum()

    def ll(k, m, pr):
        out = 0.0
        if k > 0:
            out += k * math.log(pr) if pr > 0 else -np.inf
        if m - k > 0:
            out += (m - k) * math.log(1 - pr) if pr < 1 else -np.inf
        return out
    lr_uc = -2 * (ll(x, n, p) - ll(x, n, x / n))
    a, b = hits[:-1], hits[1:]
    n00 = int(np.sum((a == 0) & (b == 0))); n01 = int(np.sum((a == 0) & (b == 1)))
    n10 = int(np.sum((a == 1) & (b == 0))); n11 = int(np.sum((a == 1) & (b == 1)))
    p01 = n01 / (n00 + n01) if (n00 + n01) else 0.0
    p11 = n11 / (n10 + n11) if (n10 + n11) else 0.0
    p1 = (n01 + n11) / (n00 + n01 + n10 + n11)
    l_null = ll(n01 + n11, n00 + n01 + n10 + n11, p1)
    l_alt = ll(n01, n00 + n01, p01) + ll(n11, n10 + n11, p11)
    lr_ind = -2 * (l_null - l_alt)
    lr_cc = lr_uc + lr_ind
    return (stats.chi2.sf(lr_uc, 1), stats.chi2.sf(lr_ind, 1), stats.chi2.sf(lr_cc, 2))


def summarise(df: pd.DataFrame, mask=None, a=ALPHA) -> dict:
    d = df if mask is None else df[mask]
    n = len(d)
    if n == 0:
        return dict(n=0)
    hit = ~((d.lo <= d.y) & (d.y <= d.hi))
    x = int(hit.sum())
    return dict(n=n, misses=x, coverage=1 - x / n, width=float((d.hi - d.lo).mean()),
                IS=float(interval_score(d.lo, d.hi, d.y, a).mean()),
                kupiec_exact_p=float(stats.binomtest(x, n, a).pvalue),
                above=int((d.y > d.hi).sum()), below=int((d.y < d.lo).sum()))


def regime_masks(idx, last):
    m = {"All": np.ones(len(idx), bool)}
    for r, (a, b) in REGIMES.items():
        mm = (idx >= a) & (idx <= b)
        if mm.any():
            m[r] = mm
    s = shock.reindex(idx).values
    m["Shock"] = s == 1
    m["Normal"] = s == 0
    return m


# --------------------------------------------------------------------------
# 6. Run
# --------------------------------------------------------------------------
all_rows, interval_store, point_store = [], {}, {}
for tname, tser in (("headline", headline), ("food", food_2012)):
    log(f"\n=== TARGET: {tname} ===")
    pf = point_forecasts(tser, tname)
    point_store[tname] = pf
    pf.to_csv(OUT / f"point_forecasts_{tname}.csv", float_format="%.6f")
    ev = pf[pf.index >= EVAL_START]
    log(f"OOS point forecasts {pf.index.min()}..{pf.index.max()}; evaluation {ev.index.min()}..{ev.index.max()} (n={len(ev)})")
    masks_pt = regime_masks(ev.index, ev.index.max())
    for fc in ("AR", "EN"):
        e = ev.y - ev[fc]
        txt = ", ".join(f"{k} {math.sqrt(np.mean(e[v] ** 2)):.3f}" for k, v in masks_pt.items() if v.any())
        log(f"RMSE {fc}: {txt}")
        all_rows.append(dict(target=tname, forecaster=fc, method="(point RMSE)", regime="All", nominal=np.nan,
                             n=len(e), RMSE=math.sqrt(float(np.mean(e ** 2)))))
    for fc in ("AR", "EN"):
        for a in ALPHAS:
            ints = build_intervals(pf, fc, a)
            for meth, df in ints.items():
                df = df.copy()
                df["IS"] = interval_score(df.lo, df.hi, df.y, a)
                df["miss"] = (~((df.lo <= df.y) & (df.y <= df.hi))).astype(int)
                interval_store[(tname, fc, meth, round(1 - a, 2))] = df
                puc, pind, pcc = christoffersen(df["miss"].values, p=a)
                for reg, m in regime_masks(df.index, df.index.max()).items():
                    s = summarise(df, m, a)
                    row = dict(target=tname, forecaster=fc, method=meth, regime=reg, nominal=round(1 - a, 2), **s)
                    if reg == "All":
                        row.update(LR_uc_p=puc, LR_ind_p=pind, LR_cc_p=pcc)
                        if "fallback" in df:
                            row["fallback_share"] = float(df.fallback.mean())
                        if "flag" in df:
                            row["aci_capped"] = int((df.flag == "cap").sum())
                            row["aci_zero"] = int((df.flag == "zero").sum())
                    all_rows.append(row)
                drop = df.index.isin(IMPUTED + IMPUTED_BASE)
                s = summarise(df, ~drop, a)
                all_rows.append(dict(target=tname, forecaster=fc, method=meth, nominal=round(1 - a, 2),
                                     regime="All excl. Apr-May 2020/2021", **s))

res = pd.DataFrame(all_rows)
res.to_csv(OUT / "results_all_levels.csv", index=False, float_format="%.6f")

paths = []
for (tname, fc, meth, nom), df in interval_store.items():
    cols = [c for c in ("y", "yhat", "lo", "hi", "IS", "miss", "scale") if c in df]
    d = df[cols].copy()
    d.insert(0, "nominal", nom); d.insert(0, "method", meth); d.insert(0, "forecaster", fc); d.insert(0, "target", tname)
    d["regime"] = [next((r for r, (s0, s1) in REGIMES.items() if s0 <= p <= s1), "") for p in d.index]
    d["shock"] = shock.reindex(d.index).values
    paths.append(d.reset_index())
pd.concat(paths).to_csv(OUT / "interval_paths_levels.csv", index=False, float_format="%.6f")

# --------------------------------------------------------------------------
# 7. Check: existing methods at 90% reproduce the original results exactly
# --------------------------------------------------------------------------
orig = pd.read_csv(ORIG_OUT / "results_all.csv")
orig = orig[orig.method != "(point RMSE)"]
new90 = res[(res.nominal == 0.9)].set_index(["target", "forecaster", "method", "regime"])
maxdiff = 0.0
nchk = 0
for _, r in orig.iterrows():
    k = (r.target, r.forecaster, r.method, r.regime)
    for c in ("n", "misses", "coverage", "width", "IS", "kupiec_exact_p"):
        maxdiff = max(maxdiff, abs(float(new90.loc[k, c]) - float(r[c])))
        nchk += 1
log(f"\nCHECK vs illustration/output/results_all.csv: {len(orig)} rows, {nchk} values, max |diff| = {maxdiff:.2e} "
    f"(original stored to 4 dp)")
assert maxdiff < 1e-4

log("\n=== HEADLINE, nominal 0.90, key rows ===")
for fc in ("AR", "EN"):
    for meth in ("Gaussian", "EB-Gauss W=36", "EB-Gauss W=60", "EB-Gauss-sd W=36", "EB-Gauss-sd W=60",
                 "SCP W=36", "SCP W=60"):
        sub = res[(res.target == "headline") & (res.forecaster == fc) & (res.method == meth) & (res.nominal == 0.9)]
        parts = [f"{r.regime} {r.coverage:.3f} ({int(r.misses)}/{int(r.n)})" for r in sub.itertuples()
                 if r.regime in ("All", "R1", "R2", "R3", "R4")]
        al = sub[sub.regime == "All"].iloc[0]
        log(f"{fc} | {meth}: " + "; ".join(parts) + f" | width {al.width:.3f} IS {al.IS:.3f} LR_cc p {al.LR_cc_p:.3f}")
(OUT / "run_log2.txt").write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
print("done")
