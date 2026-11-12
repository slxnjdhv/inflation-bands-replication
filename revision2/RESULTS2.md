# Revision 2: error-based baseline, DM tests, window comparison, Proposition 1 gap, fan-chart centring, figures

All numbers below come from the scripts in `revision2/code/`, run on 2026-11-04. Nothing outside `revision2/` was changed.

## Files

| File | Content |
|---|---|
| `code/run_illustration2.py` | Copy of `illustration/code/run_illustration.py`, extended to nominal 50/70/90 % and with the new out-of-sample error-based Gaussian baseline. It checks itself against the original `results_all.csv`: 270 rows and 1,620 values, max abs. diff 5.0e-5, which is the 4-dp rounding of the stored file. The existing methods' 90 % results are therefore unchanged. Runtime about 5 min. |
| `code/dm_tests.py` | Diebold–Mariano tests, window comparison, Proposition 1 numbers, `table_baseline_dm.tex/.csv` |
| `code/coverage_levels.py` | Compact coverage / width / IS by level and regime |
| `code/fanchart_centring.py` | Centring bias, sign tests and width diagnostics for the RBI fan charts |
| `code/fig1.py`, `code/fig2.py`, `code/check_fonts.py` | Figures and the font-size check |
| `output/results_all_levels.csv`, `output/interval_paths_levels.csv` | All methods × levels × regimes, and per-month paths with IS |
| `output/dm_tests.csv` | 750 DM tests: forecaster × level × W × pair × regime, HLN–NW and lag-0 variants |
| `output/window_comparison.csv`, `output/coverage_by_level.csv`, `output/prop1_numbers.txt` | Tables behind sections 2 and 3 |
| `output/fanchart_centring.csv`, `output/fanchart_obs_wide.csv` | Fan-chart diagnostics |
| `table_baseline_dm.tex/.csv` | Drop-in table (label `tab:baseline_dm`) |
| `Fig1.pdf/.png`, `Fig2.pdf/.png` | Figures at sn-jnl `\textwidth`, the recommended versions. PNGs are 600 dpi. |
| `Fig1_174mm.pdf/.png`, `Fig2_174mm.pdf/.png` | 6.85 in (174 mm) variants |

Run order (from the project root): `run_illustration2.py`, then `dm_tests.py`, `coverage_levels.py`, `fig1.py`, `fig2.py`, `fanchart_centring.py` and `check_fonts.py`.

## 1. New baseline: Gaussian interval from recent out-of-sample errors

The interval is the point forecast ± z × RMSE of the last W out-of-sample errors. These are exactly the errors that calibrate the rolling conformal intervals. Early in the sample, fewer than W errors are available, with a minimum of 12. This is the Reifschneider–Tulip / Clark–McCracken–Mertens-type band.

- I used the zero-mean RMSE as the primary scale, because the band is centred on the point forecast.
- A variant uses the demeaned SD (ddof=1). It is labelled `EB-Gauss-sd` in the CSVs and gives very similar results (see below).

**Headline, nominal 90 %, coverage (misses/n), width and IS (full sample):**

| | All | R1 | R2 | R3 | R4 | Width | IS |
|---|---|---|---|---|---|---|---|
| AR Gaussian, in-sample | 0.846 (18/117) | 0.868 | 0.727 (6/22) | 0.875 | 0.889 | 2.069 | 3.539 |
| AR Gaussian, OOS errors W=36 | 0.897 (12) | 0.895 | 0.773 (5) | 0.938 | 1.000 | 2.455 | 3.565 |
| AR Gaussian, OOS errors W=60 | 0.897 (12) | 0.895 | 0.773 (5) | 0.938 | 1.000 | 2.417 | 3.493 |
| AR split conformal W=36 | 0.915 (10) | 0.895 | 0.818 (4) | 0.958 | 1.000 | 2.844 | 3.719 |
| AR split conformal W=60 | 0.915 (10) | 0.895 | 0.773 (5) | 0.979 | 1.000 | 2.506 | 3.511 |
| EN Gaussian, in-sample | 0.838 (19) | 0.868 | 0.682 (7) | 0.875 | 0.889 | 2.036 | 3.337 |
| EN Gaussian, OOS errors W=36 | 0.906 (11) | 0.921 | 0.727 (6) | 0.958 | 1.000 | 2.632 | 3.412 |
| EN Gaussian, OOS errors W=60 | 0.932 (8) | 0.947 | 0.864 (3) | 0.938 | 1.000 | 2.649 | 3.266 |
| EN split conformal W=36 | 0.932 (8) | 0.947 | 0.818 (4) | 0.958 | 1.000 | 2.786 | 3.410 |
| EN split conformal W=60 | 0.932 (8) | 0.974 | 0.864 (3) | 0.917 | 1.000 | 2.734 | 3.338 |

