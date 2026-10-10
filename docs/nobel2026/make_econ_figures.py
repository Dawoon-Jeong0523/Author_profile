#!/usr/bin/env python3
"""make_econ_figures.py: README figures of the 2026 economics forecast, treatment against control.

    $PY docs/nobel2026/make_econ_figures.py     # -> docs/nobel2026/economics_2026_{fields,people}_top5.{png,svg}
                                                #    (+ copies and the data CSVs in Data/Result/Economics/)

Each figure shows the top five options of the treatment arm with the control's probability beside it, then the
control's own top-five options that are outside the treatment's top five (below a gap, with their treatment rank).
Data: the Preseen run files of Econ/04_field_forecast/preseen_exp/fields14_nobel (field question, title "... Nobel
Prize in Economic Sciences ...") and Econ/07_people_forecast/preseen_exp/people30 (people question; skipped until both
arms are complete). Layout and ink colours follow make_figures.py; the two arm colours (teal #00876f treatment, violet
#6250d6 control) pass the dataviz palette validator (lightness, chroma, CVD and normal-vision separation, contrast).
"""
import json
import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ECON = ROOT / "Econ"
DATA = ROOT / "Data" / "Result" / "Economics"
OUT = Path(__file__).resolve().parent
INK, MUTED, BRAND, GRID = "#172F40", "#556773", "#087F74", "#E4E9EC"
TREAT, CONTROL = "#00876f", "#6250d6"
TOP_N = 5


def load_runs(run_dir):
    """{arm: {option: probability in %}} from the Preseen run files of one question; None unless both arms completed."""
    out = {}
    for f in sorted((run_dir / "runs").glob("*.json")):
        d = json.loads(f.read_text())
        if d.get("status") != "completed" or not d.get("forecast"):
            return None
        arm = "control" if f.name.startswith("control_") else "treatment"
        p = d["forecast"]["forecast_data"]["payload"]["probabilities"]
        t = sum(p.values())
        out[arm] = {k: 100 * v / t for k, v in p.items()}
    return out if set(out) == {"control", "treatment"} else None


def table(runs):
    df = pd.DataFrame(runs).reset_index().rename(columns={"index": "option"})
    df["treatment_rank"] = df["treatment"].rank(ascending=False, method="first").astype(int)
    df["control_rank"] = df["control"].rank(ascending=False, method="first").astype(int)
    return df.sort_values("treatment_rank").reset_index(drop=True)


