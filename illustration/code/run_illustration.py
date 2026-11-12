"""Empirical illustration: coverage of standard 90% prediction intervals for
Indian CPI inflation across regimes.

Run from anywhere with:  python -I illustration/code/run_illustration.py
Reads only illustration/data_raw/, writes only illustration/output/.
Deterministic: no random sampling is used; seeds are fixed anyway.
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

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw"
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

LOG_LINES: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    LOG_LINES.append(msg)


# --------------------------------------------------------------------------
# Settings (fixed before estimation)
# --------------------------------------------------------------------------
ALPHA = 0.10
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


def build_intervals(pf: pd.DataFrame, fc: str) -> dict[str, pd.DataFrame]:
    """Returns {method_name: DataFrame(month, y, yhat, lo, hi, extra...)} over the evaluation sample."""
    resid = (pf["y"] - pf[fc])
    months = [t for t in pf.index if t >= EVAL_START]
    out = {}
    z = stats.norm.ppf(1 - ALPHA / 2)
    # (i) Gaussian
    g = pd.DataFrame({"y": pf.loc[months, "y"], "yhat": pf.loc[months, fc]})
    g["lo"] = g.yhat - z * pf.loc[months, f"{fc}_sd"]
    g["hi"] = g.yhat + z * pf.loc[months, f"{fc}_sd"]
    out["Gaussian"] = g
    for W in WINDOWS:
        # (ii) rolling split conformal; (iii) ACI on top; (iv) regime-conditional
        sc_rows, rc_rows = [], []
        aci_state = {gm: ALPHA for gm in GAMMAS}
        aci_rows = {gm: [] for gm in GAMMAS}
        for t in months:
            past = resid[resid.index < t].dropna()
            cal = past.iloc[-W:].abs().values
            assert len(cal) >= MIN_CAL, (t, len(cal))
            yhat, y = pf.loc[t, fc], pf.loc[t, "y"]
            q, _ = cq(cal, ALPHA)
            sc_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - q, hi=yhat + q, ncal=len(cal)))
            for gm in GAMMAS:
                a_t = aci_state[gm]
                qa, flag = cq(cal, a_t)
                lo, hi = yhat - qa, yhat + qa
                err = int(not (lo <= y <= hi))
                aci_rows[gm].append(dict(month=t, y=y, yhat=yhat, lo=lo, hi=hi, alpha_t=a_t, flag=flag))
                aci_state[gm] = a_t + gm * (ALPHA - err)
            s_t = shock[t]
            same = past[[shock.get(s, -1) == s_t for s in past.index]]
            fb = len(same) < MIN_CAL
            calg = cal if fb else same.iloc[-W:].abs().values
            qg, _ = cq(calg, ALPHA)
            rc_rows.append(dict(month=t, y=y, yhat=yhat, lo=yhat - qg, hi=yhat + qg, shock=s_t,
                                fallback=int(fb), ncal=len(calg)))
        out[f"SCP W={W}"] = pd.DataFrame(sc_rows).set_index("month")
        for gm in GAMMAS:
            out[f"ACI g={gm} W={W}"] = pd.DataFrame(aci_rows[gm]).set_index("month")
        out[f"RC-SCP W={W}"] = pd.DataFrame(rc_rows).set_index("month")
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


def summarise(df: pd.DataFrame, mask=None) -> dict:
    d = df if mask is None else df[mask]
    n = len(d)
    if n == 0:
        return dict(n=0)
    hit = ~((d.lo <= d.y) & (d.y <= d.hi))
    x = int(hit.sum())
    return dict(n=n, misses=x, coverage=1 - x / n, width=float((d.hi - d.lo).mean()),
                IS=float(interval_score(d.lo, d.hi, d.y).mean()),
                kupiec_exact_p=float(stats.binomtest(x, n, ALPHA).pvalue))


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
    pf.to_csv(OUT / f"point_forecasts_{tname}.csv", float_format="%.4f")
    ev = pf[pf.index >= EVAL_START]
    log(f"OOS point forecasts {pf.index.min()}..{pf.index.max()}; evaluation {ev.index.min()}..{ev.index.max()} (n={len(ev)})")
    log(f"AR lag order chosen by BIC over evaluation sample: min {ev.AR_p.min()}, median {ev.AR_p.median():.0f}, max {ev.AR_p.max()}")
    log(f"Elastic net non-zero coefficients: min {ev.EN_nnz.min()}, median {ev.EN_nnz.median():.0f}, max {ev.EN_nnz.max()}")
    masks_pt = regime_masks(ev.index, ev.index.max())
    for fc in ("AR", "EN"):
        e = ev.y - ev[fc]
        txt = ", ".join(f"{k} {math.sqrt(np.mean(e[v] ** 2)):.3f}" for k, v in masks_pt.items() if v.any())
        log(f"RMSE {fc}: {txt}")
        all_rows.append(dict(target=tname, forecaster=fc, method="(point RMSE)", regime="All",
                             n=len(e), RMSE=math.sqrt(float(np.mean(e ** 2)))))
    for fc in ("AR", "EN"):
        ints = build_intervals(pf, fc)
        for meth, df in ints.items():
            interval_store[(tname, fc, meth)] = df
            hits = (~((df.lo <= df.y) & (df.y <= df.hi))).astype(int).values
            puc, pind, pcc = christoffersen(hits)
            for reg, m in regime_masks(df.index, df.index.max()).items():
                s = summarise(df, m)
                row = dict(target=tname, forecaster=fc, method=meth, regime=reg, **s)
                if reg == "All":
                    row.update(LR_uc_p=puc, LR_ind_p=pind, LR_cc_p=pcc)
                    if "fallback" in df:
                        row["fallback_share"] = float(df.fallback.mean())
                        row["fallback_shock_months"] = int(df.fallback[df.shock == 1].sum())
                        row["n_shock_months"] = int((df.shock == 1).sum())
                    if "flag" in df:
                        row["aci_capped"] = int((df.flag == "cap").sum())
                        row["aci_zero"] = int((df.flag == "zero").sum())
                all_rows.append(row)
            # sensitivity: drop imputed and imputed-base months
            drop = df.index.isin(IMPUTED + IMPUTED_BASE)
            s = summarise(df, ~drop)
            all_rows.append(dict(target=tname, forecaster=fc, method=meth, regime="All excl. Apr-May 2020/2021", **s))

res = pd.DataFrame(all_rows)
res.to_csv(OUT / "results_all.csv", index=False, float_format="%.4f")

# Interval paths (all methods) for transparency
paths = []
for (tname, fc, meth), df in interval_store.items():
    d = df[["y", "yhat", "lo", "hi"]].copy()
    d.insert(0, "method", meth); d.insert(0, "forecaster", fc); d.insert(0, "target", tname)
    paths.append(d.reset_index())
pd.concat(paths).to_csv(OUT / "interval_paths.csv", index=False, float_format="%.4f")


# --------------------------------------------------------------------------
# 7. Tables
# --------------------------------------------------------------------------
MAIN_METHODS = [("Gaussian", "Gaussian"), ("SCP W=36", "Split conformal"),
                ("ACI g=0.005 W=36", r"ACI, $\gamma=0.005$"), ("ACI g=0.02 W=36", r"ACI, $\gamma=0.02$"),
                ("RC-SCP W=36", "Regime-cond.\\ SCP")]
ROB_METHODS = [("SCP W=60", "Split conformal"), ("ACI g=0.005 W=60", r"ACI, $\gamma=0.005$"),
               ("ACI g=0.02 W=60", r"ACI, $\gamma=0.02$"), ("RC-SCP W=60", "Regime-cond.\\ SCP")]
FC_LABEL = {"AR": "AR", "EN": "EN"}


def get(tname, fc, meth, reg, col):
    r = res[(res.target == tname) & (res.forecaster == fc) & (res.method == meth) & (res.regime == reg)]
    return r.iloc[0][col] if len(r) else np.nan


def make_table(tname, methods, fname, regs):
    ref = interval_store[(tname, "EN", "Gaussian")]
    masks = regime_masks(ref.index, ref.index.max())
    regs = [r for r in regs if r in masks]
    ns = {r: int(masks[r].sum()) for r in regs}
    header = ["Forecaster", "Interval"] + [f"{'All' if r == 'All' else r} ({ns[r]})" for r in regs] + \
             ["Width", "IS", r"$p_{\mathrm{cc}}$"]
    csv_rows, tex = [], []
    tex.append(r"\begin{tabular}{ll" + "c" * len(regs) + "ccc}")
    tex.append(r"\toprule")
    tex.append(" & & \\multicolumn{%d}{c}{Empirical coverage (nominal 0.90; $n$ in parentheses)} & & & \\\\" % len(regs))
    tex.append(r"\cmidrule(lr){3-%d}" % (2 + len(regs)))
    tex.append(" & ".join(header).replace("Shock", "Food shock") + r" \\")
    tex.append(r"\midrule")
    for i, fc in enumerate(("AR", "EN")):
        rm = math.sqrt(float(np.mean((point_store[tname].loc[ref.index, 'y'] - point_store[tname].loc[ref.index, fc]) ** 2)))
        for j, (meth, lab) in enumerate(methods):
            cells, crow = [], dict(target=tname, forecaster=fc, interval=meth, point_RMSE=rm)
            for r in regs:
                c = get(tname, fc, meth, r, "coverage"); p = get(tname, fc, meth, r, "kupiec_exact_p")
                star = "$^{*}$" if p < 0.05 else ""
                cells.append(f"{c:.2f}{star}")
                crow[f"cov_{r}"] = c; crow[f"n_{r}"] = ns[r]; crow[f"kupiec_p_{r}"] = p
            w = get(tname, fc, meth, "All", "width"); s = get(tname, fc, meth, "All", "IS")
            pcc = get(tname, fc, meth, "All", "LR_cc_p")
            crow.update(width=w, IS=s, LR_uc_p=get(tname, fc, meth, "All", "LR_uc_p"),
                        LR_ind_p=get(tname, fc, meth, "All", "LR_ind_p"), LR_cc_p=pcc)
            csv_rows.append(crow)
            first = f"{FC_LABEL[fc]} (RMSE {rm:.2f})" if j == 0 else ""
            tex.append(" & ".join([first, lab] + cells + [f"{w:.2f}", f"{s:.2f}", f"{pcc:.3f}"]) + r" \\")
        if i == 0:
            tex.append(r"\midrule")
    tex.append(r"\bottomrule")
    tex.append(r"\end{tabular}")
    (OUT / f"{fname}.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    pd.DataFrame(csv_rows).to_csv(OUT / f"{fname}.csv", index=False, float_format="%.4f")


REG_COLS = ["All", "R1", "R2", "R3", "R4", "Shock", "Normal"]
make_table("headline", MAIN_METHODS, "table_coverage", REG_COLS)
make_table("headline", ROB_METHODS, "table_coverage_W60", REG_COLS)
make_table("food", MAIN_METHODS, "table_coverage_food", REG_COLS)


# --------------------------------------------------------------------------
# 8. Figure
# --------------------------------------------------------------------------
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42, "axes.linewidth": 0.6})
g = interval_store[("headline", "EN", "Gaussian")]
a = interval_store[("headline", "EN", "ACI g=0.005 W=36")]
x = g.index.to_timestamp()
fig, ax = plt.subplots(figsize=(174 / 25.4, 80 / 25.4))
shade = {"R1": None, "R2": "0.90", "R3": None, "R4": "0.80"}
for r, (s0, s1) in REGIMES.items():
    s1 = min(s1, g.index.max())
    if s0 > g.index.max():
        continue
    x0 = (s0.to_timestamp() - pd.Timedelta(days=15)); x1 = (s1.to_timestamp() + pd.Timedelta(days=15))
    if shade[r]:
        ax.axvspan(x0, x1, color=shade[r], lw=0, zorder=0)
    ax.text(x0 + (x1 - x0) / 2, 1.0, r, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8)
ax.plot(x, g.lo, color="0.0", lw=0.8, ls=(0, (4, 2)), zorder=2)
ax.plot(x, g.hi, color="0.0", lw=0.8, ls=(0, (4, 2)), zorder=2, label="Gaussian 90% interval")
ax.plot(x, a.lo, color="0.45", lw=1.0, zorder=2)
ax.plot(x, a.hi, color="0.45", lw=1.0, zorder=2, label=r"ACI 90% interval ($\gamma=0.005$, $W=36$)")
ax.plot(x, g.y, color="0.0", lw=1.3, zorder=3, label="Actual headline CPI inflation")
imp = [p for p in IMPUTED if p in g.index]
ax.plot([p.to_timestamp() for p in imp], g.y.loc[imp], ls="none", marker="o", ms=4, mfc="white", mec="0.0",
        mew=0.8, zorder=4, label="Imputed index (Apr–May 2020)")
# Apr-May 2021 indices are not imputed (MoSPI status F), but their y-o-y rates use the
# imputed Apr-May 2020 indices as base, so they are marked separately.
imp_b = [p for p in IMPUTED_BASE if p in g.index]
ax.plot([p.to_timestamp() for p in imp_b], g.y.loc[imp_b], ls="none", marker="s", ms=3.5, mfc="white",
        mec="0.0", mew=0.8, zorder=4, label="Rate on imputed base (Apr–May 2021)")
ax.set_ylabel("Year-on-year inflation (%)")
ax.set_xlim(x.min() - pd.Timedelta(days=20), x.max() + pd.Timedelta(days=20))
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="0.85", lw=0.4)
ax.set_axisbelow(True)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), frameon=False, ncol=2, handlelength=2.6)
fig.tight_layout(pad=0.4)
fig.savefig(OUT / "fig_intervals.pdf")
fig.savefig(OUT / "fig_intervals.png", dpi=300)
plt.close(fig)


# --------------------------------------------------------------------------
# 9. Log of key numbers
# --------------------------------------------------------------------------
log("\n=== FOOD-SHOCK INDICATOR ===")
ev_idx = point_store["headline"].index[point_store["headline"].index >= EVAL_START]
log(f"Shock months in headline evaluation sample: {int(shock.reindex(ev_idx).sum())} of {len(ev_idx)}")
log("\n=== KEY RESULTS (headline, coverage by regime) ===")
for fc in ("AR", "EN"):
    for meth, _ in MAIN_METHODS + ROB_METHODS:
        parts = []
        for r in REG_COLS:
            n = get("headline", fc, meth, r, "n")
            if not (isinstance(n, float) and np.isnan(n)) and n:
                parts.append(f"{r} {get('headline', fc, meth, r, 'coverage'):.3f} (n={int(n)}, miss={int(get('headline', fc, meth, r, 'misses'))}, p={get('headline', fc, meth, r, 'kupiec_exact_p'):.3f})")
        log(f"{fc} | {meth}: " + "; ".join(parts))
        log(f"      width {get('headline', fc, meth, 'All', 'width'):.3f}, IS {get('headline', fc, meth, 'All', 'IS'):.3f}, "
            f"LR_uc p {get('headline', fc, meth, 'All', 'LR_uc_p'):.3f}, LR_ind p {get('headline', fc, meth, 'All', 'LR_ind_p'):.3f}, "
            f"LR_cc p {get('headline', fc, meth, 'All', 'LR_cc_p'):.3f}")
(OUT / "run_log.txt").write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
print("done")
