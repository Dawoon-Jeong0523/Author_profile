#!/usr/bin/env python3
"""analyze.py: per-field and pooled analysis of the Preseen runs (SPEC §11).

    $PY analyze.py field --field medicine          # results/<field>/*.csv, summary.json, figures, captions.md
    $PY analyze.py pooled                          # results/pooled/ (fields with treat runs)
    $PY analyze.py score --field medicine --option 3   # after the announcement only: log score of the realized option

Write-up term counts cover the final write-up and, separately ("sub: ..."), the four subforecast write-ups.
Reads the completed run JSONs in preseen_exp/<field>/runs/ (schema: results/<field>/schema.md), the question
(questions/<field>.json) and the committee list (committee/<field>/candidates.json). Probabilities are matched to the
question's options by exact text; options are numbered 1..K+1 in question order (K+1 = Other).
"""
import argparse
import itertools
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load((HERE / "config.yaml").read_text())
TERMS = {"percentile": r"percentile", "disruption": r"disrupt", "patent": r"patent|invention",
         "textbook/book": r"textbook|\bbooks?\b", "laureate": r"laureate", "co-author": r"co-?authors?",
         "supplied bibliometrics": r"bibliometric|user-provided|supplied (data|notes|profiles)|profile notes?|context notes?"}


def load(field):
    q = json.loads((HERE / "questions" / f"{field}.json").read_text())
    opts = q["options"]
    rows, subs, texts = [], [], []
    for f in sorted((HERE / "preseen_exp" / field / "runs").glob("*.json")):
        t = json.loads(f.read_text())
        if t.get("status") != "completed":
            continue
        arm, rep = f.name.split("_rep")[0], int(f.name.split("_rep")[1][:2])
        p = t["forecast"]["forecast_data"]["payload"]["probabilities"]
        if set(p) != set(opts):
            sys.exit(f"{f.name}: option texts differ from the question")
        for i, o in enumerate(opts, 1):
            rows.append({"arm": arm, "rep": rep, "task_id": t["id"], "created_at": t["created_at"], "option": i,
                         "p": p[o]})
        for s in t.get("subforecasts") or []:
            sp = s["forecast_data"]["payload"]["probabilities"]
            for i, o in enumerate(opts, 1):
                subs.append({"arm": arm, "rep": rep, "sub": s["sequence_index"], "option": i, "p": sp.get(o)})
        wu = t["forecast"].get("write_up") or ""
        sw = " ".join(s.get("write_up") or "" for s in t.get("subforecasts") or [])
        texts.append({"arm": arm, "rep": rep, "chars": len(wu), "n_sources": len(t["forecast"].get("sources") or []),
                      **{k: len(re.findall(v, wu, re.I)) for k, v in TERMS.items()},
                      **{f"sub: {k}": len(re.findall(v, sw, re.I)) for k, v in TERMS.items()}})
    return opts, pd.DataFrame(rows), pd.DataFrame(subs), pd.DataFrame(texts)


def card_strength(field, out):
    """Exploratory (not pre-specified): does an option's shift follow how its people compare with the field's
    laureates on their cards? Mean laureate share (impact median; citing inventions) of the shown people vs Δ."""
    import csv
    import build_cards as bc
    ref = pd.read_csv(HERE / "cards" / "laureate_reference.csv")
    L = ref[ref.field == field]

    def share(v, vals):
        vals = [x for x in vals if pd.notna(x)]
        return (sum(x < v for x in vals) + 0.5 * sum(x == v for x in vals)) / len(vals) if vals and v is not None else None
    ident = {r["person"]: r["openalex_ids"].split(";") for r in csv.DictReader(open(HERE / "people" / f"{field}_identity.csv"))}
    cand = json.loads((HERE / "committee" / field / "candidates.json").read_text())["options"][:-1]
    eff = pd.read_csv(out / "effects.csv")
    eff = eff[eff.arm == "treat"].set_index("option")
    rows = []
    for i, o in enumerate(cand, 1):
        mi, mv = [], []
        for p in o["people"]:
            m = bc.metrics(bc.find_profile(ident[p["name"]]))
            mi.append(share(m["impact_median"], L.impact_median.tolist()))
            mv.append(share(m["citing_inventions"], L.citing_inventions.tolist()))
        mi = [x for x in mi if x is not None]
        rows.append({"option": i, "impact_share": float(np.mean(mi)) if mi else None,
                     "inventions_share": float(np.mean(mv)), "diff": float(eff.loc[i, "diff"])})
    d = pd.DataFrame(rows)
    d.to_csv(out / "card_strength_vs_effect.csv", index=False)
    res = {}
    for x in ("impact_share", "inventions_share"):
        r = spearmanr(d[x], d["diff"], nan_policy="omit")
        res[x] = {"spearman": float(r.statistic), "p": float(r.pvalue), "n": int(d[x].notna().sum())}
    return res


