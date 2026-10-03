#!/usr/bin/env python3
"""analyze_main.py: the "cards as main evidence" follow-up against the runs of ../preseen/ (SPEC.md, Analysis).

    $PY analyze_main.py field --field medicine     # results/<field>/*.csv, summary.json
    $PY analyze_main.py pooled                     # results/pooled.csv
    $PY analyze_main.py score --field medicine --option 3   # after the announcement only: log score per arm

Arms (the run JSONs are read where the two experiments saved them):
    control  ../preseen/preseen_exp/<field>/runs/control_*  (1 Oct, 4 runs) + preseen_exp/<field>/runs/control_*  (2 Oct, 1 run)
    cards    ../preseen/preseen_exp/<field>/runs/treat_*    (1 Oct, 3 runs; cards with treatment=consider)
    main     preseen_exp/<field>/runs/treat_*               (2 Oct, 1 run; instruction note + the same cards)
    balanced ../preseen_cards_balanced/preseen_exp/<field>/runs/treat_*  (2 Oct, 1 run; "one of the main sources" note
             + the same cards); optional, the tables gain its columns once its run has completed
Probabilities are matched to the question's options by exact text; options are numbered 1..13 in question order (13 = Other).
"""
import argparse
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "preseen"
FIELDS = ["medicine", "physics", "chemistry"]
ARMS = ["control", "cards", "balanced", "main"]
COL = {"cards": "cards_mean", "balanced": "balanced_p", "main": "main_p"}
DIFF = {"cards": "diff_cards", "balanced": "diff_balanced", "main": "diff_main"}
BAL = HERE.parent / "preseen_cards_balanced"
TERMS = {"percentile": r"percentile", "disruption": r"disrupt", "patent": r"patent|invention",
         "textbook/book": r"textbook|\bbooks?\b", "laureate": r"laureate", "co-author": r"co-?authors?",
         "supplied bibliometrics": r"bibliometric|user-provided|supplied (data|notes|profiles)|profile notes?|context notes?",
         "premise": r"premise|assumption"}
SOURCES = [("control", BASE, "control", "1 Oct"), ("cards", BASE, "treat", "1 Oct"),
           ("control", HERE, "control", "2 Oct"), ("main", HERE, "treat", "2 Oct"), ("balanced", BAL, "treat", "2 Oct")]


def load(field):
    """Runs of all arms: long table of probabilities, subforecasts, write-up term counts, write-ups."""
    opts = json.loads((HERE / "questions" / f"{field}.json").read_text())["options"]
    rows, subs, texts, wus = [], [], [], []
    rep = {}
    for arm, root, prefix, batch in SOURCES:
        for f in sorted((root / "preseen_exp" / field / "runs").glob(f"{prefix}_rep*.json")):
            t = json.loads(f.read_text())
            if t.get("status") != "completed":
                continue
            rep[arm] = rep.get(arm, 0) + 1
            k = rep[arm]
            p = t["forecast"]["forecast_data"]["payload"]["probabilities"]
            if set(p) != set(opts):
                sys.exit(f"{f}: option texts differ from the question")
            for i, o in enumerate(opts, 1):
                rows.append({"arm": arm, "rep": k, "batch": batch,                      # no Preseen ids in outputs
                             "created_at": t["created_at"], "option": i, "p": p[o]})
            for s in t.get("subforecasts") or []:
                sp = s["forecast_data"]["payload"]["probabilities"]
                for i, o in enumerate(opts, 1):
                    subs.append({"arm": arm, "rep": k, "sub": s["sequence_index"], "option": i, "p": sp.get(o)})
            wu = t["forecast"].get("write_up") or ""
            sw = " ".join(s.get("write_up") or "" for s in t.get("subforecasts") or [])
            texts.append({"arm": arm, "rep": k, "chars": len(wu), "n_sources": len(t["forecast"].get("sources") or []),
                          **{k2: len(re.findall(v, wu, re.I)) for k2, v in TERMS.items()},
                          **{f"sub: {k2}": len(re.findall(v, sw, re.I)) for k2, v in TERMS.items()}})
            wus.append({"arm": arm, "rep": k, "batch": batch, "created_at": t["created_at"], "write_up": wu,
                        "sub_write_ups": [s.get("write_up") or "" for s in sorted(t.get("subforecasts") or [],
                                                                                    key=lambda s: s["sequence_index"])]})
    return opts, pd.DataFrame(rows), pd.DataFrame(subs), pd.DataFrame(texts), wus