- The demeaned-SD variant gives 0.897/0.897 overall for AR (IS 3.545/3.491) and 0.897/0.915 for EN (IS 3.385/3.251), at W=36/60.
- **EN with the OOS-error band at W=60 has the lowest 90 % interval score of any interval in the study (3.266; sd variant 3.251).**
- Exact binomial tests:
  - The OOS-error band rejects in R2 only for EN at W=36 (0.727, p = 0.018).
  - Overall, no test of the OOS-error band rejects (p ≥ 0.35).
  - LR_cc p-values: AR 0.297 at both W; EN 0.975 (W=36) and 0.289 (W=60).

**Other levels (full-sample coverage; the R2 figure is in brackets).** The table `output/coverage_by_level.csv` has every cell.

- 70 % nominal:
  - AR: in-sample Gaussian 0.692 [0.591], OOS-error W36 0.718 [0.636], SCP W36 0.701 [0.591].
  - EN: in-sample Gaussian **0.607 [0.318]** (exact p = 0.034 overall, p < 0.001 in R2), OOS-error W36 0.735 [0.409], SCP W36 0.752 [0.455].
  - At 70 %, every EN OOS-error and conformal interval also under-covers R2 (0.41–0.45, p = 0.005–0.018).
- 50 % nominal:
  - AR: Gaussian 0.513, OOS-error W36 0.590, SCP W36 0.530.
  - EN: 0.470, 0.556 and 0.573.
  - R2 coverage is 0.27–0.46 for all methods.
- **Interpretation.** In-sample versus out-of-sample error scale explains most of the Gaussian under-coverage at 90 %. Once the Gaussian band is scaled by recent out-of-sample errors, it covers 0.90–0.93 overall, as conformal does, and is narrower: 2.42–2.65 against 2.51–2.87. What remains for conformal is a small R2 gain at W=36: 0.82 against 0.73–0.77, which is one or two misses out of 22.

## 2. Diebold–Mariano tests on interval-score differentials

Setup:
- Loss differential: d_t = IS(row)_t − IS(benchmark)_t, so a negative value favours the row interval.
- Variance: Newey–West (Bartlett kernel) with L = floor(4(n/100)^{2/9}). That gives L = 4 for n = 117, 3 for R1 and R3, 2 for R2, and 1 for R4.
- The HLN factor is √((n−1)/n) for h = 1, and p-values come from t(n−1).
- The lag-0 version is also in the CSV (`DM_HLN_L0`, `p_L0`).

**Full sample, nominal 90 % (DM stat, p).** These are also in `table_baseline_dm.tex`.

| | vs in-sample Gaussian, W=36 | vs OOS-error Gaussian, W=36 | vs in-sample Gaussian, W=60 | vs OOS-error Gaussian, W=60 |
|---|---|---|---|---|
| AR SCP | 0.91 (0.37) | 1.47 (0.14) | −0.23 (0.82) | 0.52 (0.60) |
| AR ACI γ=.005 | 0.92 (0.36) | 1.50 (0.14) | 0.25 (0.80) | 1.27 (0.21) |
| AR ACI γ=.02 | 0.57 (0.57) | 0.72 (0.47) | 0.34 (0.73) | 1.07 (0.29) |
| AR RC-SCP | 0.65 (0.52) | 0.97 (0.33) | 0.46 (0.64) | 1.68 (0.10) |
| AR OOS-error Gaussian | 0.23 (0.81) | – | −0.44 (0.66) | – |
| EN SCP | 0.39 (0.70) | −0.03 (0.98) | 0.00 (1.00) | 1.53 (0.13) |
| EN ACI γ=.005 | 0.62 (0.53) | 0.50 (0.61) | −0.16 (0.87) | 0.92 (0.36) |
| EN ACI γ=.02 | 0.75 (0.46) | 0.74 (0.46) | −0.15 (0.88) | 1.09 (0.28) |
| EN RC-SCP | 0.59 (0.56) | 0.46 (0.65) | 0.01 (0.99) | 1.03 (0.31) |
| EN OOS-error Gaussian | 0.50 (0.61) | – | −0.40 (0.69) | – |