def uptake_quotes(field, k=4):
    """Sentences of the treat subforecast write-ups that refer to the supplied bibliometrics (untrusted text, data)."""
    pat = re.compile(r"[^.\n]*(supplied bibliometric|user-provided bibliometric|bibliometrics? (were|was|are)|"
                     r"percentiles? among (previous|prior|past) laureates|profile notes?)[^.\n]*[.\n]", re.I)
    quotes = []
    for f in sorted((HERE / "preseen_exp" / field / "runs").glob("treat_*.json")):
        t = json.loads(f.read_text())
        for s in t.get("subforecasts") or []:
            for m in pat.finditer(s.get("write_up") or ""):
                q = re.sub(r"[*#`]+", "", m.group(0)).strip()
                if 40 <= len(q) <= 320 and q not in quotes:
                    quotes.append(q)
    return quotes[:k]


def entropy(p):
    p = np.asarray([x for x in p if x > 0])
    return float(-(p * np.log2(p)).sum())


def pairwise_abs(df):
    """Mean over options of the mean |p_a - p_b| over pairs of runs (run-to-run spread)."""
    vals = []
    for _, g in df.groupby("option"):
        x = g.p.tolist()
        if len(x) > 1:
            vals.append(np.mean([abs(a - b) for a, b in itertools.combinations(x, 2)]))
    return float(np.mean(vals)) if vals else None


