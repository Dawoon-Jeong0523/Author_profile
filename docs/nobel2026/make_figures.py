#!/usr/bin/env python3
"""make_figures.py: README figures of the 2026 Nobel forecasts, top 5 against the award.

    $PY docs/nobel2026/make_figures.py      # -> docs/nobel2026/{medicine,physics}_2026_top5_vs_award.{png,svg},
                                            #    docs/nobel2026/chemistry_2026_top5_{main3,one_main_source,cards_context}.{png,svg}; the same files
                                            #    also in Data/Result/{Medicine,Physics,Chemistry}/

Data: Data/Result/nobel_chemistry_2026_main3.csv (the 6 October forecast with the cards as the main evidence, arm main3 in the run files),
Data/Result/nobel_medicine_2026_cards_main_evidence.csv (the 2 October run with the profile cards as the main
evidence, 12 discoveries + Other, as on the public dashboard) and Data/Result/nobel_physics_2026_probabilities.csv (the
5 October final forecast, 30 discoveries). The
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
        "csv": "nobel_medicine_2026_cards_main_evidence.csv",
        "title": "2026 Nobel Prize in Physiology or Medicine",
        "subtitle": "Cards as the main evidence: top 5 of 12 named discoveries (Other 40.0 %)",
        "awarded": [1],                       # optogenetics
        "award_tag": "awarded discovery",
        "xmax": 10,
        "notes": ["Awarded 5 Oct 2026: Karl Deisseroth, Peter Hegemann and Georg Nagel, for light-gated ion channels and "
                  "optogenetics (the option named Miesenböck instead of Nagel; options are matched by discovery). "
                  "\"Other\" (a discovery not listed) received 40.0 %.",
                  "Cards as the main evidence: Preseen, 2 Oct 2026, 12 discoveries + Other (arm 4 of "
                  "the public dashboard)."],
    },
    "chemistry": {
        "csv": "nobel_chemistry_2026_main3.csv",
        "stem": "chemistry_2026_top5_main3",
        "title": "2026 Nobel Prize in Chemistry",
        "subtitle": "Cards as the main evidence: top 5 of 30 discoveries, and the awarded discovery",
        "awarded": [],                        # 7 Oct 2026: not among the options (see "unlisted")
        "award_tag": "awarded discovery",
        "xmax": 10,
        "unlisted": {"label": "Kagan · Soai", "discovery": "Non-linear effects and autocatalysis in asymmetric synthesis",
                     "value": "not among the 30 options"},
        "notes": ["Awarded 7 Oct 2026: Henri B. Kagan and Kenso Soai, for the discovery of non-linear effects and autocatalysis in "
                  "asymmetric organic synthesis. It was not among the 30 listed discoveries, so this forecast (Preseen, 6 Oct 2026, one run) is annulled.",
                  "Question: 30 discoveries from the virtual committee and convergence signals, each with the living people "
                  "of its best-scoring committee lineup (v2); profile cards with the patents tied to each discovery as the "
                  "main evidence, every card measure treated as important."],
    },
    "chemistry_one_main_source": {
        "csv": "nobel_chemistry_2026_one_main_source.csv",
        "stem": "chemistry_2026_top5_one_main_source",
        "folder": "Chemistry",
        "title": "2026 Nobel Prize in Chemistry",
        "subtitle": "Cards as one main source: top 5 of 30 discoveries, and the awarded discovery",
        "awarded": [],
        "award_tag": "awarded discovery",
        "xmax": 15,
        "unlisted": {"label": "Kagan · Soai", "discovery": "Non-linear effects and autocatalysis in asymmetric synthesis",
                     "value": "not among the 30 options"},
        "notes": ["Awarded 7 Oct 2026: Henri B. Kagan and Kenso Soai, for the discovery of non-linear effects and autocatalysis in "
                  "asymmetric organic synthesis. It was not among the 30 listed discoveries, so this forecast (Preseen, 6 Oct 2026, one run) is annulled.",
                  "The profile cards (with the patents tied to each discovery) are one of the main sources, weighed "
                  "comparably with prizes, news, predictions and the history of the prize; same question, reference notes "
                  "and cards as the main-evidence forecast."],
    },
    "chemistry_context": {
        "csv": "nobel_chemistry_2026_cards_context.csv",
        "stem": "chemistry_2026_top5_cards_context",
        "folder": "Chemistry",
        "title": "2026 Nobel Prize in Chemistry",
        "subtitle": "Cards as context: top 5 of 30 discoveries, and the awarded discovery",
        "awarded": [],
        "award_tag": "awarded discovery",
        "xmax": 25,
        "unlisted": {"label": "Kagan · Soai", "discovery": "Non-linear effects and autocatalysis in asymmetric synthesis",
                     "value": "not among the 30 options"},
        "notes": ["Awarded 7 Oct 2026: Henri B. Kagan and Kenso Soai, for the discovery of non-linear effects and autocatalysis in "
                  "asymmetric organic synthesis. It was not among the 30 listed discoveries, so this forecast (Preseen, 6 Oct 2026, one run) is annulled.",
                  "The profile cards (with the patents tied to each discovery) and the reference notes are given with no "
                  "instruction on how to use them; same question, reference notes and cards as the main-evidence forecast."],
    },
    "physics": {
        "csv": "nobel_physics_2026_probabilities.csv",
        "title": "2026 Nobel Prize in Physics",
        "subtitle": "Cards as the main evidence: top 5 of 30 discoveries, and the awarded discovery",
        "awarded": [14],                      # high-energy cosmic neutrinos
        "award_tag": "awarded discovery",
        "xmax": 10,
        "notes": ["Awarded 6 Oct 2026: Francis Halzen alone, for the IceCube Neutrino Observatory and the discovery of "
                  "high-energy neutrinos of astrophysical origin (the option named Halzen, Karle and Kurahashi Neilson).",
                  "Cards as the main evidence: Preseen, 5 Oct 2026, conditional on one of the 30 "
                  "listed discoveries."],
    },
}


def draw(key, cfg):
    df = pd.read_csv(DATA / cfg["csv"], encoding="utf-8-sig").dropna(subset=["rank"]).sort_values("rank")
    df["rank"] = df["rank"].astype(int)                  # "Other" (no rank) is stated in the subtitle
    top = df.head(TOP_N)
    extra = df[df["rank"].isin(cfg["awarded"]) & (df["rank"] > TOP_N)]
    rows = list(top.itertuples()) + ([None] if len(extra) else []) + list(extra.itertuples())
    if cfg.get("unlisted"):                              # an award outside the listed options: its own row, no bar
        rows += [None, "unlisted"]
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
            if r == "unlisted":
                u = cfg["unlisted"]
                ax.text(-1.11, i - 0.12, f"—  {u['label']}   ◀ {cfg['award_tag']}", transform=ax.get_yaxis_transform(),
                        ha="left", va="center", fontsize=15.5, weight="bold", color=AWARD)
                ax.text(-1.11, i + 0.19, u["discovery"], transform=ax.get_yaxis_transform(), ha="left", va="center",
                        fontsize=11.5, color=AWARD, weight="bold")
                ax.text(cfg["xmax"] / 60, i, u["value"], ha="left", va="center", fontsize=15, color=AWARD,
                        style="italic")
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
        name = cfg.get("stem", f"{key}_2026_top5_vs_award")
        for folder in (OUT, DATA / cfg.get("folder", key.capitalize())):   # README copy and the field's Data/Result folder
            folder.mkdir(exist_ok=True)
            for suffix in ("png", "svg"):
                fig.savefig(folder / f"{name}.{suffix}", dpi=200, facecolor="white")
            print(f"{(folder / name).relative_to(ROOT)}.png / .svg")
        plt.close(fig)


if __name__ == "__main__":
    for k, c in FIELDS.items():
        draw(k, c)
