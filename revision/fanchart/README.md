# Back-of-envelope evaluation of RBI CPI inflation fan charts (plan item 5)

Folder: `revision/fanchart/`. Built 2026-11-03 for the referee plan (`referee_assessment.md`, Section 4, rank 5, and Section 5, item 13). Nothing outside this folder was changed. The inflation file `illustration/output/data_inflation_series.csv` was only read.

## Deliverables

| File | Content |
|---|---|
| `bands.csv` | One row per issue × target quarter × band (50/70/90). There are 495 rows from 20 issues. Columns: issue, publication date and quarter, chart number, PDF page, target quarter, horizon, band level, lower, upper, digitised median (`central`), `source_type`, the digitised edges (`lower_digitised`, `upper_digitised`), the baseline stated in the text (`central_stated`), the per-issue `digitisation_error`, the official PDF URL and the archived copy. Rows with zero band width (history and the fan origin) are dropped. |
| `coverage_results.csv` | Horizons 0 to 4, bands 50/70/90, several samples. For each: n, inside, coverage, Clopper–Pearson 95% interval, exact two-sided binomial p against the nominal level, misses above and below, and borderline cases. Every row is computed twice: with the numbers stated in the text where available, and with digitised edges throughout. |
| `fig_fanchart_backtest.pdf/.png` | Outturns against band edges at h = 1, 2 and 4. Width 174 mm, sans-serif, 8 pt. |
| `table_fanchart.tex` | Booktabs tabular for h = 1, 2, 4. It has the full sample and a version excluding the imputation-affected quarters. |
| `code/` | `01_list_mprs.py` (archive index), `02_fetch_wayback.py` (PDFs), `03_survey.py` and `04_probe.py` (diagnostics), `05_extract_bands.py` (extraction and validation), `06_check_actual_line.py` (second check), `07_evaluate.py` (outputs). `chart_meta.json` holds the per-chart axis and quarter metadata. `stated_values.json` holds the numbers transcribed from the text. |
| `data_raw/` | MPR PDFs, archive index pages, `projection_text.txt` (extracted outlook passages), `validation.csv`, `actual_line_check.csv`, `bands_raw.csv`, `evaluation_obs.csv` and `outturns_quarterly.csv`. Chart renders are in `data_raw/render/`. |

Rerun everything from the project root with `python -I` in this order: `01, 02, 03, 05, 06, 07`. Scripts 01–06 take `revision/fanchart` as their argument. Scripts 06 and 07 also take the path to the inflation CSV.

## Sources (accessed 2026-11-03)

- **Index of issues.** RBI, *Monetary Policy Report* archive, https://www.rbi.org.in/Scripts/HalfYearlyPublications.aspx?head=Monetary%20Policy%20Report. Scraped year by year into `data_raw/mpr_index.csv`. It lists 22 issues from April 2016 to October 2026; the second 2022 issue is dated 30 September 2022.
- **PDFs.** A direct download from `rbidocs.rbi.org.in` returns a bot-check page. We did not try to circumvent it. Each full PDF was instead taken from an Internet Archive capture of the official URL, listed below. These are byte copies of the official files at the capture time. Several 1 MB captures were truncated and were replaced by complete captures.
- **Outturns.** Quarterly averages of monthly y-o-y all-India CPI (Combined), column `headline_yoy` of `illustration/output/data_inflation_series.csv`. These are MoSPI data at the latest vintage. They are on the 2012 base up to December 2025 and use the official 2024-base rates from January 2026; see `illustration/output/RESULTS.md`.