- **No full-sample 90 % difference between any interval methods is significant** (smallest p = 0.10, AR RC-SCP W=60 vs OOS-error Gaussian).
- **At 70 %**, the only full-sample rejections between methods are:
  - AR ACI γ=0.02 W36 is worse than the in-sample Gaussian (DM 2.00, p = 0.048).
  - EN RC-SCP W60 is worse than the OOS-error Gaussian W60 (DM 2.39, p = 0.019).
  - Given the 40 method comparisons at 70 % (20 per forecaster), two rejections at 5 % is about what chance alone produces.
- **R2 (n = 22, 90 %).** Every interval has a lower mean IS than the in-sample Gaussian, but none is significant:
  - AR: Gaussian 6.224; SCP W36 5.634 (DM −0.74, p = 0.47); OOS-error W60 5.848 (p = 0.19).
  - EN: Gaussian 4.812; SCP W36 4.266 (DM −1.83, p = 0.081); RC-SCP W36 3.999 (p = 0.14); OOS-error W60 4.162 (DM −1.92, p = 0.068).
- **R3 (n = 48, 90 %).** Conformal W=36 is significantly *worse* for AR:
  - SCP/ACI γ=0.005 have IS 3.870 against the in-sample Gaussian's 3.207 (DM 2.96, p = 0.005) and against the OOS-error Gaussian's 3.415 (DM 5.69, p < 0.001).
  - All 8 significant R3 tests at 90 % go against the conformal interval. This is the width cost in a calm regime.
- **R4 (n = 9, no conformal misses).** The differential is almost pure width, and several |DM| values are very large (up to 10.5). With n = 9, these should not be read as evidence.
- **Window comparison, W=60 vs W=36, same method, full sample, 90 %.** The longer window lowers IS in every case:
  - Significant for EN ACI γ=0.005 (3.307 vs 3.445; DM −2.81, p = 0.006), EN ACI γ=0.02 (3.311 vs 3.464; p = 0.016) and EN RC-SCP (3.339 vs 3.465; p = 0.027).
  - Not significant for EN SCP (3.338 vs 3.410, p = 0.092), AR SCP (3.511 vs 3.719, p = 0.13) or the EN OOS-error band (3.266 vs 3.412, p = 0.052).
  - At 70 %, W=60 is also significantly better for AR SCP and both ACI variants, and for EN SCP, both ACI variants and the OOS-error band (p = 0.010–0.022).

## 3. Window comparison: 36 vs 60 months, mean interval score, nominal 90 %, full sample

| | Gaussian, in-sample | W=36 | W=60 | W=60 below Gaussian? |
|---|---|---|---|---|
| AR SCP | 3.5387 | 3.7185 | **3.5108** | yes (−0.028) |
| AR ACI γ=0.005 | 3.5387 | 3.7220 | 3.5782 | no |
| AR ACI γ=0.02 | 3.5387 | 3.6604 | 3.6026 | no |
| AR RC-SCP | 3.5387 | 3.6689 | 3.5939 | no |
| AR OOS-error Gaussian | 3.5387 | 3.5655 | **3.4925** | yes |
| EN SCP | 3.3374 | 3.4097 | 3.3378 | tie (+0.0004) |
| EN ACI γ=0.005 | 3.3374 | 3.4449 | **3.3072** | yes |
| EN ACI γ=0.02 | 3.3374 | 3.4642 | **3.3111** | yes |
| EN RC-SCP | 3.3374 | 3.4653 | 3.3393 | no (+0.002) |
| EN OOS-error Gaussian | 3.3374 | 3.4115 | **3.2665** | yes |

- With W = 36, no interval beats the in-sample Gaussian IS.
- With W = 60, AR SCP and EN ACI (both γ) are lower, EN SCP ties, and the OOS-error Gaussian is lower for both forecasters.
- The differences against the Gaussian are all insignificant (section 2).
- Width premium over the in-sample Gaussian: 34–41 % at W=36 and **21–36 %** at W=60 (AR SCP 2.506 vs 2.069; EN RC-SCP 2.766 vs 2.036).
- At 70 % (W=60): AR SCP 2.375 and EN ACI γ=0.02 2.388 are below the Gaussian (2.384 and 2.411); the DM tests are insignificant.
- At 50 %, the in-sample Gaussian has the lowest IS for both forecasters at both windows.

