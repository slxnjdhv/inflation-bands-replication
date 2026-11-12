# Raw data sources

All files in this folder were downloaded on **2026-11-03** with `curl` (User-Agent "Mozilla/5.0").
No downloaded code was executed. The files are stored exactly as returned by the server.

## 1. CPI, base 2012 = 100 (MoSPI API)

Endpoint: MoSPI public API, `getCPIIndex`.
All-India (`state_code=99`), Combined sector (`sector_code=3`), all groups and sub-groups, one
calendar year per request. The server caps `limit` at 200, so each year comes in two pages.

URL template (Y = 2013..2026, P = 1, 2):

    https://api.mospi.gov.in/api/cpi/getCPIIndex?base_year=2012&series=Current&year=Y&state_code=99&sector_code=3&Format=JSON&limit=200&page=P

Files: `mospi_cpi_base2012_<Y>_p<P>.json`.
- Coverage: January 2013 to December 2025, with 28 records per month. The 2026 files hold only the
  response `"No Data Found"`, because the 2012-base series stops at December 2025.
- Series used: `General / General-Overall` (CPI Combined General Index) and
  `Consumer Food Price / Consumer Food Price-Overall` (CFPI).
- The `status` field is `F*` for General in April and May 2020, and for CFPI in April 2020.
  These are MoSPI's imputed indices for the COVID-19 lockdown months, and the published
  y-o-y inflation for them is `null`. CFPI for May 2020 carries status `F`, but it was also
  compiled under lockdown conditions. Both April and May 2020 are flagged for both series.

## 2. CPI, base 2024 = 100 (MoSPI API, the endpoint behind the eSankhyiki portal)

Endpoint: `getCPIData`. I found it in the public JavaScript bundle of
https://esankhyiki.mospi.gov.in. The bundle was only read and searched with grep; it was not
executed. For base 2024, All-India is `state_code=1`. The server caps `limit` at 100.

- General index, Current series (2025 and 2026; 2025 is the overlap year):
  `https://api.mospi.gov.in/api/cpi/getCPIData?base_year=2024&level=Group&state_code=1&sector_code=3&limit=100&series=Current&year=Y&division_code=0`
  Files: `mospi_cpi_base2024_current_2025_general.json` (Jan to Dec 2025, index only) and
  `mospi_cpi_base2024_current_2026_general.json` (Jan to Sep 2026, index and y-o-y inflation).
- General index, official Back series (linked, 2013 to 2024):
  same URL with `series=Back&year=Y`, Y = 2013..2024. Files: `mospi_cpi_base2024_back_<Y>_general.json`.
- Food group (COICOP 2018 group 01.1 "Food", division 1, group 1), Current series 2026, 18 pages:
  `https://api.mospi.gov.in/api/cpi/getCPIData?base_year=2024&level=Group&state_code=1&sector_code=3&limit=100&series=Current&year=2026&division_code=1&group_code=1&page=P`
  Files: `mospi_cpi_base2024_current_2026_foodgroup_p01.json` to `..._p18.json`. Only the
  group-level aggregate records (`class == null`) are used.

The parameter discovery endpoints were queried but not stored, because they contain no data:
`https://api.mospi.gov.in/api/cpi/getCpiBaseYear` and
`https://api.mospi.gov.in/api/cpi/getCpiFilterByLevelAndBaseYear?base_year=2024&level=Group&series=Current`.

## 3. MoSPI FAQ on CPI 2024 series (Annexure V, 12 Feb 2026)

URL: https://www.mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf
File: `mospi2026_faq_Annexure_V.pdf` (bib key `mospi2026faq`).

Q37 defines LF = (geometric mean of new-series index, 2025) / (geometric mean of old-series index, 2025)
and states that the linked index is the old index multiplied by LF, i.e. I_linked(t) = I_old(t) x LF.
Q38 gives LF = 0.5267 for Combined. So the direction is: **new-base equivalent = old x 0.5267**.

## 4. Sources tried and not used

- RBI DBIE and the FRED/OECD fallback were not needed, because MoSPI data were available.
- Rainfall: no public machine-readable all-India monthly rainfall-departure series covering
  2013 to 2026 was found. The IITM all-India series (via IRI Data Library) ends in 2016.
  data.gov.in resources end in 2017 or 2019, cover only the monsoon season, or need an API key.
  IMD monthly summaries are PDF charts. Rainfall was therefore **not used**, and a lagged
  food-shock indicator built from CFPI was used instead (see README).