| Issue | Published | CPI fan chart | Digitisation error (max abs. deviation from text, pp) | Official PDF | Archived copy used |
|---|---|---|---|---|---|
| 2016 Apr | 2016-04-05 | Chart I.6, PDF p. 12 | 0.236 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR169AE87CE346B04E7384BC328081503FC8.PDF | https://web.archive.org/web/20220420045027/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR169AE87CE346B04E7384BC328081503FC8.PDF |
| 2016 Oct | 2016-10-04 | Chart I.6, PDF p. 12 | 0.047 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR_F4A9FF233E5B5453D856849DD52D5F6A4.PDF | https://web.archive.org/web/20211221044854/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR_F4A9FF233E5B5453D856849DD52D5F6A4.PDF |
| 2017 Apr | 2017-04-06 | Chart I.7, PDF p. 15 | 0.05 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR060420174217941BF3DB49899EC6B51294AC6EF5.PDF | https://web.archive.org/web/20210126050541/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR060420174217941BF3DB49899EC6B51294AC6EF5.PDF |
| 2017 Oct | 2017-10-04 | Chart I.6, PDF p. 14 | 0.042 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRE9D435BE4A964EE1917FDF1A5003C65F.PDF | https://web.archive.org/web/20210416223000/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRE9D435BE4A964EE1917FDF1A5003C65F.PDF |
| 2018 Apr | 2018-04-05 | Chart I.6, PDF p. 15 | 0.071 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0504201881C23881962B49BD98827921418306A5.PDF | https://web.archive.org/web/20220420044811/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0504201881C23881962B49BD98827921418306A5.PDF |
| 2018 Oct | 2018-10-05 | Chart I.6, PDF p. 14 | 0.144 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR20181903C4178AD08947D5A2BD6C315B3F121C.PDF | https://web.archive.org/web/20220120190533/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR20181903C4178AD08947D5A2BD6C315B3F121C.PDF |
| 2019 Apr | 2019-04-04 | Chart I.6, PDF p. 17 | 0.066 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR_APRIL2019EE03BCD257AF4C6493A43FAE1150738F.PDF | https://web.archive.org/web/20220308015040/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR_APRIL2019EE03BCD257AF4C6493A43FAE1150738F.PDF |
| 2019 Oct | 2019-10-04 | Chart I.6, PDF p. 15 | 0.085 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCTOBER2019_E166D908F28014DDF9E9254660184B787.PDF | https://web.archive.org/web/20220603184733/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCTOBER2019_E166D908F28014DDF9E9254660184B787.PDF |
| 2020 Apr | 2020-04-09 | **No CPI fan chart.** The text gives a "tentative" point path only, 4.8, 4.4, 2.7 and 2.4% for Q1–Q4 2020-21, citing COVID-19 uncertainty. | – | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL2020E3D4AD8245734F27B6C5688F22B4FA2F.PDF | https://web.archive.org/web/20200416123635/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL2020E3D4AD8245734F27B6C5688F22B4FA2F.PDF |
| 2020 Oct | 2020-10-09 | Chart I.6, PDF p. 16 | 0.054 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0910200CB2848C2D8A40758A1FB7AE110E3F16.PDF | https://web.archive.org/web/20201014220624/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0910200CB2848C2D8A40758A1FB7AE110E3F16.PDF |
| 2021 Apr | 2021-04-07 | Chart I.6, PDF p. 15 | 0.039 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRA202113A99DAD95344334BF6145CCBB26A744.PDF | https://web.archive.org/web/20210407190944/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRA202113A99DAD95344334BF6145CCBB26A744.PDF |
| 2021 Oct | 2021-10-08 | Chart I.6, PDF p. 16 | 0.048 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRO08102021A0391DC82DBF4F78BA600399F12356EA.PDF | https://web.archive.org/web/20211008092627/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRO08102021A0391DC82DBF4F78BA600399F12356EA.PDF |
| 2022 Apr | 2022-04-08 | Chart I.6, PDF p. 19 | 0.045 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0804223897C8D9006C4981AEBA943DEDDD6F98.PDF | https://web.archive.org/web/20220408053639/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR0804223897C8D9006C4981AEBA943DEDDD6F98.PDF |
| 2022 Sep | 2022-09-30 | Chart I.6, PDF p. 18 | 0.051 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRSEPT2022F37AE373909740E3A281C7C08B56984E.PDF | https://web.archive.org/web/20240711081442/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRSEPT2022F37AE373909740E3A281C7C08B56984E.PDF |
| 2023 Apr | 2023-04-06 | Chart I.6, PDF p. 16 | 0.045 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPR2023CE7252C3A2594B408162BF7877EF7F03.PDF | https://web.archive.org/web/20230407114809/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPR2023CE7252C3A2594B408162BF7877EF7F03.PDF |
| 2023 Oct | 2023-10-06 | Chart I.6, PDF p. 16 | 0.036 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCT2023438C9B0CF19149FC80BAE49B80424FCB.PDF | https://web.archive.org/web/20231006114528/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCT2023438C9B0CF19149FC80BAE49B80424FCB.PDF |
| 2024 Apr | 2024-04-05 | Chart I.6, PDF p. 19 | 0.022 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL2024866555514098406BA610767D0E792E87.PDF | https://web.archive.org/web/20240405090249/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL2024866555514098406BA610767D0E792E87.PDF |
| 2024 Oct | 2024-10-09 | Chart I.6, PDF p. 17 | 0.045 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCT09102024F3D5C5FF43BC447BFBCDAC6195D350443.PDF | https://web.archive.org/web/20241020203829/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPROCT09102024F3D5C5FF43BC447BFBCDAC6195D350443.PDF |
| 2025 Apr | 2025-04-09 | **Not obtained.** The official URL is behind the bot check, the Internet Archive holds no PDF capture, and the archived HTML page has no content. The issue is skipped. | – | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL2025D2BFE2D64214448F8234BCAC98C133C9.PDF | none |
| 2025 Oct | 2025-10-01 | Chart I.6, PDF p. 16 | 0.048 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR011020257F52BDBF1F184AE0A627BD9CEB1580FB.PDF | https://web.archive.org/web/20251001064840/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPR011020257F52BDBF1F184AE0A627BD9CEB1580FB.PDF |
| 2026 Apr | 2026-04-08 | Chart V.5, PDF p. 109 | 0.05 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL080426F22A3C8019DF4BDE889912B6209E8B7B.PDF | https://web.archive.org/web/20260408085628/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/MPRAPRIL080426F22A3C8019DF4BDE889912B6209E8B7B.PDF |
| 2026 Oct | 2026-10-07 | Chart V.6, PDF p. 100 | 0.009 | https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/01MPR071020267B057FA4E71E4164A8B14EDC40197418.PDF | https://web.archive.org/web/20261007062600/https://rbidocs.rbi.org.in/rdocs/Publications/PDFs/01MPR071020267B057FA4E71E4164A8B14EDC40197418.PDF |