## 4. Why the pandemic Gaussian coverage (0.68–0.73) can fall below the 0.727 "floor"

Source: `output/prop1_numbers.txt`.

1. **The bound is about pooled split-conformal calibration on correctly scaled errors, not about the Gaussian interval.** The Gaussian interval uses the *in-sample* residual SD.
   - In R2, that SD averages 0.634 (AR) and 0.604 (EN).
   - The out-of-sample R2 RMSE is 1.044 and 0.991, so the interval's scale is only **0.61 × s₂** for both forecasters.
   - In other months it is 0.94 × s₁ (AR) and 0.90 × s₁ (EN).
   - If errors were N(0, s_k²), the implied coverage is 2Φ(1.645 × 0.61) − 1 = **0.681** in R2 for both forecasters, and 0.871 (AR) and 0.853 (EN) elsewhere.
   - The observed values are 0.727/0.682 in R2 and 0.874/0.874 elsewhere.
   - Under-estimation of the error variance, which is a scale bias and not regime pooling, accounts for the observed R2 coverage almost exactly. The floor 2Φ(z s₁/s₂) − 1 assumes the interval is scaled to the pooled out-of-sample error distribution.
2. **The 0.727 floor uses the rounded ratio s₂/s₁ = 1.5.** The forecaster-specific ratios give different limits:
   - AR: ratio 1.557, p = 0.188, limit 0.760, floor 0.709. The observed 0.727 is above its own floor.
   - EN: ratio 1.429, limit 0.789, floor 0.750. The observed 0.682 is below it.
3. **These are n → ∞ limits, while R2 has 22 serially dependent months.**
   - The 95 % Clopper–Pearson intervals are [0.498, 0.893] (AR, 16/22) and [0.451, 0.861] (EN, 15/22).
   - If the true coverage were the limit, the probability of seeing as few covered months is 0.44 (AR, Bin(22, 0.760)) and 0.17 (EN, Bin(22, 0.789)).
   - The interval estimates of the ratio s₂/s₁ are themselves noisy.

The out-of-sample-error Gaussian band, which is close to the setting of Proposition 1(a), covers R2 at 0.773 (AR) and 0.727 (EN) at W=36. These values are close to the limits 0.760 and 0.789.

Suggested sentence for Section 4.2: "The Gaussian intervals of the illustration are not pooled conformal intervals. Their in-sample residual standard deviation is only about 0.61 times the out-of-sample root mean squared error in the COVID-19 regime, which by itself implies coverage of about 0.68 there, so their observed 0.68–0.73 reflects an under-estimated error scale more than regime pooling. A Gaussian band scaled by the previous 36 out-of-sample errors covers 0.73–0.77 in that regime, close to the limits of 0.76–0.79 implied by each forecaster's own scale ratio."

## 5. Fan charts: "close to nominal" re-examined

These results come from `fanchart_centring.py`, read against `revision/fanchart/coverage_results.csv`. The coverage counts were re-derived and match that file.

- **8 of 9 cells (h = 1, 2, 4 × 50/70/90) have point coverage at or above nominal**: 0.667, 0.778, 0.944; 0.588, 0.706, **0.882**; 0.625, 0.812, 0.938. The exception is h = 2 / 90 %. All p > 0.2.
- **Centring.** e = outturn − fan median, in pp; n excludes 4 bars with no extractable median (Oct 2016 ×3, Oct 2024 2025Q2). Each cell gives the mean error, the median error, and the count of outturns below/above the fan median.

| h | 2016Q4–2020Q1 | 2020Q2–2022Q4 | 2023Q1–2026Q3 |
|---|---|---|---|
| 1 | −0.23 / −0.44, 4 below 2 above (n=6) | +0.33 / +0.37, 2/3 (n=5) | +0.08 / +0.13, 3/3 (n=6) |
| 2 | −0.32 / −0.49, 3/2 (n=5) | **+1.53 / +1.29, 0/5** (n=5; sign p = 0.06) | +0.12 / −0.03, 3/2 (n=5) |
| 4 | −0.55 / −0.53, 2/2 (n=4) | **+1.96 / +2.47, 0/5** (n=5; sign p = 0.06) | −0.37 / +0.27, 2/4 (n=6) |