def hbar(ax, y, w, h, color, r_px=6.0):
    """Horizontal bar with a rounded data end and a square baseline (corner radius r_px display pixels)."""
    if w <= 0:
        return
    fig = ax.figure
    fig.canvas.draw_idle()
    bb = ax.get_window_extent()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    rx = r_px * (x1 - x0) / bb.width
    ry = r_px * abs(y1 - y0) / bb.height
    rx = min(rx, w / 2)
    ry = min(ry, h / 2)
    ax.add_patch(FancyBboxPatch((0, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={rx}",
                                mutation_aspect=ry / rx, facecolor=color, edgecolor="none", zorder=3))
    ax.add_patch(Rectangle((0, y - h / 2), min(rx, w), h, facecolor=color, edgecolor="none", zorder=3))


def draw(stem, title, subtitle, rows, xmax, notes, legend):
    """rows: list of dicts (label, sub, treatment, control, rank) or None for the gap row."""
    n = len(rows)
    k_notes = len(notes)
    foot = 0.3 + 0.55 * k_notes + 0.6
    height = 2.35 + 1.0 * n + foot
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.fonttype": "none"}):
        fig = plt.figure(figsize=(14, height), facecolor="white")
        fig.text(0.065, 1 - 0.34 / height, "KNOWLEDGE LAB + PRESEEN", fontsize=12, weight="bold", color=BRAND, va="top")
        fig.text(0.065, 1 - 0.72 / height, title, fontsize=25, weight="bold", color=INK, va="top")
        fig.text(0.065, 1 - 1.28 / height, subtitle, fontsize=13.5, color=MUTED, va="top")
        handles = [Patch(facecolor=TREAT, label=legend[0]), Patch(facecolor=CONTROL, label=legend[1])]
        fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.515, 1 - 1.72 / height), ncol=2, frameon=False,
                   fontsize=12, labelcolor=INK, handlelength=1.4, handleheight=0.9, columnspacing=2.2)
        bottom = foot / height
        ax = fig.add_axes([0.515, bottom, 0.405, (1.0 * n - 0.05) / height])
        ax.set_ylim(n - 0.45, -0.6)
        ax.set_xlim(0, xmax)
        ax.set_xticks(range(0, xmax + 1, 5))
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
        ax.tick_params(axis="x", length=0, pad=9, labelsize=11, colors=MUTED)
        ax.set_yticks([])
        ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
        for s in ax.spines.values():
            s.set_visible(False)
        h, gap = 0.3, 0.04
        for i, r in enumerate(rows):
            if r is None:
                ax.text(-1.11, i - 0.05, "···", transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=18, color=MUTED)
                ax.text(-1.03, i - 0.05, "the control's own top five, outside the treatment's top five", transform=ax.get_yaxis_transform(),
                        ha="left", va="center", fontsize=11.5, color=MUTED, style="italic")
                continue
            first = r["rank"] == 1
            ax.text(-1.11, i - 0.12, f"{r['rank']:02d}  {r['label']}", transform=ax.get_yaxis_transform(), ha="left", va="center",
                    fontsize=15.5, weight="bold" if first else "normal", color=INK)
            ax.text(-1.11, i + 0.19, r["sub"], transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=11.5, color=MUTED)
            yt, yc = i - (h + gap) / 2, i + (h + gap) / 2
            hbar(ax, yt, r["treatment"], h, TREAT)
            hbar(ax, yc, r["control"], h, CONTROL)
            ax.text(r["treatment"] + xmax / 70, yt, f"{r['treatment']:.1f}%", ha="left", va="center", fontsize=15,
                    weight="bold", color=INK)
            ax.text(r["control"] + xmax / 70, yc, f"{r['control']:.1f}%", ha="left", va="center", fontsize=13, color=INK)
        for k, note in enumerate(notes):
            fig.text(0.065, (0.3 + 0.55 * (k_notes - 1 - k) + 0.25) / height, textwrap.fill(note, width=150),
                     fontsize=10.5, color=INK if k == 0 else MUTED, va="center")
        for folder in (OUT, DATA):
            folder.mkdir(parents=True, exist_ok=True)
            for suffix in ("png", "svg"):
                fig.savefig(folder / f"{stem}.{suffix}", dpi=200, facecolor="white")
            print(f"{(folder / stem).relative_to(ROOT)}.png / .svg")
        plt.close(fig)


def rows_for(df, label, sub):
    top = df[df.treatment_rank <= TOP_N]
    extra = df[(df.control_rank <= TOP_N) & (df.treatment_rank > TOP_N)].sort_values("control_rank")
    rows = [dict(label=label(r), sub=sub(r), treatment=r.treatment, control=r.control, rank=r.treatment_rank) for r in top.itertuples()]
    if len(extra):
        rows.append(None)
        rows += [dict(label=label(r), sub=f"{sub(r)} · control #{r.control_rank}", treatment=r.treatment, control=r.control,
                      rank=r.treatment_rank) for r in extra.itertuples()]
    return rows


def fields_figure():
    runs = load_runs(ECON / "04_field_forecast" / "preseen_exp" / "fields14_nobel")
    df = table(runs)
    hist = pd.read_csv(ECON / "04_field_forecast" / "results" / "preseen_fields14_results.csv").set_index("field")
    df["field"] = df.option.str.split(" \\(JEL").str[0]
    df["jel"] = df.option.str.extract(r"\(JEL ([^)]*)\)")[0]
    df["years_since_last"] = df.field.map(hist["years since last"]).astype(int)
    df[["field", "jel", "years_since_last", "treatment", "control", "treatment_rank", "control_rank"]].to_csv(
        DATA / "nobel_economics_2026_fields.csv", index=False, float_format="%.2f")
    rows = rows_for(df, lambda r: r.field, lambda r: f"JEL {r.jel} · last awarded {2026 - r.years_since_last} ({r.years_since_last} years before 2026)")
    draw("economics_2026_fields_top5", "2026 Nobel Prize in Economic Sciences",
         "Field forecast: top 5 of 14 fields of economics, treatment against control", rows, 20,
         ["Treatment: nine context notes on the award record (field rotation applied strongly, maturity of unawarded work, "
          "recent prizes, the 2026 committee), all as assumed true. Control: the same question with no context.",
          "Preseen, 10 Oct 2026, one run per arm. Question: \"Which field of economics will the 2026 Nobel Prize in Economic "
          "Sciences recognize?\", 14 fields defined by JEL code groups (Dolton and Tol 2026), no \"Other\"."],
         ("Treatment (context notes)", "Control (no context)"))


