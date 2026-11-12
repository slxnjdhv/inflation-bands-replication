# Empirical illustration: coverage of 90% intervals for Indian CPI inflation

A small, reproducible exercise for the review article (`../main.tex`). It does not modify the
manuscript.

## Reproduce

```
pip install pandas numpy scipy scikit-learn matplotlib statsmodels
python -I illustration/code/run_illustration.py      # run from the package root; about 80 s
```

Versions used: Python 3.11 on Windows, pandas 3.1.0, scikit-learn 1.9.1.

The script reads only `data_raw/` and writes only `output/`. It uses no random sampling,
and two consecutive runs gave byte-identical CSV outputs. Download URLs and dates are in
`data_raw/SOURCES.md`. Re-downloading later may give revised numbers, especially for the
provisional 2026 months.

## Data

| Series | Source | Span used |
|---|---|---|
| CPI Combined General, base 2012=100 | MoSPI API `getCPIIndex` | indices 2013-01 to 2025-12; y-o-y 2014-01 to 2025-12 |
| CFPI Combined, base 2012=100 | same | same |
| CPI Combined General, base 2024=100 | MoSPI API `getCPIData` (eSankhyiki backend) | indices 2025-01 to 2026-09; y-o-y 2026-01 to 2026-09 |
| Food group (COICOP 01.1), base 2024=100 | same | published y-o-y 2026-01 to 2026-09 |
| Official linked back series, General | same (`series=Back`) | 2013-01 to 2024-12, used for checks only |

**Headline target.** Y-o-y inflation is computed from the 2012-base indices up to December 2025.
From January 2026 it is the official new-basket y-o-y, i.e. a 2026 index over a 2025 index,
both on base 2024.

**Linking factor.** The MoSPI FAQ (Q37–38) defines the linked index as old × LF, with
LF = 0.5267 (Combined). The script verifies this in three ways:
- the official back series equals old × 0.5267 to within rounding (max diff 0.05 index points);
- the 2025 geometric-mean ratio of new to old indices is 0.5267;
- recomputing y-o-y from the indices reproduces the published rates (max diff 0.01 pp).

A constant factor leaves y-o-y rates before 2026 unchanged. Because 2025 exists on both bases,
2026 y-o-y needs no cross-base splice. For comparison only, a cross-base rate
(2026 new index / (2025 old index × LF)) differs from the official rate by -0.20 to +0.27 pp
(see `output/run_log.txt`).

**Regime R4 starts in 2026-01, not 2026-02.** The release of 12 February 2026 published the
**January 2026** index on base 2024 (y-o-y 2.73–2.75 per cent). So the new-base window is
2026-01 to 2026-09 (n = 9), and R3 ends in 2025-12.

**Food.** The food target uses only the 2012-base CFPI, evaluated to 2025-12. The food
inflation used as a *predictor* and in the shock indicator is CFPI up to 2025-12 and the
new-base Food group (01.1) y-o-y from 2026-01. This splice is researcher-made: there is no
official linked CFPI, and the two baskets differ.

**Imputed months.** MoSPI flags April–May 2020 General and April 2020 CFPI as imputed
(status `F*`). Y-o-y for April–May 2021 uses those imputed bases. All four months stay in the
main results. A sensitivity check that drops them is in `output/results_all.csv`
(regime `All excl. Apr-May 2020/2021`).

**Rainfall.** No public machine-readable all-India monthly rainfall-departure series for
2013–2026 was found (see SOURCES.md), so rainfall was not used.

## Design

- **Timing.** The forecast for month t uses data through t−1 and is re-estimated every month
  on an expanding window. Targets start in 2015-01, the first month with 12 lags.
  Out-of-sample point forecasts run from 2016-01, with a first training size of 12. Intervals
  are evaluated from 2017-01, with a training size of 24 to 140. The CPI release lag of about
  12 days is ignored: y_{t−1} is treated as known when forecasting t.
- **Forecasters.**
  - AR(p): OLS with an intercept, p ∈ {1..min(12, n/4)} chosen by BIC.
  - Elastic net: sklearn `ElasticNetCV` on 12 lags of headline and food y-o-y inflation, with
    standardised features, l1_ratio ∈ {0.1, 0.5, 0.9, 1}, 50 alphas, and `TimeSeriesSplit`
    using min(5, max(2, n/8)) folds. The scaler is fit on the full training window before CV,
    which leaks a little within folds.
- **Intervals at α = 0.10.**
  - (i) Gaussian: ŷ ± 1.645 s, where s is the in-sample residual s.d. with a degrees-of-freedom
    correction.
  - (ii) Split conformal on absolute out-of-sample residuals of the last W ∈ {36, 60} months,
    taking the ⌈(n+1)(1−α)⌉-th smallest. In 2017–2018 (W = 36) and 2017–2020 (W = 60) fewer than
    W residuals exist, so the window holds all available ones (at least 12).
  - (iii) ACI (Gibbs & Candès 2021): α_t starts at 0.1 in 2017-01 and is updated by
    α_{t+1} = α_t + γ(α − err_t), with γ ∈ {0.005, 0.02}. A capped or empty interval would be
    logged, but neither occurred.
  - (iv) Regime-conditional split conformal: uses the most recent W past residuals from months
    in the same food-shock state, and falls back to pooled (ii) when fewer than 9 exist.
- **Food-shock indicator** (known at t−1). Let d_s = π^food_s − π^food_{s−3}. Then
  S_t = 1{d_{t−1} > 80th percentile of all d_s with s ≤ t−1}. In the headline evaluation sample,
  27 of 117 months are shock months.
- **Metrics.**
  - Coverage, mean width and mean interval score (Gneiting & Raftery 2007), overall and by
    regime and shock state.
  - Exact two-sided binomial (Kupiec-type) p-values per regime.
  - Christoffersen LR_uc, LR_ind and LR_cc p-values (asymptotic χ²) overall.
  - Point RMSE.

## Outputs (`output/`)

- `table_coverage.tex` / `.csv` — main headline table, W = 36 (booktabs tabular only).
- `table_coverage_W60.tex` / `.csv` — robustness, W = 60.
- `table_coverage_food.tex` / `.csv` — CFPI target, to 2025-12.
- `fig_intervals.pdf` / `.png` — EN headline forecasts with Gaussian and ACI (γ = 0.005, W = 36)
  intervals; 174 mm wide, sans-serif 8 pt.
- `results_all.csv` — every target × forecaster × method × regime, plus test p-values,
  fallback counts and ACI flags.
- `interval_paths.csv`, `point_forecasts_*.csv`, `data_inflation_series.csv`, `run_log.txt`.
- `RESULTS.md` — summary of results and draft text for the manuscript.

## Caveats

- Regimes are short, with n = 38, 22, 48 and 9. At 90 per cent nominal coverage, R4 expects
  about one miss, so the tests have very low power.
- The data are current vintage, not real time. The release lag is ignored.
- The early elastic-net fits use 12 to 24 observations for 24 predictors.
- The 2026 food predictor is spliced across bases.
- The imputed COVID months are included in the main results.
- The design was fixed before results were inspected. The only post-run changes were to the
  figure: moving the legend, and (3 Nov 2026) adding a square marker for April–May 2021, whose
  indices are not imputed (MoSPI status `F`) but whose y-o-y rates use the imputed April–May 2020
  indices as base. A re-run confirmed that all CSV and .tex outputs are byte-identical; only
  `fig_intervals.pdf/.png` changed. The manuscript uses `../Fig1.pdf`, a copy of `fig_intervals.pdf`.