def cmd_field(a):
    field = a.field
    out = HERE / "results" / field
    out.mkdir(parents=True, exist_ok=True)
    opts, runs, subs, texts = load(field)
    K1 = len(opts)
    runs.to_csv(out / "runs_long.csv", index=False)
    arms = sorted(runs.arm.unique(), key=lambda x: ["control", "treat", "shuffle"].index(x))
    by = runs.groupby(["arm", "option"]).p.agg(n="size", mean="mean", sd="std", min="min", max="max").reset_index()
    by["option_text"] = by.option.map(lambda i: opts[i - 1])
    by.to_csv(out / "by_option.csv", index=False)

    C = runs[runs.arm == "control"]
    summary = {"field": field, "runs": runs.groupby("arm").rep.nunique().to_dict(),
               "control_run_to_run_mean_abs_diff": pairwise_abs(C)}
    eff = []
    for arm in [x for x in arms if x != "control"]:
        T = runs[runs.arm == arm]
        for i in range(1, K1 + 1):
            c, t = C[C.option == i].p, T[T.option == i].p
            d = t.mean() - c.mean()
            eff.append({"arm": arm, "option": i, "control_mean": c.mean(), "control_sd": c.std(), "control_min": c.min(),
                        "control_max": c.max(), "arm_mean": t.mean(), "arm_sd": t.std(), "diff": d,
                        "diff_over_control_sd": d / c.std() if c.std() and c.std() > 0 else None,
                        "outside_control_range": bool(t.mean() < c.min() or t.mean() > c.max()),
                        "option_text": opts[i - 1]})
        e = pd.DataFrame([x for x in eff if x["arm"] == arm])
        cm = C.groupby("option").p.mean().sort_index()
        tm = T.groupby("option").p.mean().sort_index()
        rho = spearmanr(cm, tm).statistic
        ent = {k: float(np.mean([entropy(g.sort_values("option").p) for _, g in R.groupby("rep")]))
               for k, R in (("control", C), (arm, T))}
        summary[arm] = {"mean_abs_diff_vs_control": float(e["diff"].abs().mean()),
                        "options_outside_control_range": int(e.outside_control_range.sum()),
                        "other_control": float(cm.iloc[-1]), f"other_{arm}": float(tm.iloc[-1]),
                        "entropy_bits_control": ent["control"], f"entropy_bits_{arm}": ent[arm],
                        "spearman_rank_control_vs_arm": float(rho),
                        "rank_changes": {int(i): int(r2 - r1) for i, r1, r2 in
                                         zip(cm.index, cm.rank(ascending=False), tm.rank(ascending=False)) if r1 != r2}}
    pd.DataFrame(eff).to_csv(out / "effects.csv", index=False)

    if len(subs):
        sm = subs.groupby(["arm", "sub", "option"]).p.mean().reset_index()
        sm.to_csv(out / "subforecasts.csv", index=False)
        moved = {}
        for arm in [x for x in arms if x != "control"]:
            for s in sorted(subs["sub"].unique()):
                c = sm[(sm.arm == "control") & (sm["sub"] == s)].set_index("option").p
                t = sm[(sm.arm == arm) & (sm["sub"] == s)].set_index("option").p
                if len(c) and len(t):
                    moved[f"{arm}_sub{s}"] = float((t - c).abs().mean())
        summary["subforecast_mean_abs_diff"] = moved
    terms = texts.groupby("arm")[list(TERMS) + [f"sub: {k}" for k in TERMS] + ["chars", "n_sources"]].mean()
    terms.to_csv(out / "terms.csv")
    summary["writeup_term_means"] = terms.round(2).to_dict(orient="index")

    c1 = C[C.rep == 1].set_index("option").p
    later = C[C.rep > 1].groupby("option").p.mean()
    if len(later):
        summary["drift_control_rep1_vs_later_mean_abs_diff"] = float((later - c1).abs().mean())

    cand = json.loads((HERE / "committee" / field / "candidates.json").read_text())["options"][:-1]
    cm = C.groupby("option").p.mean()
    cvp = pd.DataFrame([{"option": i, "borda": o["score"], "n_models": o["n_models"], "consensus": o["consensus"],
                         "control_mean": cm.get(i)} for i, o in enumerate(cand, 1)])
    cvp.to_csv(out / "committee_vs_preseen.csv", index=False)
    summary["committee_vs_preseen"] = {
        "spearman_borda_vs_control": float(spearmanr(cvp.borda, cvp.control_mean).statistic),
        "spearman_n_models_vs_control": float(spearmanr(cvp.n_models, cvp.control_mean).statistic),
        "control_mean_cross_model_consensus": float(cvp[cvp.consensus == "cross-model consensus"].control_mean.mean()),
        "control_mean_single_model": float(cvp[cvp.consensus == "single-model"].control_mean.mean())
        if (cvp.consensus == "single-model").any() else None}
    if "treat" in summary:
        summary["exploratory_card_strength"] = card_strength(field, out)
        summary["uptake_quotes"] = uptake_quotes(field)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=float))
    figures(field, opts, runs, by, out)
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=float))


INK, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
ARM_STYLE = {"control": ("#2a78d6", "o"), "treat": ("#eb6834", "^"), "shuffle": ("#1baf7a", "s")}   # reference palette slots 1-3


def short(o, n=46):
    t = re.sub(r"^for (the|their|his|her) (discover(y|ies)|development|invention|theoretical prediction and experimental "
               r"(discovery|realization)) (of |concerning )?", "", o.split(" — ")[0])
    return t if len(t) <= n else t[: n - 1] + "…"