## What the MPRs publish

- **Fan chart.** Every issue except April 2020 and the unobtained April 2025 has a CPI fan chart, titled "Projection of CPI Inflation (y-o-y)". In 2026 it moved to Chapter V.
- **Bands.** Every chart shows **50, 70 and 90 per cent** bands. The chart note defines them as "confidence intervals" with 50/70/90% probability of containing the outturn; see, for example, the October 2024 MPR, Chart I.6 note. The October 2016 and April 2016 legends already show all three, so the manuscript's "90% in some issues" should read "50, 70 and 90 per cent in every MPR fan chart since at least April 2016".
- **Horizon.** The fan starts at the last fully observed quarter. The first projected quarter is the one before publication, partly observed (Jan–Mar in April issues, Jul–Sep in October issues). The fan ends in Q4 (Jan–Mar) of the next fiscal year: 7 to 9 projected quarters, or up to 7 quarters after the publication quarter.
- **Numbers in the text.** The text gives the baseline (modal) path by quarter. From April 2017 it also gives the 50 and 70 per cent intervals for Q4 of the current and next fiscal year; October 2016 and April 2016 give only the 70 per cent interval. The **90 per cent band is never stated numerically**. We found no chart data download or RBI database series.

## Method

1. **Extraction (digitisation of vector graphics, not raster images).** All 20 fan charts are vector paths in the PDFs. The band polygons are filled in three shades of red, which we classify by the green channel. At each quarterly vertex, the edges of the L% band are the outermost vertices of all polygons with shade ≤ L; the bands are nested. y is mapped to per cent linearly using the value-axis line. Its end points coincide with the end tick marks; in April 2016 we used tick-label centres instead. The axis end values were read from the rendered charts. Quarters are counted back from the last quarter on the x axis.
   - The digitised "central" value is the median quantile path, the middle boundary of the symmetric quantile pairs. It is not the modal baseline, and the two differ when risks are skewed.
