r"""Fig. 1 (CPI intervals), re-rendered for print.

Plotting code copied from illustration/code/run_illustration.py (section 8) with the same content
(elastic net, Gaussian 90% interval, ACI 90% interval with gamma = 0.005 and W = 36, actual inflation,
markers for imputed / imputed-base months, R2 and R4 shaded), restyled:
  * width = sn-jnl \textwidth (31pc = 5.147 in = 130.7 mm), so \includegraphics[width=\textwidth] is 1:1;
  * all lettering 9 pt Arial, no mathtext (avoids a DejaVu fallback font);
  * no colour: line style distinguishes the intervals (dashed vs solid grey), shading in light grey.
Input: revision2/output/interval_paths_levels.csv (from run_illustration2.py).
Outputs: revision2/Fig1.pdf/.png and revision2/Fig1_174mm.pdf/.png (6.85 in variant).
Run:  python -I revision2/code/fig1.py
"""
from pathlib import Path

import warnings
import pandas as pd
warnings.filterwarnings("ignore", category=DeprecationWarning)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PROJ = Path(__file__).resolve().parents[2]
R2 = PROJ / "revision2"
TEXTWIDTH_IN = 372 / 72.27
REGIMES = {"R1": ("2017-01", "2020-02"), "R2": ("2020-03", "2021-12"), "R3": ("2022-01", "2025-12"),
           "R4": ("2026-01", "2099-12")}
IMPUTED = ["2020-04", "2020-05"]
IMPUTED_BASE = ["2021-04", "2021-05"]

p = pd.read_csv(R2 / "output" / "interval_paths_levels.csv")
p = p[(p.target == "headline") & (p.forecaster == "EN") & (p.nominal.round(2) == 0.9)]
g = p[p.method == "Gaussian"].set_index("month")
a = p[p.method == "ACI g=0.005 W=36"].set_index("month")
assert len(g) == 117 and len(a) == 117
idx = pd.PeriodIndex(g.index, freq="M")
x = idx.to_timestamp()

FS = 9
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial"], "font.size": FS,
                     "axes.labelsize": FS, "xtick.labelsize": FS, "ytick.labelsize": FS, "legend.fontsize": FS,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6})


def draw(width_in, fname):
    fig, ax = plt.subplots(figsize=(width_in, width_in * 0.62))
    last = idx.max()
    shade = {"R1": None, "R2": "0.88", "R3": None, "R4": "0.78"}
    for r, (s0, s1) in REGIMES.items():
        s0, s1 = pd.Period(s0, "M"), min(pd.Period(s1, "M"), last)
        x0 = s0.to_timestamp() - pd.Timedelta(days=15); x1 = s1.to_timestamp() + pd.Timedelta(days=15)
        if shade[r]:
            ax.axvspan(x0, x1, color=shade[r], lw=0, zorder=0)
        ax.text(x0 + (x1 - x0) / 2, 1.0, r, transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=FS)
    ax.plot(x, g.lo, color="0.0", lw=0.9, ls=(0, (4, 2)), zorder=2)
    ax.plot(x, g.hi, color="0.0", lw=0.9, ls=(0, (4, 2)), zorder=2, label="Gaussian 90% interval")
    ax.plot(x, a.lo, color="0.5", lw=1.1, zorder=2)
    ax.plot(x, a.hi, color="0.5", lw=1.1, zorder=2, label="ACI 90% interval (γ = 0.005, W = 36)")
    ax.plot(x, g.y, color="0.0", lw=1.4, zorder=3, label="Headline CPI inflation")
    ax.plot([pd.Period(m, "M").to_timestamp() for m in IMPUTED], g.y.loc[IMPUTED], ls="none", marker="o", ms=4.5,
            mfc="white", mec="0.0", mew=0.9, zorder=4, label="Imputed index, Apr–May 2020")
    ax.plot([pd.Period(m, "M").to_timestamp() for m in IMPUTED_BASE], g.y.loc[IMPUTED_BASE], ls="none",
            marker="s", ms=4, mfc="white", mec="0.0", mew=0.9, zorder=4,
            label="Imputed base, Apr–May 2021")
    ax.set_ylabel("Year-on-year inflation (%)")
    ax.set_xlim(x.min() - pd.Timedelta(days=20), x.max() + pd.Timedelta(days=20))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color="0.85", lw=0.4)
    ax.set_axisbelow(True)
    h, l = ax.get_legend_handles_labels()
    order = [0, 1, 2, 3, 4]
    fig.legend([h[i] for i in order], [l[i] for i in order], loc="lower center", bbox_to_anchor=(0.5, 0.0),
               frameon=False, ncol=2, handlelength=2.2, columnspacing=1.0, labelspacing=0.3)
    fig.tight_layout(pad=0.4, rect=(0, 0.185, 1, 1))
    fig.savefig(R2 / f"{fname}.pdf")
    fig.savefig(R2 / f"{fname}.png", dpi=600)
    plt.close(fig)


draw(TEXTWIDTH_IN, "Fig1")
draw(6.85, "Fig1_174mm")
print("Fig1 written")