def _axes(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelcolor=INK, length=0, labelsize=8)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def figures(field, opts, runs, by, out):
    """Two PNGs; series identity and error-bar definitions are in captions.md (no in-figure legends)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    arms = [a for a in ("control", "treat", "shuffle") if a in set(runs.arm)]
    K1 = len(opts)
    labels = [f"{i}. {short(o)}" if o != CFG["question"]["other_option"] else f"{i}. Other" for i, o in enumerate(opts, 1)]
    off = {a: (k - (len(arms) - 1) / 2) * 0.22 for k, a in enumerate(arms)}

    fig, ax = plt.subplots(figsize=(8.5, 0.42 * K1 + 1.2), dpi=150, facecolor=SURFACE)
    _axes(ax)
    for a in arms:
        col, mk = ARM_STYLE[a]
        R = runs[runs.arm == a]
        ax.scatter(R.p, K1 - R.option + off[a], s=22, marker=mk, facecolors="none", edgecolors=col, linewidths=1.0, zorder=2)
        M = by[by.arm == a]
        ax.scatter(M["mean"], K1 - M.option + off[a], s=64, marker=mk, color=col, edgecolors=SURFACE, linewidths=1.5, zorder=3)
    ax.set_yticks(range(K1 - 1, -1, -1), labels)
    ax.set_xlabel("Probability", color=MUTED, fontsize=8)
    ax.set_xlim(0, runs.p.max() * 1.08)
    fig.tight_layout()
    fig.savefig(out / "option_probabilities.png", facecolor=SURFACE)
    plt.close(fig)

    figs = ["option_probabilities.png"]
    C = runs[runs.arm == "control"]
    for a in [x for x in arms if x != "control"]:
        T = runs[runs.arm == a]
        cg = C.groupby("option").p
        cm, cmin, cmax, tm = cg.mean(), cg.min(), cg.max(), T.groupby("option").p.mean()
        fig, ax = plt.subplots(figsize=(8.5, 0.42 * K1 + 1.2), dpi=150, facecolor=SURFACE)
        _axes(ax)
        y = K1 - cm.index.values
        ax.barh(y, (cmax - cmin).values, left=(cmin - cm).values, height=0.5, color=GRID, zorder=1)
        ax.axvline(0, color=AXIS, linewidth=1, zorder=1)
        col, mk = ARM_STYLE[a]
        ax.scatter((tm - cm).values, y, s=64, marker=mk, color=col, edgecolors=SURFACE, linewidths=1.5, zorder=3)
        ax.set_yticks(range(K1 - 1, -1, -1), labels)
        ax.set_xlabel(f"{a} minus control (probability)", color=MUTED, fontsize=8)
        fig.tight_layout()
        name = f"{a}_minus_control.png"
        fig.savefig(out / name, facecolor=SURFACE)
        plt.close(fig)
        figs.append(name)

    n = runs.groupby("arm").rep.nunique().to_dict()
    cap = [f"# Figure captions — {CFG['fields'][field]['prize']}", "",
           "## option_probabilities.png", "",
           "Forecast probability of each option (rows, in question order; labels shortened, full texts in "
           "questions/" + field + ".json). " + "; ".join(
               f"{a}: {'blue circles' if a == 'control' else 'orange triangles' if a == 'treat' else 'green squares'} "
               f"(n = {n[a]} runs)" for a in arms) + ". Small hollow markers = individual runs; large filled marker = "
           "mean over runs. Arms are offset vertically within a row.", ""]
    for name in figs[1:]:
        a = name.split("_minus")[0]
        cap += [f"## {name}", "", f"Difference between the mean {a} probability and the mean control probability per "
                f"option (orange triangle). Grey bar = the control arm's run-to-run range (min to max over the {n['control']} "
                "control runs), centred on the control mean (0); a difference outside the grey bar is larger than the "
                "spread between control runs.", ""]
    (out / "captions.md").write_text("\n".join(cap))


def cmd_pooled(a):
    out = HERE / "results" / "pooled"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for field in CFG["order"]:
        p = HERE / "results" / field / "summary.json"
        if not p.exists():
            continue
        s = json.loads(p.read_text())
        if "treat" not in s:
            continue
        t = s["treat"]
        rows.append({"field": field, "control_run_to_run": s["control_run_to_run_mean_abs_diff"],
                     "treat_vs_control": t["mean_abs_diff_vs_control"],
                     "other_change": t["other_treat"] - t["other_control"],
                     "entropy_change": t["entropy_bits_treat"] - t["entropy_bits_control"],
                     "spearman": t["spearman_rank_control_vs_arm"], "outside_range": t["options_outside_control_range"]})
    df = pd.DataFrame(rows)
    df.to_csv(out / "pooled.csv", index=False)
    print(df.to_string(index=False))


def cmd_score(a):
    opts, runs, _, _ = load(a.field)
    r = runs[runs.option == a.option].assign(log_score=lambda d: np.log(d.p))
    s = r.groupby("arm").log_score.agg(["mean", "std", "size"])
    out = HERE / "results" / a.field / "log_score.csv"
    s.to_csv(out)
    print(f"realized option {a.option}: {opts[a.option - 1]}\n{s}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("field"); s.add_argument("--field", required=True)
    sub.add_parser("pooled")
    s = sub.add_parser("score"); s.add_argument("--field", required=True); s.add_argument("--option", type=int, required=True)
    a = ap.parse_args()
    {"field": cmd_field, "pooled": cmd_pooled, "score": cmd_score}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
