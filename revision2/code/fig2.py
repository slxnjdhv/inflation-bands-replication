r"""Fig. 2 (RBI fan-chart back-test), re-rendered for print.

Plotting code copied from revision/fanchart/code/07_evaluate.py (figure section) and restyled:
  * figure width = sn-jnl \textwidth (31pc = 372 TeX pt = 5.147 in = 130.7 mm), so that
    \includegraphics[width=\textwidth] is a 1:1 inclusion; every text item is 9 pt Arial
    (9 pt also stays within 8-12 pt if the figure is set at 174 mm, x1.33 -> 12.0 pt, or 119 mm, x0.91 -> 8.2 pt);
  * no titles inside the panels; panel labels (a), (b), (c) in the top-left corner;
  * bands in one colour-blind-safe hue with three clearly different lightness levels (readable in
    greyscale), the fan median as a short horizontal tick, the outturn as a solid line, filled / open
    circles for outturns inside / outside the 70 per cent band, hatching for imputation-affected
    quarters, a dotted vertical line at the start of the 2024-base CPI.
Inputs (read-only): revision/fanchart/bands.csv, illustration/output/data_inflation_series.csv.
Outputs: revision2/Fig2.pdf, revision2/Fig2.png, plus revision2/Fig2_174mm.pdf/.png (6.85 in wide variant).
Run:  python -I revision2/code/fig2.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

PROJ = Path(__file__).resolve().parents[2]
FAN = PROJ / "revision" / "fanchart"
R2 = PROJ / "revision2"
TEXTWIDTH_IN = 372 / 72.27

mon = {r["month"]: float(r["headline_yoy"]) for r in csv.DictReader(open(PROJ / "illustration/output/data_inflation_series.csv"))}
qv = {}
for m, v in mon.items():
    q = f"{m[:4]}Q{(int(m[5:7]) - 1) // 3 + 1}"
    qv.setdefault(q, []).append(v)
outturn = {q: sum(v) / 3 for q, v in qv.items() if len(v) == 3}

bands = list(csv.DictReader(open(FAN / "bands.csv")))
for b in bands:
    b["horizon"] = int(b["horizon"]); b["band_level"] = int(b["band_level"])
    b["lower"] = float(b["lower"]); b["upper"] = float(b["upper"])
    b["central"] = float(b["central"]) if b["central"] not in ("", "nan") else None
MAIN_ISSUES = sorted({b["issue"] for b in bands} - {"2016 Apr"})
IMPUTED = {"2020Q2", "2021Q2"}

FS = 9
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial"], "mathtext.fontset": "custom",
                     "mathtext.rm": "Arial", "font.size": FS, "axes.titlesize": FS, "axes.labelsize": FS,
                     "xtick.labelsize": FS, "ytick.labelsize": FS, "legend.fontsize": FS,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42, "ps.fonttype": 42,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})
# single blue hue (colour-blind safe), lightness 90% band > 70% band > 50% band
shade = {90: "#c6dbef", 70: "#6baed6", 50: "#2171b5"}
LINE = "#000000"
qi = lambda q: int(q[:4]) + (int(q[5]) - 1) / 4  # noqa: E731


def draw(width_in, fname):
    fig, axes = plt.subplots(3, 1, figsize=(width_in, width_in * 1.12), sharex=True)
    allq = sorted(outturn)
    for ax, h, lab in zip(axes, (1, 2, 4), ("(a)", "(b)", "(c)")):
        sel = [b for b in bands if b["issue"] in MAIN_ISSUES and b["horizon"] == h]
        for q in IMPUTED:
            ax.axvspan(qi(q) - 0.125, qi(q) + 0.125, facecolor="none", edgecolor="#8c8c8c", hatch="////",
                       lw=0, zorder=0)
        for L in (90, 70, 50):
            for b in [s for s in sel if s["band_level"] == L]:
                x = qi(b["target_quarter"])
                ax.add_patch(plt.Rectangle((x - 0.09, b["lower"]), 0.18, b["upper"] - b["lower"],
                                           facecolor=shade[L], lw=0, zorder=1))
        for b in [s for s in sel if s["band_level"] == 50 and s["central"] is not None]:
            x = qi(b["target_quarter"])
            ax.plot([x - 0.09, x + 0.09], [b["central"]] * 2, color="white", lw=1.0, zorder=1.5,
                    solid_capstyle="butt")
        qs = [q for q in allq if "2016Q3" <= q <= "2026Q3"]
        ax.plot([qi(q) for q in qs], [outturn[q] for q in qs], color=LINE, lw=0.9, zorder=2)
        for b in [s for s in sel if s["band_level"] == 70 and s["target_quarter"] in outturn]:
            y = outturn[b["target_quarter"]]; inside = b["lower"] <= y <= b["upper"]
            ax.plot(qi(b["target_quarter"]), y, marker="o", ms=4.2, zorder=3, ls="none",
                    mfc=LINE if inside else "white", mec=LINE, mew=0.9)
        ax.axvline(qi("2026Q1") - 0.125, color=LINE, lw=0.8, ls=(0, (1, 1.5)), zorder=0)
        ax.set_ylabel("Per cent")
        ax.text(0.005, 0.97, lab, transform=ax.transAxes, ha="left", va="top", fontsize=FS)
        ax.set_ylim(-1, 10.5); ax.set_yticks([0, 2, 4, 6, 8, 10])
        ax.grid(axis="y", color="#e6e6e6", lw=0.5); ax.set_axisbelow(True)
    axes[-1].set_xlim(2016.6, 2026.9)
    axes[-1].set_xticks(range(2017, 2027)); axes[-1].set_xlabel("Target quarter")
    hand = [Patch(facecolor=shade[50], label="50% band"), Patch(facecolor=shade[70], label="70% band"),
            Patch(facecolor=shade[90], label="90% band"),
            Line2D([], [], color=LINE, lw=0.9, label="CPI inflation, quarterly average"),
            Line2D([], [], marker="o", ls="none", mfc=LINE, mec=LINE, label="Outturn inside 70% band"),
            Line2D([], [], marker="o", ls="none", mfc="white", mec=LINE, label="Outturn outside 70% band"),
            Patch(facecolor="white", edgecolor="#8c8c8c", hatch="////", lw=0, label="Imputation-affected quarter"),
            Line2D([], [], color=LINE, lw=0.8, ls=(0, (1, 1.5)), label="Start of 2024-base CPI")]
    fig.legend(handles=hand, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0),
               handlelength=2.0, columnspacing=1.5, labelspacing=0.35)
    fig.tight_layout(rect=(0, 0.13, 1, 1), h_pad=0.6)
    fig.savefig(R2 / f"{fname}.pdf"); fig.savefig(R2 / f"{fname}.png", dpi=600)
    plt.close(fig)


draw(TEXTWIDTH_IN, "Fig2")
draw(6.85, "Fig2_174mm")
print("Fig2 written")