def entropy(p):
    p = np.asarray([x for x in p if x > 0])
    return float(-(p * np.log2(p)).sum())


def pairwise_abs(df):
    """Mean over options of the mean |p_a - p_b| over pairs of runs (the run-to-run spread of ../preseen/)."""
    vals = [np.mean([abs(a - b) for a, b in itertools.combinations(g.p.tolist(), 2)])
            for _, g in df.groupby("option") if len(g) > 1]
    return float(np.mean(vals)) if vals else None


def single_run_dev(R, C):
    """Per run of R: mean over options of |run − control mean|, with the run itself left out of the control mean when
    it is a control run. Puts one main run, single cards runs and single control runs on the same footing."""
    out = []
    for k, g in R.groupby("rep"):
        CC = C[C.rep != k] if (R.arm.iloc[0] == "control") else C
        cm = CC.groupby("option").p.mean()
        out.append(float((g.set_index("option").p - cm).abs().mean()))
    return out


def quotes(text, k=8):
    """Sentences of a write-up that say how the profiles were used (model output, kept as data)."""
    pat = re.compile(r"[^.\n]*(profile|bibliometric|reference line|percentile|premise|past laureates at)[^.\n]*[.\n]", re.I)
    out = []
    for m in pat.finditer(text):
        q = re.sub(r"[*#`]+", "", m.group(0)).strip()
        q = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", q)
        if 50 <= len(q) <= 360 and q not in out:
            out.append(q)
    return out[:k]


