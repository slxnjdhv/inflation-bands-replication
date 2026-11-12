"""Holm-adjusted coverage p-values and DQ tests on the food-shock label (fix round v5).
Reads illustration/output (read-only); prints results."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
ROOT = Path(__file__).resolve().parents[2]
d = pd.read_csv(ROOT/"illustration/output/interval_paths.csv")
s = pd.read_csv(ROOT/"illustration/output/data_inflation_series.csv")
s.index = pd.PeriodIndex(s.month, freq="M")
F = s.food_yoy_spliced; dF = (F - F.shift(3)).dropna()
shock = {}
for m in s.index:
    past = dF[dF.index <= m - 1]
    if len(past) >= 12:
        shock[str(m)] = int(past.iloc[-1] > np.quantile(past.values, 0.80))
d = d[d.target == "headline"].copy()
d["shock"] = d.month.map(shock)
d["miss"] = ((d.y < d.lo) | (d.y > d.hi)).astype(int)
mp = pd.PeriodIndex(d.month, freq="M")
reg = np.select([mp <= pd.Period("2020-02","M"), mp <= pd.Period("2021-12","M"), mp <= pd.Period("2025-12","M")], ["R1","R2","R3"], "R4")
d["reg"] = reg
def binp(k, n): return stats.binomtest(k, n, 0.10).pvalue
def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for i, j in enumerate(o):
        run = max(run, min(1, (m - i) * p[j])); adj[j] = run
    return adj
rows = []
for (f, me), g in d.groupby(["forecaster", "method"]):
    cells = {"All": g, **{r: g[g.reg == r] for r in ["R1","R2","R3","R4"]}, "Shock": g[g.shock == 1], "Normal": g[g.shock == 0]}
    for c, gg in cells.items():
        rows.append(dict(forecaster=f, method=me, cell=c, n=len(gg), miss=gg.miss.sum(), p=binp(int(gg.miss.sum()), len(gg))))
r = pd.DataFrame(rows)
r["holm_row"] = r.groupby(["forecaster","method"]).p.transform(lambda x: holm(x.values))
r["holm_all"] = holm(r.p.values)
print(sorted(d.method.unique()))
print(r[r.p < 0.1].round(4).to_string())
print("n tests:", len(r))
# DQ test: miss_t - 0.1 on const, miss_{t-1}, shock_t ; Wald ~ chi2(3)
out = []
for (f, me), g in d.groupby(["forecaster", "method"]):
    g = g.sort_values("month"); h = g.miss.values - 0.10
    X = np.column_stack([np.ones(len(g)-1), g.miss.values[:-1], g.shock.values[1:]]); y = h[1:]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    dq = b @ X.T @ X @ b / (0.10*0.90)
    out.append(dict(forecaster=f, method=me, DQ=dq, p=stats.chi2.sf(dq, 3), b_shock=b[2]))
print(pd.DataFrame(out).round(3).to_string())
r.to_csv(Path(__file__).with_name("holm_cells.csv"), index=False)
pd.DataFrame(out).to_csv(Path(__file__).with_name("dq_tests.csv"), index=False)