- **Size of errors relative to the band.** The ratio is mean |e| divided by the mean half-width of the 50 % band. It is about 1.18 for calibrated Gaussian bands; above that means bands too narrow or badly centred, below means generous.
  - h = 1: **1.31** (2017–19), 0.42 (2020–22), 0.53 (2023–26).
  - h = 2: 1.04, 1.02, 0.38.
  - h = 4: 0.87, 1.23, 0.85.
- **Coverage by period at h = 1** (50/70/90): 2/7, 3/7, 6/7 (2017–19); 5/5, 5/5, 5/5 (2020–22); 5/6, 6/6, 6/6 (2023–26).
- **Reading.**
  - In 2017–19, short-horizon errors were large relative to the band, and the misses were mostly below it (h = 1, 50 %: 4 below, 1 above).
  - In 2020–22, the bands were generous at h = 1, but at h = 2 and h = 4 every outturn lay above the fan median, by 1.5–2.0 pp on average. This is an upward centring error during the pandemic and post-pandemic inflation, which the wide bands largely absorbed: 4q coverage was 2/5, 3/5 and 5/5.
  - In 2023–26, the bands were well centred (|mean e| ≤ 0.37) and generous: errors were 0.38–0.85 of the 50 % half-width, and coverage at h = 1–2 was 5/6–6/6.
  - So the referee's "generous in 2020–26" holds at h = 1 throughout and in 2023–26 at all horizons, but not at h = 2–4 in 2020–22.
- All cells have n = 4–7, the observations overlap, and none of the sign tests rejects at 5 %.

## 6. Suggested replacement text

**(i) Abstract**, replacing "rolling conformal intervals cover 91 to 93 per cent but are 34 to 41 per cent wider without a lower interval score":

> rolling conformal intervals cover 91 to 93 per cent, as does a Gaussian band scaled by recent out-of-sample errors, and Diebold–Mariano tests find no significant difference in 90 per cent interval scores between any of the methods

This adds about 6 words. The abstract is at 248/250, so drop other text accordingly; for example, delete "and survey probability bins" or shorten the fan-chart clause in (ii).

A shorter alternative (−3 words relative to the original):

> rolling conformal intervals cover 91 to 93 per cent, with interval scores not significantly different from the Gaussian ones

**Results paragraph** (replaces the "Coverage is paid for in width…" paragraph and the W=60 sentence):

> Coverage is paid for in width, but the scoring evidence is inconclusive. With a 36-month window the conformal intervals are 34 to 41 per cent wider than the Gaussian ones and have slightly higher mean interval scores (3.41–3.47 against 3.34 for the elastic net, 3.66–3.72 against 3.54 for the AR); with a 60-month window they are 21 to 36 per cent wider and their scores are similar or lower (elastic net 3.31–3.34, AR 3.51–3.60). None of these differences is significant: Diebold–Mariano tests on the interval-score differentials (Newey–West variance, Harvey–Leybourne–Newbold correction) give $p\geq0.36$ over the full sample. The Gaussian under-coverage is largely a matter of scale rather than shape. A Gaussian interval scaled by the root mean squared error of the previous 36 or 60 out-of-sample errors, in the spirit of \citet{clark2020} and \citet{reifschneider2019gauging}, covers 0.90–0.93 overall, is narrower than the conformal intervals (2.42–2.65 percentage points) and is not significantly different from them in interval score (smallest $p=0.10$; Table~\ref{tab:baseline_dm}). With $W=60$ it attains the lowest interval score of the methods in Table~\ref{tab:baseline_dm} for both forecasters (3.27 elastic net, 3.49 AR). Within regimes, conformal and error-based intervals lower the interval score in R2 relative to the in-sample Gaussian interval, but insignificantly ($p=0.06$–$0.67$), while in R3 the 36-month AR split conformal and ACI intervals score significantly worse than both Gaussian benchmarks ($p\leq0.005$), the width cost in a calm regime.

Both keys (`reifschneider2019gauging`, `clark2020`) exist in references.bib.

**(ii) Fan-chart framing.** Abstract, replacing "finds coverage close to nominal, with low power and misses clustered in regime shifts":