def cmd_field(a):
    field = a.field
    out = HERE / "results" / field
    out.mkdir(parents=True, exist_ok=True)
    opts, runs, subs, texts, wus = load(field)
    K1 = len(opts)
    runs.to_csv(out / "runs_long.csv", index=False)
    subs.to_csv(out / "subforecasts.csv", index=False)
    (out / "writeups.json").write_text(json.dumps(wus, ensure_ascii=False, indent=1))
    by = runs.groupby(["arm", "option"]).p.agg(n="size", mean="mean", sd="std", min="min", max="max").reset_index()
    by["option_text"] = by.option.map(lambda i: opts[i - 1])
    by.to_csv(out / "by_option.csv", index=False)

    C = runs[runs.arm == "control"]
    C1 = C[C.batch == "1 Oct"]
    cg = C.groupby("option").p
    cm, cmin, cmax = cg.mean(), cg.min(), cg.max()
    arms = [a for a in ARMS if (runs.arm == a).any()]
    TA = [a for a in arms if a != "control"]
    M = {arm: runs[runs.arm == arm].groupby("option").p.mean() for arm in arms}
    eff = pd.DataFrame({"option": range(1, K1 + 1), "control_mean": cm.values, "control_min": cmin.values,
                        "control_max": cmax.values, "control_sd": cg.std().values,
                        **{COL[a]: M[a].values for a in TA}})
    for arm in TA:
        eff[DIFF[arm]] = eff[COL[arm]] - eff.control_mean
    eff["main_minus_cards"] = eff.main_p - eff.cards_mean
    if "balanced" in TA:
        eff["balanced_minus_cards"] = eff.balanced_p - eff.cards_mean
        eff["balanced_minus_main"] = eff.balanced_p - eff.main_p
    for arm in TA:
        eff[f"{arm}_outside"] = (eff[COL[arm]] < eff.control_min) | (eff[COL[arm]] > eff.control_max)
    eff["option_text"] = [opts[i - 1] for i in eff.option]
    eff.to_csv(out / "effects.csv", index=False)

    named = eff[eff.option < K1]
    cs = pd.read_csv(BASE / "results" / field / "card_strength_vs_effect.csv")[["option", "impact_share", "inventions_share"]]
    al = named.merge(cs, on="option")
    al.to_csv(out / "card_alignment.csv", index=False)

    def rho(x, y):
        r = spearmanr(al[x], al[y], nan_policy="omit")
        return {"spearman": float(r.statistic), "p": float(r.pvalue), "n": int(al[[x, y]].dropna().shape[0])}

    S = {"field": field, "runs": runs.groupby("arm").rep.nunique().to_dict(),
         "noise_pairwise_all_control": pairwise_abs(C), "noise_pairwise_1oct_control": pairwise_abs(C1),
         "single_run_dev": {arm: single_run_dev(runs[runs.arm == arm], C) for arm in arms},
         "drift_2oct_control_vs_1oct_mean": float((C[C.batch == "2 Oct"].set_index("option").p
                                                   - C1.groupby("option").p.mean()).abs().mean()),
         "drift_2oct_control_outside_1oct_range": int(((C[C.batch == "2 Oct"].set_index("option").p
                                                       < C1.groupby("option").p.min())
                                                      | (C[C.batch == "2 Oct"].set_index("option").p
                                                         > C1.groupby("option").p.max())).sum())}
    for arm in TA:
        col, dcol = COL[arm], DIFF[arm]
        lead = int(eff[eff.option < K1].sort_values(col, ascending=False).option.iloc[0])
        S[arm] = {"mean_abs_diff_vs_control": float(eff[dcol].abs().mean()),
                  "ratio_to_pairwise_noise": float(eff[dcol].abs().mean() / S["noise_pairwise_all_control"]),
                  "options_outside_control_range": int(eff[f"{arm}_outside"].sum()),
                  "other": float(eff[col].iloc[-1]), "named_mass": float(1 - eff[col].iloc[-1]),
                  "entropy_bits": float(np.mean([entropy(g.sort_values("option").p)
                                                 for _, g in runs[runs.arm == arm].groupby("rep")])),
                  "spearman_vs_control": float(spearmanr(eff.control_mean, eff[col]).statistic),
                  "leader": lead, "leader_p": float(eff.loc[eff.option == lead, col].iloc[0]),
                  "rank_changes": {int(i): int(r2 - r1) for i, r1, r2 in
                                   zip(eff.option, eff.control_mean.rank(ascending=False), eff[col].rank(ascending=False))
                                   if r1 != r2},
                  "delta_vs_impact_share": rho(dcol, "impact_share"),
                  "delta_vs_inventions_share": rho(dcol, "inventions_share"),
                  "level_vs_impact_share": rho(col, "impact_share"),
                  "level_vs_inventions_share": rho(col, "inventions_share")}
    lead_c = int(eff[eff.option < K1].sort_values("control_mean", ascending=False).option.iloc[0])
    S["control"] = {"other": float(cm.iloc[-1]), "named_mass": float(1 - cm.iloc[-1]), "leader": lead_c,
                    "leader_p": float(cm.loc[lead_c]),
                    "entropy_bits": float(np.mean([entropy(g.sort_values("option").p) for _, g in C.groupby("rep")])),
                    "level_vs_impact_share": rho("control_mean", "impact_share"),
                    "level_vs_inventions_share": rho("control_mean", "inventions_share")}
    S["main_minus_cards_mean_abs"] = float(eff.main_minus_cards.abs().mean())
    if "balanced" in TA:
        # where the balanced run sits on the line from the cross-check mean (0) to the main run (1), over all options
        dm = eff.main_p - eff.cards_mean
        S["balanced_position"] = {
            "projection_cards0_main1": float((eff.balanced_minus_cards * dm).sum() / (dm ** 2).sum()),
            "mean_abs_vs_cards": float(eff.balanced_minus_cards.abs().mean()),
            "mean_abs_vs_main": float(eff.balanced_minus_main.abs().mean()),
            "spearman_vs_cards": float(spearmanr(eff.cards_mean, eff.balanced_p).statistic),
            "spearman_vs_main": float(spearmanr(eff.main_p, eff.balanced_p).statistic)}
    terms = texts.groupby("arm")[list(TERMS) + [f"sub: {k}" for k in TERMS] + ["chars", "n_sources"]].mean()
    terms.to_csv(out / "terms.csv")
    S["writeup_term_means"] = terms.round(2).to_dict(orient="index")
    for arm in ("main", "balanced"):
        a_wu = [w for w in wus if w["arm"] == arm]
        if a_wu:
            S[f"{arm}_quotes_final"] = quotes(a_wu[0]["write_up"])
            S[f"{arm}_quotes_sub"] = quotes(" ".join(a_wu[0]["sub_write_ups"]), k=10)
        sm = subs[subs.arm == arm]
        if len(sm):
            S[f"{arm}_subforecast_sd_mean"] = float(sm.groupby("option").p.std().mean())
            S[f"{arm}_subforecast_other"] = sm[sm.option == K1].sort_values("sub").p.round(4).tolist()
    (out / "summary.json").write_text(json.dumps(S, indent=1, ensure_ascii=False, default=float))
    print(json.dumps({k: v for k, v in S.items() if "_quotes_" not in k}, indent=1, ensure_ascii=False, default=float))


