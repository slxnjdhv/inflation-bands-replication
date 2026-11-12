# Results: empirical illustration (generated 2026-11-03)

All numbers come from `run_illustration.py`; see `results_all.csv` and `run_log.txt`.
Nominal coverage is 0.90. "miss" is the number of outcomes outside the interval.
p is the exact two-sided binomial p-value against a miss rate of 0.10.

## Data actually used

- MoSPI API, All-India Combined:
  - CPI General and CFPI on base 2012=100, January 2013 to December 2025.
  - CPI General on base 2024=100, January 2025 to September 2026.
  - New-base Food group (COICOP 01.1) y-o-y, January to September 2026.
- Headline y-o-y inflation runs from 2014-01 to 2026-09 (n = 153).
- The evaluation runs from 2017-01 to 2026-09 (n = 117) for headline and from 2017-01 to
  2025-12 (n = 108) for food (CFPI).
- Linking factor 0.5267: the direction (linked = old × LF) was verified in the MoSPI FAQ Q37,
  and the factor itself was reproduced from the 2025 geometric means (0.5267). The official
  back series equals old × 0.5267 to within 0.05 index points.
- The first base-2024 month is **January 2026**, so R4 = 2026-01 to 2026-09 (n = 9) and
  R3 = 2022-01 to 2025-12 (n = 48).
- Rainfall was not used, because no public monthly all-India series covering 2013–2026 was found.
  The food-shock indicator is built from lagged food inflation. 27 of the 117 headline
  evaluation months are shock months.

## Point accuracy (RMSE, percentage points, headline, 2017-01 to 2026-09)

| | All | R1 | R2 | R3 | R4 |
|---|---|---|---|---|---|
| AR(BIC) | 0.755 | 0.610 | 1.044 | 0.740 | 0.500 |
| Elastic net | 0.758 | 0.659 | 0.991 | 0.757 | 0.433 |

The elastic net does not beat the AR overall. For food (CFPI, to 2025-12), the RMSE is
1.741 for AR and 1.721 for the elastic net.

## Headline coverage, W = 36 (`table_coverage.tex`)

| Forecaster | Interval | All (117) | R1 (38) | R2 (22) | R3 (48) | R4 (9) | Shock (27) | Normal (90) | Width | IS | LR_cc p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AR | Gaussian | 0.846 (18) | 0.868 (5) | **0.727 (6), p=0.018** | 0.875 (6) | 0.889 (1) | 0.889 | 0.833 | 2.07 | 3.54 | 0.138 |
| AR | Split conformal | 0.915 (10) | 0.895 (4) | 0.818 (4) | 0.958 (2) | 1.000 (0) | 0.926 | 0.911 | 2.84 | 3.72 | 0.855 |
| AR | ACI γ=0.005 | 0.915 (10) | 0.895 | 0.818 | 0.958 | 1.000 | 0.926 | 0.911 | 2.85 | 3.72 | 0.855 |
| AR | ACI γ=0.02 | 0.923 (9) | 0.895 | 0.864 | 0.958 | 1.000 | 0.926 | 0.922 | 2.80 | 3.66 | 0.323 |
| AR | Regime-cond. SCP | 0.915 (10) | 0.895 | 0.818 | 0.958 | 1.000 | 0.889 | 0.922 | 2.84 | 3.67 | 0.855 |
| EN | Gaussian | **0.838 (19), p=0.030** | 0.868 (5) | **0.682 (7), p=0.004** | 0.875 (6) | 0.889 (1) | 0.815 | 0.844 | 2.04 | 3.34 | **0.037** |
| EN | Split conformal | 0.932 (8) | 0.947 (2) | 0.818 (4) | 0.958 (2) | 1.000 (0) | 0.963 | 0.922 | 2.79 | 3.41 | 0.289 |
| EN | ACI γ=0.005 | 0.923 (9) | 0.947 (2) | 0.818 (4) | 0.938 (3) | 1.000 (0) | 0.963 | 0.911 | 2.73 | 3.44 | 0.352 |
| EN | ACI γ=0.02 | 0.915 (10) | 0.921 (3) | 0.818 (4) | 0.938 (3) | 1.000 (0) | 0.926 | 0.911 | 2.75 | 3.46 | 0.372 |
| EN | Regime-cond. SCP | 0.915 (10) | 0.921 (3) | 0.909 (2) | 0.896 (5) | 1.000 (0) | 0.852 (4) | 0.933 | 2.87 | 3.47 | 0.372 |

