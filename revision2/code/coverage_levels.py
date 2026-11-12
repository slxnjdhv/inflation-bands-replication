"""Compact coverage / width / interval-score table by nominal level and regime (headline target).
Input: revision2/output/results_all_levels.csv.  Output: revision2/output/coverage_by_level.csv (+ printout).
Run: python -I revision2/code/coverage_levels.py
"""
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "output"
R = pd.read_csv(OUT / "results_all_levels.csv")
R = R[(R.target == "headline") & R.nominal.notna()]
R["nominal"] = R.nominal.round(2)
M = ["Gaussian", "EB-Gauss W=36", "SCP W=36", "ACI g=0.005 W=36", "ACI g=0.02 W=36", "RC-SCP W=36",
     "EB-Gauss W=60", "SCP W=60", "ACI g=0.005 W=60", "ACI g=0.02 W=60", "RC-SCP W=60"]
rows = []
for fc in ("AR", "EN"):
    for nom in (0.9, 0.7, 0.5):
        for m in M:
            s = R[(R.forecaster == fc) & (R.nominal == nom) & (R.method == m)].set_index("regime")
            r = dict(forecaster=fc, nominal=nom, method=m)
            for g in ("All", "R1", "R2", "R3", "R4"):
                r[f"cov_{g}"] = s.loc[g, "coverage"]; r[f"miss_{g}"] = int(s.loc[g, "misses"])
                r[f"IS_{g}"] = s.loc[g, "IS"]
                r[f"kupiec_p_{g}"] = s.loc[g, "kupiec_exact_p"]
            r["width"] = s.loc["All", "width"]; r["LR_cc_p"] = s.loc["All", "LR_cc_p"]
            rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(OUT / "coverage_by_level.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
cols = ["forecaster", "nominal", "method", "cov_All", "cov_R1", "cov_R2", "cov_R3", "cov_R4", "width", "IS_All", "IS_R2",
        "kupiec_p_All", "kupiec_p_R2", "LR_cc_p"]
print(T[cols].round(3).to_string(index=False))
