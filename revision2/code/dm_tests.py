"""Diebold-Mariano tests on interval-score loss differentials, window comparison, and the
numbers behind the Proposition 1 discussion.

Input : revision2/output/interval_paths_levels.csv, results_all_levels.csv (run_illustration2.py)
Output: revision2/output/dm_tests.csv        (all comparisons, levels, regimes)
        revision2/output/window_comparison.csv
        revision2/output/prop1_numbers.txt
        revision2/table_baseline_dm.tex, revision2/table_baseline_dm.csv
DM test: d_t = IS(A)_t - IS(B)_t (negative mean: A has the lower score). Long-run variance by
Newey-West (Bartlett kernel, lag L = floor(4 (n/100)^(2/9))); statistic multiplied by the
Harvey-Leybourne-Newbold factor sqrt((n + 1 - 2h + h(h-1)/n) / n) with h = 1 and compared with
t(n-1). The h = 1 textbook version (no autocovariances) is also stored (columns *_L0).
Run: python -I revision2/code/dm_tests.py
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

R2D = Path(__file__).resolve().parents[1]
OUT = R2D / "output"
P = pd.read_csv(OUT / "interval_paths_levels.csv")
P["nominal"] = P.nominal.round(2)
RES = pd.read_csv(OUT / "results_all_levels.csv")
RES["nominal"] = RES.nominal.round(2)
H = P[P.target == "headline"]


def nw_lrv(d, L):
    d = d - d.mean()
    n = len(d)
    g0 = float(d @ d) / n
    s = g0
    for k in range(1, L + 1):
        if k >= n:
            break
        gk = float(d[k:] @ d[:-k]) / n
        s += 2 * (1 - k / (L + 1)) * gk
    return s


def dm(d, h=1, L=None):
    d = np.asarray(d, float)
    n = len(d)
    if L is None:
        L = int(math.floor(4 * (n / 100) ** (2 / 9)))
    lrv = nw_lrv(d, L)
    if lrv <= 0:
        return np.nan, np.nan, L
    stat = d.mean() / math.sqrt(lrv / n)
    stat *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p = 2 * stats.t.sf(abs(stat), df=n - 1)
    return stat, p, L


def series(fc, meth, nom):
    s = H[(H.forecaster == fc) & (H.method == meth) & (H.nominal == nom)].set_index("month")
    assert len(s) == 117, (fc, meth, nom, len(s))
    return s


CONF = ["SCP", "ACI g=0.005", "ACI g=0.02", "RC-SCP"]
LAB = {"Gaussian": "Gaussian, in-sample", "EB": "Gaussian, OOS errors",
       "SCP": "Split conformal", "ACI g=0.005": r"ACI, $\gamma=0.005$", "ACI g=0.02": r"ACI, $\gamma=0.02$",
       "RC-SCP": r"Regime-cond.\ SCP"}
REGS = ["All", "R1", "R2", "R3", "R4"]

rows = []
for fc in ("AR", "EN"):
    for nom in (0.9, 0.7, 0.5):
        for W in (36, 60):
            pairs = [(f"{c} W={W}", "Gaussian") for c in CONF] + [(f"{c} W={W}", f"EB-Gauss W={W}") for c in CONF] \
                    + [(f"EB-Gauss W={W}", "Gaussian"), (f"EB-Gauss-sd W={W}", "Gaussian")]
            for A, B in pairs:
                a, b = series(fc, A, nom), series(fc, B, nom)
                for reg in REGS:
                    m = (a.regime == reg) if reg != "All" else np.ones(len(a), bool)
                    d = (a.IS - b.IS)[m].values
                    st, p, L = dm(d)
                    st0, p0, _ = dm(d, L=0)
                    rows.append(dict(forecaster=fc, nominal=nom, W=W, A=A, B=B, regime=reg, n=len(d),
                                     IS_A=a.IS[m].mean(), IS_B=b.IS[m].mean(), mean_d=d.mean(),
                                     DM_HLN=st, p=p, NW_lag=L, DM_HLN_L0=st0, p_L0=p0))
        # window comparison W=60 vs W=36, same method
        for meth in CONF + ["EB-Gauss"]:
            a, b = series(fc, f"{meth} W=60", nom), series(fc, f"{meth} W=36", nom)
            for reg in REGS:
                m = (a.regime == reg) if reg != "All" else np.ones(len(a), bool)
                d = (a.IS - b.IS)[m].values
                st, p, L = dm(d)
                st0, p0, _ = dm(d, L=0)
                rows.append(dict(forecaster=fc, nominal=nom, W="60 vs 36", A=f"{meth} W=60", B=f"{meth} W=36",
                                 regime=reg, n=len(d), IS_A=a.IS[m].mean(), IS_B=b.IS[m].mean(), mean_d=d.mean(),
                                 DM_HLN=st, p=p, NW_lag=L, DM_HLN_L0=st0, p_L0=p0))
DMT = pd.DataFrame(rows)
DMT.to_csv(OUT / "dm_tests.csv", index=False, float_format="%.4f")

# ---------------- window comparison of mean interval scores ----------------
def get(fc, meth, nom, reg, col, target="headline"):
    r = RES[(RES.target == target) & (RES.forecaster == fc) & (RES.method == meth) & (RES.nominal == nom) & (RES.regime == reg)]
    return float(r.iloc[0][col])


wc = []
for fc in ("AR", "EN"):
    for nom in (0.9, 0.7, 0.5):
        g = get(fc, "Gaussian", nom, "All", "IS")
        for meth in ["EB-Gauss", "EB-Gauss-sd"] + CONF:
            r = dict(forecaster=fc, nominal=nom, method=meth, IS_Gaussian_insample=g)
            for W in (36, 60):
                r[f"IS_W{W}"] = get(fc, f"{meth} W={W}", nom, "All", "IS")
                r[f"width_W{W}"] = get(fc, f"{meth} W={W}", nom, "All", "width")
                r[f"cov_W{W}"] = get(fc, f"{meth} W={W}", nom, "All", "coverage")
                r[f"lower_than_Gaussian_W{W}"] = r[f"IS_W{W}"] < g
            r["width_Gaussian"] = get(fc, "Gaussian", nom, "All", "width")
            wc.append(r)
WC = pd.DataFrame(wc)
WC.to_csv(OUT / "window_comparison.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(WC[WC.nominal == 0.9].round(3).to_string(index=False))
print(WC[WC.nominal != 0.9][["forecaster", "nominal", "method", "IS_Gaussian_insample", "IS_W36", "IS_W60"]].round(3).to_string(index=False))

# ---------------- Proposition 1 numbers ----------------
z = stats.norm.ppf(0.95)
lines = []
for fc in ("AR", "EN"):
    g = series(fc, "Gaussian", 0.9)
    e = g.y - g.yhat
    r2 = g.regime == "R2"
    s2, s1 = math.sqrt((e[r2] ** 2).mean()), math.sqrt((e[~r2] ** 2).mean())
    sd_r2, sd_calm = g.scale[r2].mean(), g.scale[~r2].mean()
    imp_r2 = (2 * stats.norm.cdf(z * g.scale[r2] / s2) - 1).mean()
    imp_calm = (2 * stats.norm.cdf(z * g.scale[~r2] / s1) - 1).mean()
    cov_r2 = 1 - g.miss[r2].mean(); k = int((1 - g.miss[r2]).sum()); n = int(r2.sum())
    # proposition limit and floor, with this forecaster's scale ratio
    ratio = s2 / s1; p = n / 117

    def F(q, s): return 2 * stats.norm.cdf(q / s) - 1
    from scipy.optimize import brentq
    qstar = brentq(lambda q: (1 - p) * F(q, s1) + p * F(q, s2) - 0.9, 1e-6, 50)
    lim, floor = F(qstar, s2), 2 * stats.norm.cdf(z / ratio) - 1
    eb = series(fc, "EB-Gauss W=36", 0.9)
    lines += [
        f"{fc}: R2 RMSE s2 = {s2:.3f}, other months s1 = {s1:.3f}, ratio {ratio:.3f}, p = {p:.3f}",
        f"   Prop.1(a) limit for R2 with this ratio: {lim:.3f}; floor 2Phi(z s1/s2)-1 = {floor:.3f}",
        f"   in-sample residual sd used by the Gaussian interval: mean {sd_r2:.3f} in R2, {sd_calm:.3f} elsewhere",
        f"   sd_in / s2 (R2) = {sd_r2 / s2:.3f};  sd_in / s1 (other) = {sd_calm / s1:.3f}",
        f"   implied coverage if errors were N(0, s_k^2): R2 {imp_r2:.3f}, other months {imp_calm:.3f}",
        f"   observed Gaussian coverage: R2 {cov_r2:.3f} ({k}/{n}), other months {1 - g.miss[~r2].mean():.3f}",
        f"   P(X <= {k}) for X ~ Bin({n}, {lim:.3f}) = {stats.binom.cdf(k, n, lim):.3f}; "
        f"Bin({n}, {floor:.3f}): {stats.binom.cdf(k, n, floor):.3f}",
        f"   95% Clopper-Pearson CI for R2 coverage: "
        f"[{stats.binomtest(k, n).proportion_ci(method='exact').low:.3f}, {stats.binomtest(k, n).proportion_ci(method='exact').high:.3f}]",
        f"   out-of-sample-error Gaussian (W=36) R2: mean scale {eb.scale[r2].mean():.3f}, coverage {1 - eb.miss[r2].mean():.3f}",
    ]
txt = "\n".join(lines)
(OUT / "prop1_numbers.txt").write_text(txt + "\n", encoding="utf-8")
print(txt)

# ---------------- LaTeX table (nominal 90 per cent, full sample) ----------------
def fmt_dm(A, B, fc, W, nom=0.9, reg="All"):
    r = DMT[(DMT.forecaster == fc) & (DMT.nominal == nom) & (DMT.W == W) & (DMT.A == A) & (DMT.B == B) & (DMT.regime == reg)]
    if r.empty:
        return "", np.nan, np.nan
    r = r.iloc[0]
    return f"{r.DM_HLN:.2f} ({r.p:.2f})".replace("-", "$-$"), r.DM_HLN, r.p


tex = [r"\begin{tabular}{@{}lcccccc@{}}", r"\toprule",
       r" & \multicolumn{2}{c}{Coverage} & & & \multicolumn{2}{c}{DM ($p$) vs Gaussian} \\",
       r"\cmidrule(lr){2-3}\cmidrule(l){6-7}",
       r"Interval & All & R2 & Width & IS & in-sample & OOS errors \\"]
csv_rows = []
for W in (36, 60):
    for fc in ("AR", "EN"):
        tex.append(r"\midrule")
        tex.append(r"\multicolumn{7}{@{}l}{\emph{%s, calibration window $W=%d$}}\\" % ("Autoregression" if fc == "AR" else "Elastic net", W))
        meths = ["Gaussian", f"EB-Gauss W={W}"] + [f"{c} W={W}" for c in CONF]
        for j, meth in enumerate(meths):
            key = "Gaussian" if meth == "Gaussian" else ("EB" if meth.startswith("EB") else meth.split(" W=")[0])
            c_all = get(fc, meth, 0.9, "All", "coverage"); c_r2 = get(fc, meth, 0.9, "R2", "coverage")
            p_all = get(fc, meth, 0.9, "All", "kupiec_exact_p"); p_r2 = get(fc, meth, 0.9, "R2", "kupiec_exact_p")
            w = get(fc, meth, 0.9, "All", "width"); s = get(fc, meth, 0.9, "All", "IS")
            d1, s1_, p1 = ("--", np.nan, np.nan) if meth == "Gaussian" else fmt_dm(meth, "Gaussian", fc, W)
            if meth == "Gaussian" or meth.startswith("EB"):
                d2, s2_, p2 = "--", np.nan, np.nan
            else:
                d2, s2_, p2 = fmt_dm(meth, f"EB-Gauss W={W}", fc, W)
            st = lambda p: "$^{*}$" if p < 0.05 else ""  # noqa: E731
            tex.append(" & ".join([LAB[key], f"{c_all:.2f}{st(p_all)}", f"{c_r2:.2f}{st(p_r2)}",
                                   f"{w:.2f}", f"{s:.2f}", d1, d2]) + r" \\")
            csv_rows.append(dict(W=W, forecaster=fc, interval=meth, cov_All=c_all, kupiec_p_All=p_all, cov_R2=c_r2,
                                 kupiec_p_R2=p_r2, width=w, IS=s, DM_vs_Gauss_insample=s1_, p_vs_Gauss_insample=p1,
                                 DM_vs_Gauss_errors=s2_, p_vs_Gauss_errors=p2))
tex += [r"\bottomrule", r"\end{tabular}"]
caption = (r"Out-of-sample error-based Gaussian intervals and Diebold--Mariano tests on interval scores, "
           r"nominal 90 per cent, headline CPI inflation, January 2017 to September 2026 ($n=117$)")
notes = (r"Gaussian, in-sample: point forecast $\pm z\,\hat\sigma$ with the in-sample residual standard deviation "
         r"(as in Table~\ref{tab:coverage}); Gaussian, OOS errors: point forecast $\pm z$ times the root mean "
         r"squared out-of-sample (OOS) error of the previous $W$ months, the same errors that calibrate the conformal intervals. "
         r"The in-sample Gaussian rows do not depend on $W$. R2: March 2020 to December 2021 ($n=22$). "
         r"Width and IS (mean interval score) in percentage points. DM: Diebold--Mariano statistic for the "
         r"interval-score differential (row interval minus the benchmark; negative values favour the row "
         r"interval). Benchmarks: the in-sample Gaussian interval and the Gaussian interval from OOS errors with the same $W$. Long-run variance with " + str(dm(np.zeros(117) + np.arange(117))[2]) + r" lags (Newey--West, Bartlett kernel); Harvey--Leybourne--Newbold small-sample correction; "
         r"$p$-values from $t_{116}$ in parentheses.")
notes2 = (r"$^{*}$Exact two-sided binomial test of a 10 per cent miss rate "
         r"rejects at the 5 per cent level.")
full = ["% generated by revision2/code/dm_tests.py", r"\begin{table}[htbp]", r"\caption{" + caption + r"}\label{tab:baseline_dm}",
        r"\footnotesize", r"\setlength{\tabcolsep}{4pt}"] + tex + [
        r"\footnotetext{" + notes + "}", r"\footnotetext{" + notes2 + "}", r"\footnotetext{Source: own calculations from MoSPI CPI data.}", r"\end{table}"]
(R2D / "table_baseline_dm.tex").write_text("\n".join(full) + "\n", encoding="utf-8")
pd.DataFrame(csv_rows).to_csv(R2D / "table_baseline_dm.csv", index=False, float_format="%.4f")
print("\n".join(tex))
