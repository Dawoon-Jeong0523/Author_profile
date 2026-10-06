#!/usr/bin/env python3
"""make_figures.py: README figures of the 2026 Nobel forecasts, top 5 against the award.

    $PY docs/nobel2026/make_figures.py      # -> docs/nobel2026/{medicine,physics}_2026_top5_vs_award.{png,svg}

Data: Data/Result/nobel_{medicine,physics}_2026_probabilities.csv (the final Preseen forecasts, 30 outcomes each). The
layout follows Data/Result/Figure_Nobel.ipynb (same header, colours and row geometry); added here: the awarded
discovery is drawn in a second accent colour and, when it is outside the top 5, shown below a gap with its rank.
"""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Data" / "Result"
OUT = Path(__file__).resolve().parent
INK, MUTED, ACCENT, SECONDARY, AWARD = "#172F40", "#556773", "#087F74", "#8AA4B4", "#C2410C"
TOP_N = 5

FIELDS = {
    "medicine": {
        "csv": "nobel_medicine_2026_probabilities.csv",
        "title": "2026 Nobel Prize in Physiology or Medicine",
        "subtitle": "Forecast top 5 of 30 laureate-set outcomes, and the awarded discovery",
        "awarded": [6],                       # best-ranked outcome of the awarded discovery (optogenetics)
        "award_tag": "awarded discovery",
        "xmax": 30,
        "notes": ["Awarded 5 Oct 2026: Karl Deisseroth, Peter Hegemann and Georg Nagel, for light-gated ion channels and "
                  "optogenetics. The exact trio was not among the 30 outcomes; the three optogenetics lineups "
                  "(ranks 6, 7, 23) hold 8.6 % together.",
                  "Forecast: Preseen treatment forecast of 4 Oct 2026 (Treatment Final), conditional on one of the 30 "
                  "listed outcomes."],
    },
    "physics": {
        "csv": "nobel_physics_2026_probabilities.csv",
        "title": "2026 Nobel Prize in Physics",
        "subtitle": "Forecast top 5 of 30 discoveries, and the awarded discovery",
        "awarded": [14],                      # high-energy cosmic neutrinos
        "award_tag": "awarded discovery",
        "xmax": 10,
        "notes": ["Awarded 6 Oct 2026: Francis Halzen alone, for the IceCube Neutrino Observatory and the discovery of "
                  "high-energy neutrinos of astrophysical origin (the option named Halzen, Karle and Kurahashi Neilson).",
                  "Forecast: Preseen, 5 Oct 2026, profile cards as the main evidence, conditional on one of the 30 "
                  "listed discoveries."],
    },
}


def draw(key, cfg):
    df = pd.read_csv(DATA / cfg["csv"], encoding="utf-8-sig").sort_values("rank")
    top = df.head(TOP_N)
    extra = df[df["rank"].isin(cfg["awarded"]) & (df["rank"] > TOP_N)]
    rows = list(top.itertuples()) + ([None] if len(extra) else []) + list(extra.itertuples())
    n = len(rows)
    k_notes = len(cfg["notes"])
    foot = 0.3 + 0.55 * k_notes + 0.6                      # notes block + room for the x tick labels
    height = 1.85 + 0.85 * n + foot
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none"}):
        fig = plt.figure(figsize=(14, height), facecolor="white")
        fig.text(0.065, 1 - 0.34 / height, "KNOWLEDGE LAB + PRESEEN", fontsize=12, weight="bold", color=ACCENT, va="top")
        fig.text(0.065, 1 - 0.72 / height, cfg["title"], fontsize=25, weight="bold", color=INK, va="top")
        fig.text(0.065, 1 - 1.28 / height, cfg["subtitle"], fontsize=13.5, color=MUTED, va="top")
        bottom = foot / height
        ax = fig.add_axes([0.515, bottom, 0.405, (0.85 * n - 0.05) / height])
        ax.set_ylim(n - 0.45, -0.65)
        ax.set_xlim(0, cfg["xmax"])
        step = 5 if cfg["xmax"] > 10 else 2
        ax.set_xticks(range(0, cfg["xmax"] + 1, step))
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.tick_params(axis="x", length=0, pad=9, labelsize=11, colors=MUTED)
        ax.set_yticks([])
        ax.grid(axis="x", color="#E4E9EC", linewidth=0.8, zorder=0)
        for s in ax.spines.values():
            s.set_visible(False)
        for i, r in enumerate(rows):
            if r is None:
                ax.text(-1.11, i, "···", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=18,
                        color=MUTED)
                continue
            rank, p = int(r.rank), float(r.probability_pct_reported)
            awarded, first = rank in cfg["awarded"], rank == 1
            color = AWARD if awarded else ACCENT if first else SECONDARY
            ink = AWARD if awarded else ACCENT if first else INK
            ax.barh(i, p, height=0.43, color=color, zorder=3)
            ax.text(-1.11, i - 0.12, f"{rank:02d}  {r.plot_label}", transform=ax.get_yaxis_transform(), ha="left",
                    va="center", fontsize=15.5, weight="bold" if (first or awarded) else "normal", color=ink)
            desc = textwrap.shorten(str(r.discovery_short), width=70, placeholder="…") + ("   ◀ " + cfg["award_tag"] if awarded else "")
            ax.text(-1.11, i + 0.19, desc, transform=ax.get_yaxis_transform(), ha="left", va="center",
                    fontsize=11.5, color=AWARD if awarded else MUTED, weight="bold" if awarded else "normal")
            ax.text(p + cfg["xmax"] / 60, i, f"{p:.1f}%", ha="left", va="center", fontsize=19 if first else 17,
                    weight="bold" if (first or awarded) else "normal", color=ink)
        for k, note in enumerate(cfg["notes"]):
            fig.text(0.065, (0.3 + 0.55 * (k_notes - 1 - k) + 0.25) / height, textwrap.fill(note, width=150),
                     fontsize=10.5, color=INK if k == 0 else MUTED, va="center")
        stem = OUT / f"{key}_2026_top5_vs_award"
        for suffix in ("png", "svg"):
            fig.savefig(stem.with_suffix(f".{suffix}"), dpi=200, facecolor="white")
        plt.close(fig)
        print(f"{stem.relative_to(ROOT)}.png / .svg")


if __name__ == "__main__":
    for k, c in FIELDS.items():
        draw(k, c)