Summary of the headline results:

- **Gaussian intervals under-cover.** Coverage is 0.84 to 0.85 overall and 0.68 to 0.73 in the
  COVID regime R2. Only the EN Gaussian interval rejects at 5 per cent overall: Kupiec exact
  p = 0.030 and Christoffersen LR_cc p = 0.037 (LR_uc p = 0.037, LR_ind p = 0.134).
  R2 rejects for both forecasters.
- **Conformal methods (W = 36) reach 0.91 to 0.93 overall.** None rejects in any regime.
  - R2 stays below nominal at 0.82, or 0.86 to 0.91 for ACI γ=0.02 (AR) and regime-conditional
    SCP (EN), with 2 to 4 misses out of 22.
  - Coverage is above nominal in R3 (0.90 to 0.96) and R4 (9 of 9).
- **ACI changes little relative to split conformal.** The rolling window already adapts; ACI
  intervals were never capped or empty.
- **Regime-conditional SCP** fell back to pooled residuals in 7 of the 117 months (6.0%), all of
  them shock months (7 of 27). For EN it raises R2 coverage from 0.82 to 0.91 but lowers
  shock-month coverage to 0.85 (4 misses out of 27). The differences amount to one to three
  misses, well within sampling noise.
- **Coverage gains cost width.** Conformal intervals are 34 to 41 per cent wider than the
  Gaussian ones (about 2.75 to 2.87 pp against 2.04 to 2.07). The Gaussian intervals have the
  *lowest* mean interval score for both forecasters (EN 3.34 against 3.41 to 3.47; AR 3.54
  against 3.66 to 3.72). The score does not reward the extra coverage in this sample.
- **Robustness with W = 60** (`table_coverage_W60.tex`): overall coverage is 0.90 to 0.93 and
  R2 is 0.77 to 0.91, with the same qualitative picture. EN split conformal has width 2.73 and
  IS 3.34.
- **Excluding the four imputed months** (April–May 2020 and April–May 2021, n = 113): EN Gaussian
  coverage is 0.850 and EN split conformal 0.947. For AR the figures are 0.876 and 0.938.

## Food (CFPI) target, W = 36, 2017-01 to 2025-12 (`table_coverage_food.tex`)

- Gaussian coverage is 0.852 for AR (16 misses, p = 0.107) and 0.833 for EN (18 misses,
  p = 0.035). In R2 it is 0.773 for AR (p = 0.062) and 0.682 for EN (p = 0.004).
- Split conformal and ACI reach 0.90 to 0.91 overall, with R2 at 0.77 to 0.91.
- Regime-conditional SCP gives 0.88 (AR; R2 0.73, which rejects) and 0.94 (EN).
- Widths are 4.5 pp (Gaussian) and 5.8 to 7.4 pp (conformal).

---

## Draft manuscript text (LaTeX)

