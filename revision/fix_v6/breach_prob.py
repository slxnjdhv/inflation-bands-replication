"""Probability of a statutory 'failure' (three consecutive quarters below 2%) implied by RBI fan charts.
Marginal P(X_q < 2) from a normal fitted by least squares to the lower band edges
(quantiles 0.05/0.15/0.25) of each quarter; joint probability bounded by independence
(product) and comonotonicity (minimum, the Frechet upper bound). Positively dependent
forecast errors put the truth between the two. Reads revision/fanchart/bands.csv."""
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm
b = pd.read_csv(Path(__file__).resolve().parents[1] / "fanchart/bands.csv")
Q = {50: 0.25, 70: 0.15, 90: 0.05}
def p_below(issue, tq, thr=2.0):
    s = b[(b.issue == issue) & (b.target_quarter == tq)]
    z = np.array([norm.ppf(Q[l]) for l in s.band_level]); x = s.lower.values
    slope, icpt = np.polyfit(z, x, 1)          # x = mu + sigma*z on the lower side
    return norm.cdf((thr - icpt) / slope), icpt, slope
rows = []
for issue, qs in [("2024 Oct", ["2025Q3", "2025Q4", "2026Q1"]), ("2024 Oct", ["2025Q2", "2025Q3", "2025Q4"]),
                  ("2025 Oct", ["2025Q4", "2026Q1"])]:
    ps = [p_below(issue, q)[0] for q in qs]
    rows.append(dict(issue=issue, quarters="+".join(qs), marginals=", ".join(f"{p:.3f}" for p in ps),
                     joint_indep=np.prod(ps), joint_comonotone=min(ps)))
r = pd.DataFrame(rows); print(r.round(4).to_string())
r.to_csv(Path(__file__).with_name("breach_prob.csv"), index=False)
