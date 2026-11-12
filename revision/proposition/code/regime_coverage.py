"""Observable versus latent regimes in split conformal prediction: theory checks,
Monte Carlo and calibration to the Indian CPI illustration.

Supports the formal section requested in referee_assessment.md (plan item 6; M5.1-M5.4).
Reads ../../../illustration/output/*.csv and writes only ../output/.

Model. Regime G in {1, 2}, P(G = 2) = p. Forecast error e = s_G * Z, Z ~ N(0, 1),
s_1 = 1, s_2 = kappa > 1. Score R = |e|. H(x) = P(|Z| <= x) = 2 Phi(x) - 1.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import optimize, stats

ALPHA = 0.10
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
ILL = HERE.parents[2] / "illustration" / "output"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261103)
LOG: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    LOG.append(msg)


def H(x):
    return 2 * stats.norm.cdf(x) - 1


def Hinv(c):
    return stats.norm.ppf((1 + c) / 2)


# --------------------------------------------------------------------------
# Proposition 1: marginal calibration on a two-regime scale mixture
# --------------------------------------------------------------------------
def q_mix(kappa: float, p: float, a: float = ALPHA) -> float:
    """Population marginal quantile: (1-p) H(q) + p H(q/kappa) = 1 - a."""
    f = lambda q: (1 - p) * H(q) + p * H(q / kappa) - (1 - a)
    return optimize.brentq(f, 1e-9, 1e3)


def regime_cov(kappa: float, p: float, a: float = ALPHA) -> tuple[float, float]:
    q = q_mix(kappa, p, a)
    return float(H(q)), float(H(q / kappa))


def c2_limit(p: float, a: float = ALPHA) -> float:
    """lim_{kappa -> inf} of regime-2 coverage = max(0, 1 - a/p)."""
    return max(0.0, 1 - a / p)


# --------------------------------------------------------------------------
# Proposition 3: misclassified labels
# --------------------------------------------------------------------------
def misclass_bound(kappa, p, e_fn, e_fp, a=ALPHA):
    """Lower bound of Proposition 3:
    cov2 >= (1-a) - e_fn [(1-a) - H(z/kappa)] - (1-e_fn) a (1-pi2)/pi2, z = Hinv(1-a)."""
    pi2 = p * (1 - e_fn) / (p * (1 - e_fn) + (1 - p) * e_fp)
    z = Hinv(1 - a)
    return float((1 - a) - e_fn * ((1 - a) - H(z / kappa)) - (1 - e_fn) * a * (1 - pi2) / pi2)


def misclass_cov(kappa, p, e_fn, e_fp, a=ALPHA):
    """Group-conditional calibration on a noisy label Ghat.
    e_fn = P(Ghat=1 | G=2) (missed bad regime), e_fp = P(Ghat=2 | G=1).
    Returns population coverage of true regime 2 and of true regime 1."""
    mass = {  # joint P(G=g, Ghat=h)
        (2, 2): p * (1 - e_fn), (2, 1): p * e_fn,
        (1, 2): (1 - p) * e_fp, (1, 1): (1 - p) * (1 - e_fp),
    }
    cov2 = cov1 = 0.0
    for h in (1, 2):
        tot = mass[(1, h)] + mass[(2, h)]
        if tot <= 0:
            continue
        pi = mass[(2, h)] / tot  # share of true regime 2 in cell h
        q = q_mix(kappa, pi, a) if 0 < pi < 1 else (Hinv(1 - a) * (kappa if pi == 1 else 1))
        cov2 += mass[(2, h)] / p * H(q / kappa)
        cov1 += mass[(1, h)] / (1 - p) * H(q)
    return float(cov2), float(cov1)


# --------------------------------------------------------------------------
# Proposition 2 / Remark: minimum group size and power
# --------------------------------------------------------------------------
N_MIN = math.ceil(1 / ALPHA) - 1


def conformal_k(n, a=ALPHA):
    return math.ceil((n + 1) * (1 - a) - 1e-12)


assert conformal_k(N_MIN) <= N_MIN and conformal_k(N_MIN - 1) > N_MIN - 1


def binom_power(n: int, miss_true: float, a=ALPHA, level=0.05) -> float:
    """Power of the exact two-sided binomial test of miss rate a."""
    ks = np.arange(n + 1)
    pv = np.array([stats.binomtest(int(k), n, a).pvalue for k in ks])
    rej = pv <= level
    return float(stats.binom.pmf(ks[rej], n, miss_true).sum())


# --------------------------------------------------------------------------
# Monte Carlo
# --------------------------------------------------------------------------
def cq(scores, a=ALPHA):
    n = len(scores)
    k = conformal_k(n, a)
    if k > n:
        return np.inf
    return np.partition(scores, k - 1)[k - 1]


def mc_iid(kappa, p, n, reps=40000):
    """i.i.d. mixture: marginal split conformal vs Mondrian on the true label."""
    hit_m = {1: [], 2: []}
    hit_g = {1: [], 2: []}
    hit_gb = {1: [], 2: []}  # Mondrian hits among bounded intervals only
    unbounded = 0
    for _ in range(reps):
        g = np.where(rng.random(n + 1) < p, 2, 1)
        s = np.where(g == 2, kappa, 1.0)
        r = np.abs(s * rng.standard_normal(n + 1))
        cal_r, cal_g, rt, gt = r[:n], g[:n], r[n], g[n]
        hit_m[gt].append(rt <= cq(cal_r))
        qg = cq(cal_r[cal_g == gt])
        unbounded += np.isinf(qg)
        hit_g[gt].append(rt <= qg)
        if np.isfinite(qg):
            hit_gb[gt].append(rt <= qg)
    m = {f"marg_c{g}": float(np.mean(v)) for g, v in hit_m.items()}
    m |= {f"mondrian_c{g}": float(np.mean(v)) for g, v in hit_g.items()}
    m |= {f"mondrian_bounded_c{g}": float(np.mean(v)) for g, v in hit_gb.items()}
    m["marg_all"] = float(np.mean(hit_m[1] + hit_m[2]))
    m["mondrian_unbounded_share"] = unbounded / reps
    return m


def mc_markov(kappa, p, persist, T=6000, W=36, burn=200):
    """Stationary Markov-switching regime with expected regime-2 spell length
    1/(1-persist); rolling-window split conformal (the illustration's design).
    The process is strictly stationary, yet regime-2 coverage falls short."""
    # transition probs with stationary P(G=2) = p and P(2->2) = persist
    p22 = persist
    p12 = p * (1 - p22) / (1 - p)
    g = np.empty(T, int)
    g[0] = 2 if rng.random() < p else 1
    u = rng.random(T)
    for t in range(1, T):
        g[t] = 2 if (u[t] < (p22 if g[t - 1] == 2 else p12)) else 1
    r = np.abs(np.where(g == 2, kappa, 1.0) * rng.standard_normal(T))
    hit, hit_rc, fb = [], [], []
    for t in range(burn, T):
        win_r, win_g = r[t - W:t], g[t - W:t]
        hit.append((g[t], r[t] <= cq(win_r)))
        same = win_r[win_g == g[t]]
        if len(same) < N_MIN:
            q = cq(win_r); fb.append(1)
        else:
            q = cq(same); fb.append(0)
        hit_rc.append((g[t], r[t] <= q))
    hit, hit_rc = np.array(hit), np.array(hit_rc)
    out = {}
    for name, h in (("rolling", hit), ("rc", hit_rc)):
        for gg in (1, 2):
            out[f"{name}_c{gg}"] = float(h[h[:, 0] == gg, 1].mean())
    out["rc_fallback_share_regime2"] = float(np.mean(np.array(fb)[hit[:, 0] == 2]))
    return out


# --------------------------------------------------------------------------
# Calibration to the Indian illustration
# --------------------------------------------------------------------------
def india_calibration():
    ser = pd.read_csv(ILL / "data_inflation_series.csv")
    ser.index = pd.PeriodIndex(ser.month, freq="M")
    F = ser.food_yoy_spliced
    dF = (F - F.shift(3)).dropna()
    shock = {}
    for t in ser.index:
        past = dF[dF.index <= t - 1]
        if len(past) < 12:
            continue
        shock[t] = int(past.iloc[-1] > np.quantile(past.values, 0.80))
    shock = pd.Series(shock)

    paths = pd.read_csv(ILL / "interval_paths.csv")
    paths.index = pd.PeriodIndex(paths.month, freq="M")
    rows = []
    for fc in ("AR", "EN"):
        d = paths[(paths.target == "headline") & (paths.forecaster == fc) & (paths.method == "SCP W=36")].copy()
        d["e"] = d.y - d.yhat
        d["shock"] = shock.reindex(d.index).values
        d["R2"] = (d.index >= pd.Period("2020-03", "M")) & (d.index <= pd.Period("2021-12", "M"))
        d["cover"] = (d.y >= d.lo) & (d.y <= d.hi)
        for part, mask in (("Food shock", d.shock == 1), ("COVID R2", d.R2)):
            bad, good = d.e[mask], d.e[~mask]
            # scale ratios: s.d. and normal-consistent mean absolute error (robust to the mean)
            k_sd = bad.std(ddof=1) / good.std(ddof=1)
            k_mae = np.abs(bad).mean() / np.abs(good).mean()
            # bootstrap CI for the s.d. ratio
            bs = []
            for _ in range(4000):
                b = rng.choice(bad.values, len(bad)); gq = rng.choice(good.values, len(good))
                bs.append(b.std(ddof=1) / gq.std(ddof=1))
            lo, hi = np.percentile(bs, [5, 95])
            p = mask.mean()
            pred_c2 = regime_cov(max(k_sd, 1.0001), p)[1] if k_sd > 1 else regime_cov(1 / k_sd, 1 - p)[0]
            rows.append(dict(forecaster=fc, regime=part, n_bad=int(mask.sum()), p=round(p, 3),
                             kappa_sd=round(k_sd, 3), kappa_sd_90ci=f"[{lo:.2f}, {hi:.2f}]",
                             kappa_mae=round(k_mae, 3),
                             predicted_cov_bad=round(pred_c2, 3),
                             observed_SCP_cov_bad=round(d.cover[mask].mean(), 3),
                             misses_bad=int((~d.cover[mask]).sum())))
    # how persistent is the shock state? (spell lengths, evaluation sample)
    s_eval = shock[(shock.index >= pd.Period("2017-01", "M")) & (shock.index <= pd.Period("2026-09", "M"))]
    spells = (s_eval.diff().fillna(s_eval.iloc[0]) == 1).sum()
    return pd.DataFrame(rows), dict(shock_months=int(s_eval.sum()), shock_spells=int(spells),
                                    mean_spell=round(s_eval.sum() / max(spells, 1), 2))


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------
log(f"alpha = {ALPHA}; minimum group calibration size for a bounded interval: n_G >= {N_MIN}")

# Prop 1 grid
grid = []
for p in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
    for kappa in (1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0):
        c1, c2 = regime_cov(kappa, p)
        grid.append(dict(p=p, kappa=kappa, cov_regime1=round(c1, 4), cov_regime2=round(c2, 4),
                         limit_kappa_inf=round(c2_limit(p), 4)))
grid = pd.DataFrame(grid)
grid.to_csv(OUT / "prop1_grid.csv", index=False)
log("\nProposition 1: regime-2 coverage under marginal calibration (rows p, cols kappa)")
log(grid.pivot(index="p", columns="kappa", values="cov_regime2").round(3).to_string())
for p in (0.05, 0.10, 0.2):
    log(f"  limit as kappa -> inf, p = {p}: {c2_limit(p):.3f}; kappa = 1000 numeric: {regime_cov(1000, p)[1]:.3f}")

# Prop 3 misclassification
mis = []
for kappa in (2.0, 3.0):
    for e in (0.0, 0.05, 0.10, 0.20, 0.30):
        c2, c1 = misclass_cov(kappa, 0.2, e_fn=e, e_fp=e * 0.2 / 0.8)
        lb = misclass_bound(kappa, 0.2, e, e * 0.2 / 0.8)
        assert c2 >= lb - 1e-9
        mis.append(dict(kappa=kappa, p=0.2, e_fn=e, e_fp=round(e * 0.25, 4), cov_regime2=round(c2, 4),
                        lower_bound=round(lb, 4), cov_regime1=round(c1, 4)))
mis = pd.DataFrame(mis)
mis.to_csv(OUT / "prop3_misclassification.csv", index=False)
log("\nProposition 3: coverage of true regime 2 when calibrating on a noisy label (p = 0.2)")
log(mis.to_string(index=False))

# Power
pw = []
for c2 in (0.70, 0.80, 0.85):
    for n in (9, 12, 18, 24, 36, 48, 72, 100, 150, 200):
        pw.append(dict(true_cov=c2, n=n, power=round(binom_power(n, 1 - c2), 3)))
pw = pd.DataFrame(pw)
pw.to_csv(OUT / "power_binomial.csv", index=False)
log("\nPower of the exact binomial (Kupiec) test at 5%, H0 miss rate 0.10")
log(pw.pivot(index="n", columns="true_cov", values="power").to_string())
nmin80 = {}
for c2 in (0.70, 0.80, 0.85):
    n = next(n for n in range(5, 2000) if binom_power(n, 1 - c2) >= 0.8)
    nmin80[c2] = n
log(f"  smallest n with power >= 0.80: {nmin80}")

# MC
log("\nMonte Carlo, i.i.d. mixture (40,000 reps each)")
mc_rows = []
for kappa, p, n in ((2.0, 0.2, 36), (3.0, 0.2, 36), (3.0, 0.08, 36), (3.0, 0.2, 120)):
    r = mc_iid(kappa, p, n)
    th = regime_cov(kappa, p)
    r |= dict(kappa=kappa, p=p, n=n, theory_c1=round(th[0], 4), theory_c2=round(th[1], 4),
              p_group_below_nmin=round(float(stats.binom.cdf(N_MIN - 1, n, p)), 4))
    mc_rows.append(r)
mc = pd.DataFrame(mc_rows)
mc.to_csv(OUT / "mc_iid.csv", index=False)
log(mc.round(3).to_string(index=False))

log("\nMonte Carlo, stationary Markov-switching regime, rolling W = 36 (6,000 months each)")
mk_rows = []
for kappa, p, persist in ((2.0, 0.2, 0.0), (2.0, 0.2, 0.8), (3.0, 0.2, 0.8), (3.0, 0.2, 0.95)):
    r = mc_markov(kappa, p, persist)
    r |= dict(kappa=kappa, p=p, persist=persist, mean_spell=round(1 / (1 - persist), 1),
              theory_c2=round(regime_cov(kappa, p)[1], 4))
    mk_rows.append(r)
mk = pd.DataFrame(mk_rows)
mk.to_csv(OUT / "mc_markov.csv", index=False)
log(mk.round(3).to_string(index=False))

# India
ind, spell = india_calibration()
ind.to_csv(OUT / "india_calibration.csv", index=False)
log("\nCalibration to the Indian illustration (headline, SCP W = 36, 2017-01 to 2026-09)")
log(ind.to_string(index=False))
log(f"  food-shock state in evaluation sample: {spell}")

# Figure: regime-2 coverage vs kappa, plus power
plt.rcParams.update({"font.family": "sans-serif", "font.size": 8})
fig, ax = plt.subplots(1, 2, figsize=(174 / 25.4, 2.6))
ks = np.linspace(1, 6, 120)
for p, ls in ((0.05, ":"), (0.10, "-."), (0.20, "--"), (0.30, "-")):
    ax[0].plot(ks, [regime_cov(k, p)[1] if k > 1 else 1 - ALPHA for k in ks], ls, color="k", lw=1,
               label=f"p = {p:.2f}")
ax[0].axhline(1 - ALPHA, color="grey", lw=0.6)
for _, r in ind[ind.forecaster == "EN"].iterrows():
    if r.kappa_sd > 1:
        ax[0].plot(r.kappa_sd, r.observed_SCP_cov_bad, "o", ms=4, mfc="white", mec="k")
        ax[0].annotate(r.regime, (r.kappa_sd, r.observed_SCP_cov_bad), xytext=(4, -9),
                       textcoords="offset points", fontsize=7)
ax[0].set_xlabel(r"scale ratio $\kappa = s_2/s_1$")
ax[0].set_ylabel("coverage in high-volatility regime")
ax[0].set_ylim(0.3, 1.0)
ax[0].legend(frameon=False, fontsize=7, loc="lower left")
ax[0].set_title("(a) Marginal calibration, nominal 0.90", fontsize=8)
for c2, ls in ((0.70, "-"), (0.80, "--"), (0.85, ":")):
    d = pw[pw.true_cov == c2]
    ax[1].plot(d.n, d.power, ls, color="k", lw=1, marker=".", label=f"true coverage {c2:.2f}")
ax[1].axhline(0.8, color="grey", lw=0.6)
for n, lab in ((22, "R2"), (27, "shock")):
    ax[1].axvline(n, color="grey", lw=0.6, ls=":")
    ax[1].text(n + 2, 0.03, lab, fontsize=7)
ax[1].set_xlabel("observations in regime")
ax[1].set_ylabel("power (exact binomial, 5%)")
ax[1].set_title("(b) Detecting regime undercoverage", fontsize=8)
ax[1].legend(frameon=False, fontsize=7, loc="center right")
fig.tight_layout()
fig.savefig(OUT / "fig_regime_coverage.pdf")
fig.savefig(OUT / "fig_regime_coverage.png", dpi=200)

(OUT / "run_log.txt").write_text("\n".join(LOG), encoding="utf-8")
json.dump(dict(alpha=ALPHA, n_min=N_MIN, n_for_80pct_power=nmin80, shock_spells=spell),
          open(OUT / "summary.json", "w"), indent=2)