```latex
\subsection*{An empirical illustration}

To illustrate how the coverage of standard intervals behaves across Indian regimes, we
forecast all-India combined CPI inflation (year on year) one month ahead. The data are the
MoSPI indices on base 2012$=$100 from January 2013 to December 2025 and on base 2024$=$100 from
January 2025 to September 2026. Headline inflation before 2026 is computed from the old indices.
From January 2026 we use the official new-basket rate, which compares two indices on the new
base. The linking factor of 0.5267 (linked $=$ old $\times$ factor) reproduces both the
official back series and the 2025 geometric-mean ratio \citep{mospi2026faq}. Because it is a
constant multiplier, it leaves pre-2026 inflation rates unchanged. The Consumer Food Price
Index (CFPI) is used on the 2012 base only. Two point forecasters are re-estimated every month
on an expanding window: an autoregression with lag order chosen by BIC, and an elastic net
[Zou and Hastie, 2005] on twelve lags of headline and food inflation. Each forecaster is paired
with five nominal 90 per cent intervals:
(i) a Gaussian interval based on the in-sample residual standard deviation;
(ii) rolling split conformal intervals from the absolute out-of-sample residuals of the
previous 36 months \citep{lei2018distribution};
(iii) adaptive conformal inference with $\gamma\in\{0.005,0.02\}$ \citep{gibbs2021adaptive};
(iv) a group-conditional split conformal interval that calibrates only on past months in the
same state of an observable food-shock indicator, in the spirit of \citet{gibbs2025conformal}.
A month is a food-shock month if the three-month change in food inflation, known at the
forecast origin, exceeds its expanding-window 80th percentile. Intervals are evaluated from
January 2017 to September 2026 ($n=117$). The evaluation window is split into the
pre-COVID inflation-targeting period (R1, $n=38$), COVID-19 (R2, March 2020 to December 2021,
$n=22$), the post-COVID period to December 2025 (R3, $n=48$) and the new-base window
(R4, January to September 2026, $n=9$).

The results are summarised in Table~X and Figure~Y. Point accuracy is almost identical across
the two forecasters: the root mean squared error is 0.76 percentage points for the
autoregression and for the elastic net, so the elastic net does not beat the autoregressive
benchmark \citep{choudhary2026core}. The Gaussian intervals under-cover, at 0.85 (autoregression)
and 0.84 (elastic net) overall. In the COVID-19 regime their coverage falls to 0.73 and 0.68,
which an exact binomial test rejects in both cases ($p=0.018$ and $p=0.004$) \citep{kupiec1995}.
For the elastic net the Christoffersen conditional-coverage test also rejects over the full
sample ($p=0.037$) \citep{christoffersen1998}. The conformal intervals bring overall coverage to
0.91--0.93, and no regime-level test rejects. Coverage in R2 nevertheless remains below nominal
(0.82 for split conformal and ACI), while R3 and R4 are over-covered (0.90--0.96 and nine of
nine). ACI adds little to a rolling 36-month calibration window. The regime-conditional variant
raises R2 coverage for the elastic net to 0.91 but lowers coverage in food-shock months to 0.85.
Its calibration set fell back to the pooled residuals in 7 of 117 months. Better coverage is
paid for in width: the conformal intervals are about 35--40 per cent wider. The Gaussian
intervals in fact achieve the lowest mean interval score \citep{gneiting2007scoring}, because
the penalty on their additional misses does not outweigh the width they save in calm periods.
Results with a 60-month calibration window and for food inflation are qualitatively similar.

The illustration is deliberately modest, and its limitations are those listed in
Section~\ref{subsec:threats}. The regimes are short: at the 90 per cent level, R2 and R4 contain
about two and one expected misses, so the regime-level tests have little power, and differences
of one to three misses between methods should not be read as rankings. The data are the current
vintage, and the release lag of about two weeks is ignored. The all-India indices for April and
May 2020 were imputed \citep{mospi2020covid}, which also affects inflation in April and May 2021;
excluding these four months raises all coverage rates slightly but leaves the ranking unchanged.
The 2026 observations combine an old-basket history with a new-basket target, and the food
predictor used in 2026 splices the CFPI with the new-base food group, for which no official
linking factor exists \citep{mospi2026faq}. No suitable public monthly rainfall series was
available, so the shock indicator relies on lagged food prices rather than weather. The exercise
therefore shows the kind of regime-level evidence the reporting standards above call for; it is
not a horse race between interval methods.
```

Notes on the draft text:
- There is no `zou2005` key in `references.bib`, so the elastic-net citation is written as
  "[Zou and Hastie, 2005]". Add the bib entry if desired.
- The keys used all exist in `references.bib`: `mospi2026faq`, `lei2018distribution`,
  `gibbs2021adaptive`, `gibbs2025conformal`, `kupiec1995`, `christoffersen1998`,
  `gneiting2007scoring`, `choudhary2026core` and `mospi2020covid`.
- Asterisks in the `.tex` tables mark an exact binomial p < 0.05 for that cell. Suggested
  caption note: "Coverage with $^{*}$: exact two-sided binomial test of a 10 per cent miss rate
  rejects at 5 per cent. Width and IS (interval score) are means in percentage points.
  $p_{\mathrm{cc}}$: Christoffersen conditional-coverage test."
