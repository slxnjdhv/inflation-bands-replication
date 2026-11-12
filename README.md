# Code and data: "Are Inflation Uncertainty Bands Calibrated?"

This package reproduces every number, table and figure in the manuscript's own analysis.
It contains only public data (MoSPI consumer price indices and the RBI fan-chart band edges
extracted from archived Monetary Policy Reports).

## Setup

    pip install -r requirements.txt     # Python 3.11 or 3.12

Run every command from this folder (the package root), with `python -I`.

## What reproduces what

| Manuscript item | Folder | Command |
|---|---|---|
| Table 5 (coverage) and the pandemic numbers in Section 7 | `illustration/` | `python -I illustration/code/run_illustration.py` |
| Table 6 (error-based baseline, Diebold-Mariano tests) | `revision2/` | `python -I revision2/code/run_illustration2.py`, then `python -I revision2/code/dm_tests.py` |
| Fig. 1 and Fig. 2 | `revision2/` | `python -I revision2/code/fig1.py`, `python -I revision2/code/fig2.py` |
| Holm-adjusted p-values and dynamic-quantile tests (Section 7) | `revision/fix_v5/` | `python -I revision/fix_v5/holm_dq.py` |
| Fan-chart back-test (Table 8 and Fig. 2) | `revision/fanchart/` | see `revision/fanchart/README.md` |
| Table 7 (3- and 6-month horizons) | `revision/fix_v6/horizon/` | `python -I revision/fix_v6/horizon/run_horizon.py`, then `make_table.py` |
| Three-quarter breach probability (Section 6) | `revision/fix_v6/` | `python -I revision/fix_v6/breach_prob.py` |
| Appendix simulations (power, group sizes) | `revision/proposition/` | `python -I revision/proposition/code/regime_coverage.py` |

Run `illustration/` first: the other analyses read its output CSVs.

## Data

- `illustration/data_raw/`: the MoSPI API responses as downloaded on 3 November 2026. Addresses
  and dates are in `illustration/data_raw/SOURCES.md`.
- `revision/fanchart/data_raw/`: the index of reports, the Internet Archive capture list, the
  extracted band edges and the validation files. The report PDFs themselves are not
  redistributed: `revision/fanchart/code/02_fetch_wayback.py` downloads them again from the
  Internet Archive, and `pdf_provenance.csv` records the checksum of every file used.

Stored outputs are included next to each script, so the results can be checked without
re-running anything.