> finds coverage not significantly different from nominal, with point estimates at or above nominal in 8 of 9 horizon–band cells, bands that were generous after 2020 at short horizons, and centring errors in 2017–19 and, at longer horizons, in 2020–22

Section 7.5, replacing the UK sentence:

> The pooled point estimates are therefore consistent with the UK finding that fan charts overstated uncertainty; the sub-periods qualify it. For targets from 2017Q1 to 2020Q1, outturns at the one-quarter horizon fell mostly below the fan median (median error $-0.44$ percentage points) and the 50 per cent band contained only 2 of 7 outturns. From 2020Q2 to 2022Q4 every outturn at the two- and four-quarter horizons lay above the median, by 1.5 and 2.0 percentage points on average, an error in the centre that the wide bands largely absorbed. From 2023 the bands were well centred and generous, with mean absolute errors of 0.4 to 0.5 times the half-width of the 50 per cent band at horizons of one and two quarters. With four to seven overlapping observations per cell, none of these patterns is statistically significant.

**(iii) Figure captions** (no colour words, no final punctuation)

Fig. 1:

> Indian headline CPI inflation (year on year, per cent) with one-month-ahead elastic-net 90 per cent intervals, January 2017 to September 2026. Dashed lines show Gaussian intervals, thin solid lines adaptive conformal inference intervals ($\gamma=0.005$, 36-month window) and the thick solid line actual inflation. Light and darker shading mark the COVID-19 regime (R2) and the new-base window (R4). Circles mark months with imputed indices, squares months whose year-on-year rate uses an imputed base. Source: own calculations from MoSPI CPI data

Fig. 2:

> RBI Monetary Policy Report fan-chart bands and CPI inflation outturns (a) one, (b) two and (c) four quarters after the publication quarter, by target quarter, for reports from October 2016 to October 2026. Vertical bars show the 50, 70 and 90 per cent bands, from darkest to lightest shading, and the short horizontal line across each bar marks the median of the fan. The solid line is quarterly average year-on-year CPI inflation; filled circles mark outturns inside the 70 per cent band, open circles outturns outside it, and bars without a circle have no outturn yet. Hatched areas mark target quarters affected by the 2020 CPI imputation, and the dotted vertical line marks the start of the 2024-base CPI in 2026. Source: own calculations from RBI Monetary Policy Reports and MoSPI CPI data

## 7. Figure size and lettering

- **The sn-jnl `\textwidth` is not 6.3–6.9 in.** With the default single-column option used by main.tex (`\documentclass[pdflatex,sn-apa]{sn-jnl}`), sn-jnl.cls sets `text={31pc,194.25mm}`, so `\textwidth` = 31 pc = 372 TeX pt = **5.15 in = 130.7 mm**. The 160 mm text block applies only to the twocolumn option.
- The old 174 mm figures were therefore shrunk ×0.75 by `width=\textwidth`, to 6.0 pt (Fig. 1) and 5.3–6.0 pt (Fig. 2), as `final_review/03_compliance_layout.md` #37 found.
- `Fig1.pdf` and `Fig2.pdf` are drawn at exactly 130.7 mm wide, so the existing `\includegraphics[width=\textwidth]{Fig1.pdf}` is a 1:1 inclusion.
- `check_fonts.py` finds a single font (ArialMT) at a single size, **9.0 pt**, in both files.
  - Fig. 1 is 130.7 × 81.1 mm; Fig. 2 is 130.7 × 146.4 mm.
  - If Springer sets them at 174 mm, the lettering becomes 11.98 pt; at 119 mm it becomes 8.2 pt. Both are within 8–12 pt.
- The `_174mm` variants are 9 pt at 174 mm, but they would print at 6.8 pt if included at `\textwidth` in the current manuscript. Do not use them there.
- **Fig. 2 changes.**
  - The panel titles are removed and replaced by (a), (b) and (c).
  - The bands are drawn in one colour-blind-safe hue with three clearly separated lightness levels, so they also read in greyscale.
  - New: a short horizontal line marks the fan median in each bar.
  - Imputation-affected quarters are hatched instead of grey-shaded.
- **Fig. 1 changes.** The content is unchanged (EN, Gaussian dashed, ACI γ=0.005 W=36). The interval lines are greyscale and distinguished by line style. The legend labels are shortened slightly ("Imputed index, Apr–May 2020", "Imputed base, Apr–May 2021"). Mathtext is removed, so DejaVu no longer mixes with Arial.