SHORT = {   # first words of the option's contribution -> short label for the figure (the full text is in the CSV)
    "for developing structural methods for the empirical analysis of demand": "Structural demand and market-power estimation",
    "for developing the New Keynesian framework": "New Keynesian monetary economics",
    "for the analysis of firm heterogeneity": "Firm heterogeneity in international trade",
    "for the welfare economics of sustainability": "Sustainability, natural capital, wealth accounting",
    "for showing how credit constraints and collateral": "Credit constraints and collateral in fluctuations",
    "for founding the micro-founded intertemporal new open-economy": "New open-economy macroeconomics",
    "for developing quantitative Ricardian": "Quantitative Ricardian trade models",
    "for linking optimal tax and social insurance": "Sufficient statistics for tax and insurance",
    "for the theory of general equilibrium with incomplete markets": "General equilibrium with incomplete markets",
    "for measuring management practices": "Management practices and productivity",
    "for the analysis of how political institutions": "Political institutions and economic policy",
    "for the analysis of endogenous sunk costs": "Sunk costs and market structure",
    "for the formulation and analysis of rules for monetary policy": "Monetary policy rules, staggered contracts",
    "for the empirical analysis of health insurance": "Health and social insurance design",
    "for the theory of equality of opportunity": "Equality of opportunity and fairness",
    "for the measurement of top incomes": "Top incomes and wealth from tax records",
    "for the development of heterogeneous-agent": "Heterogeneous-agent macroeconomics",
    "for the analysis of the structure, regularity and limits of general equilibrium": "Structure and limits of general equilibrium",
    "for the analysis of innovation, growth and the political economy of trade": "Trade policy, innovation and growth",
    "for the empirical analysis of productivity dispersion": "Productivity dispersion and reallocation",
    "for the empirical analysis of the local labor-market effects": "Local labour-market effects of imports",
    "for the narrative identification": "Narrative identification of policy effects",
    "for the analysis of offshoring": "Offshoring and global value chains",
    "for the economic analysis of law": "Economic analysis of law",
    "for the empirical analysis of entry and competition": "Entry and competition in concentrated markets",
    "for the analysis of public debt": "Public debt and Ricardian equivalence",
    "for the theoretical foundation of structural gravity": "Structural gravity and trade costs",
    "for the intertemporal analysis of consumption": "Consumption under rational expectations",
    "for showing how legal origins": "Legal origins and investor protection",
    "for the theory of two-sided markets": "Two-sided markets and platforms",
}
FIELD_SHORT = {"Macro": "Macro", "Trade": "Trade", "Production, Industrial Organization": "Production/IO",
               "Public, Law, Political Economy": "Public", "Equilibrium, Welfare": "Equilibrium"}


def short_contribution(m):
    for k, v in SHORT.items():
        if m.startswith(k):
            return v
    m = re.sub(r"^for (the |their |his |her )?", "", m)
    return textwrap.shorten(m[0].upper() + m[1:], width=46, placeholder="…")


def people_figure():
    runs = load_runs(ECON / "07_people_forecast" / "preseen_exp" / "people30")
    if runs is None:
        print("people question: runs not complete yet; figure skipped")
        return
    df = table(runs)
    parts = df.option.str.extract(r"^(.*) — (.*) \((.*)\)$")
    df["contribution"], df["people"], df["field"] = parts[0], parts[1], parts[2]
    surname = lambda n: n.split()[-1] if not n.endswith("Jr.") else n.split()[-2]
    df["people_short"] = df.people.map(lambda s: " · ".join(surname(x.strip()) for x in s.split(",")))
    df[["field", "people", "contribution", "treatment", "control", "treatment_rank", "control_rank"]].to_csv(
        DATA / "nobel_economics_2026_people.csv", index=False, float_format="%.2f")
    xmax = int(5 * (max(df.treatment.max(), df.control.max()) // 5 + 1))
    rows = rows_for(df, lambda r: r.people_short, lambda r: f"{short_contribution(r.contribution)} · {FIELD_SHORT[r.field]}")
    draw("economics_2026_people_top5", "2026 Nobel Prize in Economic Sciences",
         "Who: top 5 of 30 candidates from the five leading fields, treatment against control", rows, xmax,
         ["Treatment: 14 context notes (field forecast, age record, awarded prizes, candidates with defining works, the virtual "
          "committee's support and reasoning), all as assumed true. Control: the same question with no context.",
          "Preseen, 10 Oct 2026, one run per arm. 30 candidates nominated by a virtual committee (personas of the 2026 committee "
          "members on three language models) in the five leading fields of the field forecast; conditional on one of them, no \"Other\"."],
         ("Treatment (context notes)", "Control (no context)"))


if __name__ == "__main__":
    fields_figure()
    people_figure()