2. **Validation.**
   - **Against the text.** Every number in the text that can be matched was compared with the digitised value: 209 numbers from 19 MPC-era issues, of which 136 are band edges and 73 are baseline points. Mean absolute error is 0.026 pp, RMSE 0.036 pp and maximum 0.144 pp; 89% are within ±0.05, the rounding of the text. The October 2018 chart is offset by about +0.1 pp: its band edges are 0.05 to 0.13 too high and its baseline 0.08 to 0.14 too high. Excluding it, the maximum error is 0.085 and 93.5% are within ±0.05.
   - **Against the data.** The historical CPI line drawn in each chart was also digitised and compared with official quarterly averages: 154 quarters, median absolute difference 0.005 pp. The exception is again October 2018, at about +0.11. We applied no correction.
   - **April 2016** (pre-MPC) shows errors of 0.13 to 0.24, from the label-based axis. It is in `bands.csv` but outside the evaluation.
   - **Text versus digitised edges.** `bands.csv` uses the numbers stated in the text where they exist (`source_type = numeric (MPR text)`) and digitised edges otherwise. Replacing every edge with its digitised value changes one classification: April 2018, 2019Q1, 70% band, h = 3, outturn 2.47 against a stated lower edge of 2.5.
3. **Horizon.** h = target calendar quarter minus the calendar quarter containing the publication date. For April issues, h = 1 is Jul–Sep; for October issues, h = 1 is Jan–Mar. The September 2022 issue (30 September) is dated 2022Q3, so its h is one larger than an October issue's would be.
4. **Evaluation sample.** MPC-era issues from October 2016 to April 2026, 18 charts. The sample excludes April 2016 (pre-MPC), April 2020 (no fan chart), April 2025 (not obtained) and October 2026 (no outturns yet). Outturns run to 2026Q3, which gives n = 18, 17 and 16 at h = 1, 2 and 4.
5. **Statistics.** Coverage is the share of outturns with lower ≤ y ≤ upper. Each coverage figure comes with a Clopper–Pearson 95% interval and an exact two-sided binomial p-value against the nominal level, with misses split into above and below. Outturns within the issue's digitisation error, at least 0.05, of an edge are flagged as borderline.
6. **Sensitivity samples:**
   - excluding target quarters affected by the imputation of the April–May 2020 CPI (2020Q2, and 2021Q2 through the base effect);
   - excluding all COVID targets, 2020Q2 to 2021Q4;
   - excluding new-base targets from 2026Q1;
   - by period of the target quarter.

## Results (h = 1, 2, 4; text-stated edges where available)

| h | Band | Inside/n | Coverage [95% CP] | p | Above / below |
|---|---|---|---|---|---|
| 1 | 50 | 12/18 | 0.67 [0.41, 0.87] | 0.24 | 2 / 4 |
| 1 | 70 | 14/18 | 0.78 [0.52, 0.94] | 0.61 | 1 / 3 |
| 1 | 90 | 17/18 | 0.94 [0.73, 1.00] | 1.00 | 1 / 0 |
| 2 | 50 | 10/17 | 0.59 [0.33, 0.82] | 0.63 | 3 / 4 |
| 2 | 70 | 12/17 | 0.71 [0.44, 0.90] | 1.00 | 2 / 3 |
| 2 | 90 | 15/17 | 0.88 [0.64, 0.99] | 0.69 | 1 / 1 |
| 4 | 50 | 10/16 | 0.63 [0.35, 0.85] | 0.45 | 3 / 3 |
| 4 | 70 | 13/16 | 0.81 [0.54, 0.96] | 0.42 | 2 / 1 |
| 4 | 90 | 15/16 | 0.94 [0.70, 1.00] | 1.00 | 0 / 1 |