def cmd_pooled(a):
    rows = []
    for f in FIELDS:
        p = HERE / "results" / f / "summary.json"
        if not p.exists():
            continue
        s = json.loads(p.read_text())
        rows.append({"field": f, "noise_pairwise": s["noise_pairwise_all_control"],
                     "single_run_dev_control": float(np.mean(s["single_run_dev"]["control"])),
                     "single_run_dev_cards": float(np.mean(s["single_run_dev"]["cards"])),
                     "single_run_dev_main": float(np.mean(s["single_run_dev"]["main"])),
                     "mean_abs_diff_cards": s["cards"]["mean_abs_diff_vs_control"],
                     "mean_abs_diff_main": s["main"]["mean_abs_diff_vs_control"],
                     "outside_cards": s["cards"]["options_outside_control_range"],
                     "outside_main": s["main"]["options_outside_control_range"],
                     "other_control": s["control"]["other"], "other_cards": s["cards"]["other"], "other_main": s["main"]["other"],
                     "rho_delta_impact_cards": s["cards"]["delta_vs_impact_share"]["spearman"],
                     "rho_delta_impact_main": s["main"]["delta_vs_impact_share"]["spearman"],
                     "rho_level_impact_control": s["control"]["level_vs_impact_share"]["spearman"],
                     "rho_level_impact_main": s["main"]["level_vs_impact_share"]["spearman"]})
        if "balanced" in s:
            rows[-1].update({"single_run_dev_balanced": float(np.mean(s["single_run_dev"]["balanced"])),
                             "mean_abs_diff_balanced": s["balanced"]["mean_abs_diff_vs_control"],
                             "outside_balanced": s["balanced"]["options_outside_control_range"],
                             "other_balanced": s["balanced"]["other"],
                             "rho_delta_impact_balanced": s["balanced"]["delta_vs_impact_share"]["spearman"],
                             "rho_level_impact_balanced": s["balanced"]["level_vs_impact_share"]["spearman"],
                             "balanced_projection_cards0_main1": s["balanced_position"]["projection_cards0_main1"]})
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "results" / "pooled.csv", index=False)
    print(df.T.to_string())


def cmd_score(a):
    opts, runs, _, _, _ = load(a.field)
    r = runs[runs.option == a.option].assign(log_score=lambda d: np.log(d.p))
    s = r.groupby("arm").log_score.agg(["mean", "std", "size"])
    s.to_csv(HERE / "results" / a.field / "log_score.csv")
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
