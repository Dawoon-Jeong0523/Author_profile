#!/usr/bin/env python3
"""make_figures.py: README figures of the 2026 Nobel forecasts, top 5 against the award.

    $PY docs/nobel2026/make_figures.py      # -> docs/nobel2026/{medicine,physics}_2026_top5_vs_award.{png,svg},
                                            #    chemistry_2026_top5_main3, chemistry_2026_arms (all 30, three arms)

Data: Data/Result/nobel_chemistry_2026_main3.csv (the 6 October main3 run, 30 discoveries, v2 list),
Data/Result/nobel_medicine_2026_cards_main_evidence.csv (the 2 October run with the profile cards as the main
evidence, 12 discoveries + Other, as on the public dashboard) and Data/Result/nobel_physics_2026_probabilities.csv (the
5 October final forecast, 30 discoveries). The
layout follows Data/Result/Figure_Nobel.ipynb (same header, colours and row geometry); added here: the awarded
discovery is drawn in a second accent colour and, when it is outside the top 5, shown below a gap with its rank.
chemistry_2026_arms: the 30 discoveries of the v2 list with three bars each (main3, demographic, control), from the
control_pct and demographic_pct columns of the chemistry CSV.
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
        "csv": "nobel_medicine_2026_cards_main_evidence.csv",
        "title": "2026 Nobel Prize in Physiology or Medicine",
        "subtitle": "Profile cards as the main evidence: top 5 of 12 named discoveries (Other 40.0 %)",
        "awarded": [1],                       # optogenetics
        "award_tag": "awarded discovery",
        "xmax": 10,
        "notes": ["Awarded 5 Oct 2026: Karl Deisseroth, Peter Hegemann and Georg Nagel, for light-gated ion channels and "
                  "optogenetics (the option named Miesenböck instead of Nagel; options are matched by discovery). "
                  "\"Other\" (a discovery not listed) received 40.0 %.",
                  "Forecast: Preseen, 2 Oct 2026, 12 discoveries + Other, profile cards as the main evidence (arm 4), "
                  "the run shown on the public dashboard."],
    },
    "chemistry": {
        "csv": "nobel_chemistry_2026_main3.csv",
        "stem": "chemistry_2026_top5_main3",
        "title": "2026 Nobel Prize in Chemistry",
        "subtitle": "Profile cards as the main evidence (main3): top 5 of 30 discoveries, before the announcement",
        "awarded": [],                        # announced 7 Oct 2026
        "award_tag": "awarded discovery",
        "xmax": 10,
        "notes": ["To be announced on 7 Oct 2026. The same question without any notes put sequencing-by-synthesis first (17.3 %, "
                  "3.5 % here); with demographic information added, the top three stayed (8.8 %, 6.5 %, 6.2 %).",
                  "Forecast: Preseen, 6 Oct 2026, 30 discoveries (committee + convergence, v2 lineups); cards with the "
                  "patents tied to each discovery; every card measure treated as important evidence."],
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
    df = pd.read_csv(DATA / cfg["csv"], encoding="utf-8-sig").dropna(subset=["rank"]).sort_values("rank")
    df["rank"] = df["rank"].astype(int)                  # "Other" (no rank) is stated in the subtitle
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
        stem = OUT / cfg.get("stem", f"{key}_2026_top5_vs_award")
        for suffix in ("png", "svg"):
            fig.savefig(stem.with_suffix(f".{suffix}"), dpi=200, facecolor="white")
        plt.close(fig)
        print(f"{stem.relative_to(ROOT)}.png / .svg")


ARMS = [("probability_pct_reported", "main3: profile cards as the main evidence, every card measure important", ACCENT),
        ("demographic_pct", "demographic: main3 + the demographics of past laureates", "#7C6BB0"),
        ("control_pct", "control: the question only, no notes", "#B4C2CB")]


def draw_arms():
    df = pd.read_csv(DATA / "nobel_chemistry_2026_main3.csv", encoding="utf-8-sig").sort_values("rank")
    n, pitch, xmax = len(df), 0.66, 18
    head, foot = 2.75, 1.55
    height = head + pitch * n + foot
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none"}):
        fig = plt.figure(figsize=(14, height), facecolor="white")
        fig.text(0.065, 1 - 0.34 / height, "KNOWLEDGE LAB + PRESEEN", fontsize=12, weight="bold", color=ACCENT, va="top")
        fig.text(0.065, 1 - 0.72 / height, "2026 Nobel Prize in Chemistry: three forecasts", fontsize=25, weight="bold",
                 color=INK, va="top")
        fig.text(0.065, 1 - 1.28 / height, "The same 30 discoveries and named people (v2 list), sorted by main3; "
                 "Preseen, 6 Oct 2026, one run each", fontsize=13.5, color=MUTED, va="top")
        for k, (_, label, color) in enumerate(ARMS):
            y = 1 - (1.78 + 0.3 * k) / height
            fig.patches.append(plt.Rectangle((0.065, y - 0.06 / height), 0.016, 0.14 / height, color=color,
                                             transform=fig.transFigure, figure=fig))
            fig.text(0.088, y, label, fontsize=12, color=INK, va="center")
        ax = fig.add_axes([0.515, foot / height, 0.405, (pitch * n) / height])
        ax.set_ylim(n - 0.5, -0.5)
        ax.set_xlim(0, xmax)
        ax.set_xticks(range(0, xmax + 1, 2))
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.tick_params(axis="x", length=0, pad=7, labelsize=11, colors=MUTED, labeltop=True)
        ax.set_yticks([])
        ax.grid(axis="x", color="#E4E9EC", linewidth=0.8, zorder=0)
        for s_ in ax.spines.values():
            s_.set_visible(False)
        for i, r in enumerate(df.itertuples()):
            if i % 2 == 0:
                ax.axhspan(i - 0.5, i + 0.5, xmin=-1.14, xmax=1.12, color="#F5F7F8", zorder=0, clip_on=False)
            for k, (col, _, color) in enumerate(ARMS):
                p, y = float(getattr(r, col)), i + (k - 1) * 0.27
                ax.barh(y, p, height=0.24, color=color, zorder=3)
                ax.text(p + 0.15, y, f"{p:.1f}", ha="left", va="center", fontsize=9, color=INK if k == 0 else MUTED,
                        weight="bold" if k == 0 else "normal", zorder=4)
            ax.text(-1.11, i - 0.13, f"{int(r.rank):02d}  {r.plot_label}", transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=12.5, color=INK, weight="bold" if r.rank == 1 else "normal")
            ax.text(-1.11, i + 0.2, textwrap.shorten(str(r.discovery_short), width=72, placeholder="…"),
                    transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=10.5, color=MUTED)
        notes = ["To be announced on 7 Oct 2026. Without notes, the forecaster backed the prize favourite "
                 "(sequencing-by-synthesis, 17.3 %); with the cards as the main evidence it fell to 3.5 % and "
                 "probability moved to proteomics, self-assembled monolayers and dye-sensitized solar cells.",
                 "Differences of about one point are within the run-to-run spread. Prompts and cards: README, "
                 "\"What changed between versions\" (main3 = P5 with K1 + K3 cards; demographic = P6; control = P0)."]
        for k, note in enumerate(notes):
            fig.text(0.065, (1.02 - 0.5 * k) / height, textwrap.fill(note, width=150), fontsize=10.5,
                     color=INK if k == 0 else MUTED, va="center")
        stem = OUT / "chemistry_2026_arms"
        for suffix in ("png", "svg"):
            fig.savefig(stem.with_suffix(f".{suffix}"), dpi=170, facecolor="white")
        plt.close(fig)
        print(f"{stem.relative_to(ROOT)}.png / .svg")


if __name__ == "__main__":
    for k, c in FIELDS.items():
        draw(k, c)
    draw_arms()