- **Overall.** No coverage rate differs significantly from nominal; every p is above 0.2. Empirical coverage is at or above nominal for most cells, with only the h = 2 70% and 90% bands slightly below (0.71, 0.88). Excluding the imputation-affected quarters changes only h = 2 and h = 4, by at most one observation each.
- **Borderline cases.** At h = 1, two 50% cases sit within digitisation error of an edge: April 2018 → 2018Q3, and April 2023 → 2023Q3. At h = 1 there is also one 90% case, October 2018 → 2019Q1. The 50% count at h = 1 could therefore be 12 to 14.
- **2016Q4–2020Q1 (targets).** Misses are mostly **below** the band: outturns fell short of the projected path in 2017–19. The 50% band at h = 1 covered 2 of 7 (p = 0.45), and the 70% band at h = 2 covered 2 of 6 (p = 0.07). The problem looks like a level bias, not over-wide bands. The exception is the onion and COVID episode of late 2019 to 2020, where misses were **above**: October 2019 → 2020Q1 was outside even the 90% band.
- **2020Q2–2022Q4.** All h = 1 outturns were inside every band (5/5). At h = 4 the 50% band covered 2 of 5 and the 70% band 3 of 5, with all misses **above**: the 2022 surge.
- **2023Q1–2026Q3.** Coverage is at or above nominal. The only misses are **below**, in 2025 (the 2025 disinflation): October 2024 → 2025Q4 was outside the 90% band.
- **Hypothesis check.** The working hypothesis was that the bands were too wide in 2017–19 and too narrow in 2020–22. The evidence for it is weak. The 2017–19 misses point to bias in the centre, and the 2020–22 misses appear only at the 4-quarter horizon.

## Caveats

- **Small and dependent sample.** n is 16 to 18 per cell. Issues are 6 months apart while horizons reach 4 quarters, so forecast errors overlap across issues. Horizons from the same issue share the same information set. Exact binomial intervals assume independence and are therefore too narrow. Power is low: with n = 17 and nominal 0.70, the exact test rejects at 5% only if 7 or fewer outturns (coverage 0.41 or less) or 16 or more (0.94 or more) fall inside.
- **Reading of the charts.** Values are digitised from the published charts, not taken from RBI's internal densities. They are mostly accurate to the 0.1 pp rounding of the text; October 2018 is offset by about 0.1 pp.
- **Outturn vintage.** Outturns are the latest data vintage, not the real-time data RBI later compared against. Quarterly averages of monthly y-o-y rates are used, which may differ slightly from RBI's quarterly definition.
- **COVID imputation.** The April–May 2020 CPI was imputed, which affects 2020Q2 and, through the base effect, 2021Q2.
- **Base change.** Targets from 2026Q1 are on the 2024-base CPI, while the projections were made for the 2012-base series. Only 2025 Oct h = 1 and 2, and 2026 Apr h = 1, are affected.
- **Missing issues.** April 2020 had no fan chart and April 2025 could not be obtained. September 2022 shifts the horizon definition by one quarter.
- **Conditionality.** The bands are conditional on the stated assumptions (crude, monsoon, policy) and do not account for policy feedback. Strictly, this is an evaluation of the communicated uncertainty, not of a model.

## Draft paragraph for the manuscript (illustrative, about 300 words)

> To show that the absence we document is not a matter of data availability, we carried out a back-of-envelope check of the fan charts in the Reserve Bank's Monetary Policy Reports. Since at least 2016, every CPI fan chart has shown 50, 70 and 90 per cent bands, drawn as vector graphics. This allowed the band edges to be extracted from the PDFs with an error of about 0.03 percentage points, judged against the 50 and 70 per cent intervals and baseline paths stated in the text. For the 18 MPC-era reports from October 2016 to April 2026 that contain a fan chart and could be retrieved, we counted how often quarterly average CPI inflation fell inside each band at horizons of one, two and four quarters after the publication quarter. Coverage of the 50, 70 and 90 per cent bands was 0.67, 0.78 and 0.94 at one quarter (n = 18); 0.59, 0.71 and 0.88 at two quarters (n = 17); and 0.63, 0.81 and 0.94 at four quarters (n = 16). No rate differs significantly from its nominal level under exact binomial tests. The Clopper–Pearson intervals are wide: for example, 0.44 to 0.90 for the 70 per cent band at two quarters. Because successive reports overlap in their forecast windows, even these intervals overstate the information in the sample. The direction of the misses is more informative than their number. Outturns fell below the bands in 2017–19 and in 2025, and rose above them in the 2019–20 vegetable-price and pandemic episode and at the four-quarter horizon in 2022. This points to errors in the centre of the bands during regime shifts, rather than a uniform under- or over-statement of their width. The quarters affected by the imputation of CPI in April–May 2020 do not change the picture. The exercise is descriptive and has low power. Its point is that a routine, published calibration record of this kind is feasible and is currently missing.
