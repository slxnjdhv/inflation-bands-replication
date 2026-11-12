"""Build table_horizons.tex (label tab:horizons) from output/results_horizons.csv."""
from pathlib import Path
import pandas as pd
H = Path(__file__).resolve().parent
r = pd.read_csv(H / "output" / "results_horizons.csv")
ORDER = ["Gaussian", "Gaussian, OOS errors", "Split conformal", "Regime-cond. SCP"]
LAB = {"Gaussian": "Gaussian, in-sample", "Gaussian, OOS errors": "Gaussian, OOS errors",
       "Split conformal": "Split conformal", "Regime-cond. SCP": "Regime-cond.\\ SCP"}
FC = {"AR": "Autoregression", "EN": "Elastic net"}
L = [r"\begin{table}[htbp]",
     r"\caption{Coverage of nominal 90 per cent intervals at horizons of three and six months, headline CPI inflation, April 2018 to September 2026 ($n=102$)}\label{tab:horizons}",
     r"\footnotesize", r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{@{}lcccccc@{}}", r"\toprule",
     r"Interval & All & R2 & R3 & Width & IS & $p$ \\", r"\midrule"]
for h in (3, 6):
    for fc in ("AR", "EN"):
        rm = r[(r.h == h) & (r.forecaster == fc)].rmse.iloc[0]
        L.append(r"\multicolumn{7}{@{}l}{\emph{%s, %d months ahead (RMSE %.2f)}}\\" % (FC[fc], h, rm))
        for m in ORDER:
            s = r[(r.h == h) & (r.forecaster == fc) & (r.method == m)].set_index("cell")
            def cov(c):
                v = f"{s.loc[c, 'coverage']:.2f}"
                return v + ("$^{*}$" if s.loc[c, "p_exact"] < 0.05 else "")
            L.append(f"{LAB[m]} & {cov('All')} & {cov('R2')} & {cov('R3')} & {s.loc['All', 'width']:.2f} & "
                     f"{s.loc['All', 'IS']:.2f} & {s.loc['All', 'p_exact']:.3f} \\\\")
        if not (h == 6 and fc == "EN"):
            L.append(r"\addlinespace")
L += [r"\botrule", r"\end{tabular}",
      r"\footnotetext{Direct $h$-step forecasts from lags $h$ to $h+11$ of headline and food inflation, re-estimated monthly on targets observed at the forecast origin. Intervals: Gaussian with the in-sample residual standard deviation; Gaussian with the root mean squared error of the previous 36 out-of-sample errors observable at the origin; rolling split conformal (SCP) on the same errors; and SCP calibrated within the food-shock state at the origin. The common sample starts in April 2018, the first month in which every horizon has at least 12 observed errors; R2 (March 2020 to December 2021) has $n=22$, R3 (January 2022 to December 2025) $n=48$. Width and IS (mean interval score) in percentage points; $p$, exact two-sided binomial test of a 10 per cent miss rate over the full sample. Consecutive multi-step errors overlap, so the $p$-values are optimistic.}",
      r"\footnotetext{$^{*}$Exact binomial test rejects at the 5 per cent level (unadjusted).}",
      r"\footnotetext{Source: own calculations from MoSPI CPI data.}", r"\end{table}"]
(H / "table_horizons.tex").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
