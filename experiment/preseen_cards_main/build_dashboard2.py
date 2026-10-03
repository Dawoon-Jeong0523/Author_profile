#!/usr/bin/env python3
"""build_dashboard2.py: Dashboard2, one self-contained HTML page of the "cards as main evidence" follow-up.

    $PY build_dashboard2.py [--out results/dashboard2.html] [--fragment <path>]

--out writes a complete HTML document (open it in a browser); --fragment also writes the same page without the
<html>/<head>/<body> wrapper (for publishing as an Artifact, which adds its own). The page reuses the styles, chart
helpers and scripts of ../preseen/build_dashboard.py (Dashboard 1) so the two read as one series.

Reads results/<field>/{summary.json, by_option.csv, runs_long.csv, effects.csv, card_alignment.csv, terms.csv,
writeups.json, reasoning_summary.md}, results/pooled.csv, questions/<field>.json, instruction/00_instruction.md,
preseen_exp/<field>/state.json. Fields without results are shown as pending. The fourth arm, "cards as one main source"
(../preseen_cards_balanced/, SPEC.md there), appears wherever its run has completed; its reasoning summary is
results/<field>/reasoning_summary_balanced.md.
"""
import argparse
import html
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "preseen"))
import build_dashboard as bd  # noqa: E402  (Dashboard 1: CSS, JS, Markdown and SVG helpers)

FIELDS = ["medicine", "physics", "chemistry"]
LABEL, TAB = bd.LABEL, bd.TAB
E, pct, pp, short, people_of, row_label, tri, ticks = (bd.E, bd.pct, bd.pp, bd.short, bd.people_of, bd.row_label,
                                                       bd.tri, bd.ticks)
ARM = {"control": ("c1", "circle", "Control", "no context"),
       "cards": ("c2", "tri", "Cards as a cross-check", "cards, consider (1 Oct)"),
       "balanced": ("c4", "dia", "Cards as one main source", "balanced note + cards (2 Oct)"),
       "main": ("c3", "sq", "Cards as main evidence", "instruction + cards (2 Oct)")}
NEW = ("balanced", "main")  # the one-run arms of 2 October
COLS = {"cards": ("cards_mean", "diff_cards"), "balanced": ("balanced_p", "diff_balanced"), "main": ("main_p", "diff_main")}
BAL = HERE.parent / "preseen_cards_balanced"


def arms_of(d):
    """Arms with results for this field, in ARM order (the balanced arm once its run has completed)."""
    return [a for a in ARM if a in d["S"]["single_run_dev"]]


def mean(x):
    return sum(x) / len(x)


def sq(x, y, r, cls):
    return f'<rect class="{cls}" x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" rx="1.5"/>'


def mark(arm, x, y, r, kind):
    cls, shape = ARM[arm][0], ARM[arm][1]
    c = f"{cls} {kind}"
    if shape == "circle":
        return f'<circle class="{c}" cx="{x:.1f}" cy="{y:.1f}" r="{r * 0.85:.1f}"/>'
    if shape == "tri":
        return f'<path class="{c}" d="{tri(x, y, r)}"/>'
    if shape == "dia":
        return f'<path class="{c}" d="M{x:.1f},{y - r:.1f} L{x + r:.1f},{y:.1f} L{x:.1f},{y + r:.1f} L{x - r:.1f},{y:.1f} Z"/>'
    return sq(x, y, r * 0.8, c)


def legend(items):
    """items: (arm or 'band', text)."""
    out = []
    for a, t in items:
        if a == "band":
            g = '<rect class="band" x="1" y="2" width="16" height="8" rx="2"/>'
        else:
            g = mark(a, 9, 6.5, 5.5, "solid")
        out.append(f'<span class="lk"><svg width="18" height="12" aria-hidden="true">{g}</svg>{E(t)}</span>')
    return '<div class="legend">' + "".join(out) + "</div>"


def arm_label(a, n=None):
    cls, shape, name, what = ARM[a]
    return f"{name} ({what}{'' if n is None else f', {n} run' + ('s' if n != 1 else '')})"


# ---------------------------------------------------------------- data

def load_field(f):
    r = HERE / "results" / f
    d = {"field": f, "has": (r / "summary.json").exists()}
    d["question"] = json.loads((HERE / "questions" / f"{f}.json").read_text())
    st = HERE / "preseen_exp" / f / "state.json"
    d["state"] = json.loads(st.read_text()) if st.exists() else {"runs": []}
    sb = BAL / "preseen_exp" / f / "state.json"
    d["state_bal"] = json.loads(sb.read_text()) if sb.exists() else {"runs": []}
    if d["has"]:
        d["S"] = json.loads((r / "summary.json").read_text())
        d["by"] = pd.read_csv(r / "by_option.csv")
        d["runs"] = pd.read_csv(r / "runs_long.csv")
        d["eff"] = pd.read_csv(r / "effects.csv")
        d["al"] = pd.read_csv(r / "card_alignment.csv")
        d["terms"] = pd.read_csv(r / "terms.csv", index_col=0)
        d["wus"] = json.loads((r / "writeups.json").read_text())
        rs = r / "reasoning_summary.md"
        d["reason"] = rs.read_text() if rs.exists() else None
        rb = r / "reasoning_summary_balanced.md"
        d["reason_bal"] = rb.read_text() if rb.exists() else None
    return d


# ---------------------------------------------------------------- SVG charts

def dot_plot(d):
    """Probability of every option in each arm: runs hollow, means filled (the 2 October arms have one run each)."""
    opts = d["question"]["options"]
    K1, W, LW, RH, T = len(opts), 860, 430, 50, 14
    runs, by = d["runs"], d["by"]
    xmax = max(runs.p.max() * 1.08, 0.05)
    X = lambda v: LW + (W - LW - 20) * v / xmax
    H = T + K1 * RH + 34
    arms = arms_of(d)
    off = ({"control": -15, "cards": -5, "balanced": 5, "main": 15} if "balanced" in arms
           else {"control": -11, "cards": 0, "main": 11})
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Option probabilities in {len(arms)} arms, {E(LABEL[d["field"]])}">']
    for t in ticks(0, xmax):
        s.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{T + K1 * RH + 16}" text-anchor="middle">{100 * t:.0f}%</text>')
    s.append(f'<line class="axis" x1="{LW}" x2="{W - 20}" y1="{T + K1 * RH}" y2="{T + K1 * RH}"/>')
    for i, o in enumerate(opts, 1):
        yc = T + (i - 0.5) * RH
        s.append(row_label(i, o, LW, yc))
        for arm in arms:
            dy = off[arm]
            R = runs[(runs.arm == arm) & (runs.option == i)]
            if arm not in NEW:
                for r in R.itertuples():
                    x, y = X(r.p), yc + dy
                    s.append(mark(arm, x, y, 4.4, "hollow") + f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="8" '
                             f'data-tip="{E(f"{100 * r.p:.1f}%|{ARM[arm][2]}, run {r.rep} ({r.batch})|{o}")}"/>')
            M = by[(by.arm == arm) & (by.option == i)]
            if len(M):
                m = M.iloc[0]
                x, y = X(m["mean"]), yc + dy
                tip = (f"{100 * m['mean']:.1f}%|{ARM[arm][2]}: " + (f"mean of {int(m['n'])} runs (range {100 * m['min']:.1f}–"
                       f"{100 * m['max']:.1f}%)" if m["n"] > 1 else "one run") + f"|{o}")
                s.append(mark(arm, x, y, 6.5, "solid") + f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="11" tabindex="0" '
                         f'data-tip="{E(tip)}"/>')
    s.append("</svg>")
    return "".join(s)


def effect_plot(d):
    """Each context arm − control per option, against the control runs' range around their mean."""
    e = d["eff"].sort_values("option")
    ta = [a for a in arms_of(d) if a != "control"]
    off = {"cards": -7, "balanced": 0, "main": 7} if "balanced" in ta else {"cards": -5, "main": 5}
    opts = d["question"]["options"]
    K1, W, LW, RH, T = len(opts), 860, 430, 42, 14
    vals = list(e.control_min - e.control_mean) + list(e.control_max - e.control_mean) + [v for a in ta for v in e[COLS[a][1]]]
    lo, hi = min(vals) * 1.15, max(vals) * 1.15
    X = lambda v: LW + (W - LW - 20) * (v - lo) / (hi - lo)
    H = T + K1 * RH + 34
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Change against control per option, {E(LABEL[d["field"]])}">']
    for t in ticks(lo, hi):
        s.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{T + K1 * RH + 16}" text-anchor="middle">'
                 f'{"0" if abs(t) < 1e-9 else f"{100 * t:+.0f}"} pp</text>')
    s.append(f'<line class="zero" x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>')
    for r in e.itertuples():
        i, o = r.option, opts[r.option - 1]
        yc = T + (i - 0.5) * RH
        s.append(row_label(i, o, LW, yc))
        x0, x1 = X(r.control_min - r.control_mean), X(r.control_max - r.control_mean)
        s.append(f'<rect class="band" x="{x0:.1f}" y="{yc - 11:.1f}" width="{max(x1 - x0, 1):.1f}" height="22" rx="3"/>')
        for arm in ta:
            v, val, dy, out = getattr(r, COLS[arm][1]), getattr(r, COLS[arm][0]), off[arm], getattr(r, f"{arm}_outside")
            x = X(v)
            tip = (f"{100 * v:+.2f} pp|{ARM[arm][2]} {100 * val:.1f}% vs control {100 * r.control_mean:.1f}% (control range "
                   f"{100 * r.control_min:.1f}–{100 * r.control_max:.1f}%)" + ("; outside the control range" if out else "") + f"|{o}")
            s.append(mark(arm, x, yc + dy, 6.2, "solid")
                     + f'<circle class="hit" cx="{x:.1f}" cy="{yc + dy:.1f}" r="11" tabindex="0" data-tip="{E(tip)}"/>')
    s.append("</svg>")
    return "".join(s)


def scatter(d):
    """Per named option: the change against control (y) vs how its people compare with past laureates on impact (x)."""
    al, opts = d["al"], d["question"]["options"]
    W, H, L, R, T, B = 860, 380, 64, 24, 16, 46
    ta = [a for a in arms_of(d) if a != "control"]
    ys = [v for a in ta for v in al[COLS[a][1]]]
    lo, hi = min(min(ys), 0) * 1.2, max(max(ys), 0) * 1.2
    X = lambda v: L + (W - L - R) * v
    Y = lambda v: T + (H - T - B) * (hi - v) / (hi - lo)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Change against control vs laureate comparison on impact, '
         f'{E(LABEL[d["field"]])}">']
    for t in (0, 0.25, 0.5, 0.75, 1):
        s.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T}" y2="{H - B}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{H - B + 16}" text-anchor="middle">{100 * t:.0f}%</text>')
    for t in ticks(lo, hi):
        s.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{Y(t) + 4:.1f}" text-anchor="end">{"0" if abs(t) < 1e-9 else f"{100 * t:+.0f}"} pp</text>')
    s.append(f'<line class="zero" x1="{L}" x2="{W - R}" y1="{Y(0):.1f}" y2="{Y(0):.1f}"/>'
             f'<text class="tick" x="{(L + W - R) / 2:.1f}" y="{H - 8}" text-anchor="middle">Share of past laureates the '
             f'option’s people exceed on median impact (mean over the people)</text>')
    for r in al.itertuples():
        if pd.isna(r.impact_share):
            continue
        o = opts[r.option - 1]
        for arm in ta:
            v = getattr(r, COLS[arm][1])
            x, y = X(r.impact_share), Y(v)
            tip = (f"{100 * v:+.2f} pp|{ARM[arm][2]}; people above {100 * r.impact_share:.0f}% of past laureates on impact"
                   f"|{r.option}. {o}")
            s.append(mark(arm, x, y, 6.2, "solid") + f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="10" tabindex="0" '
                     f'data-tip="{E(tip)}"/>')
        s.append(f'<text class="val" x="{X(r.impact_share) + 9:.1f}" y="{Y(r.diff_main) + 4:.1f}">{r.option}</text>')
    s.append("</svg>")
    return "".join(s)


def field_bars(rows):
    """Per field: each arm's mean distance of one run from the control mean (thin horizontal bars, values at the tips)."""
    W, LW, BH, GAP, T = 820, 200, 13, 5, 10
    arms = lambda r: [a for a in ARM if a in r]
    vmax = max(max(r[a] for a in arms(r)) for r in rows) * 1.3
    X = lambda v: LW + (W - LW - 90) * v / vmax
    H = T + sum(len(arms(r)) * (BH + GAP) - GAP + 24 for r in rows) + 6
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Distance of one run from the control mean, by field and arm">']
    y = T
    for r in rows:
        fl = LABEL[r["field"]]
        n = len(arms(r))
        s.append(f'<text class="rowlab" x="{LW - 12}" y="{y + (n * (BH + GAP) - GAP) / 2 + 4:.1f}" text-anchor="end">{E(fl)}</text>')
        for a in arms(r):
            w = X(r[a]) - LW
            s.append(f'<path class="{ARM[a][0]} solid bar" d="M{LW},{y} h{max(w - 4, 0):.1f} q4,0 4,4 v{BH - 8} q0,4 -4,4 '
                     f'h{-max(w - 4, 0):.1f} Z"/><text class="val" x="{LW + w + 6:.1f}" y="{y + BH - 2}">{100 * r[a]:.2f} pp</text>'
                     f'<rect class="hit" x="{LW}" y="{y - 2}" width="{max(w, 24):.1f}" height="{BH + 4}" tabindex="0" '
                     f'data-tip="{E(f"{100 * r[a]:.2f} pp|{ARM[a][2]}: mean |run − control mean| per option|{fl}")}"/>')
            y += BH + GAP
        y += 24 - GAP
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------- page pieces

def minibar(v, vmax, cls):
    return bd.minibar(v, vmax, cls)


def arm_compare(d, top=5):
    opts, by = d["question"]["options"], d["by"]
    other = len(opts)
    arms = arms_of(d)
    M = {a: by[by.arm == a].set_index("option") for a in arms}
    rank_c = {i: k for k, i in enumerate(M["control"].drop(index=other).sort_values("mean", ascending=False).index, 1)}
    vmax = max(M[a].drop(index=other)["mean"].max() for a in arms)
    cols = []
    for a in arms:
        R = M[a].drop(index=other).sort_values("mean", ascending=False)
        i0 = R.index[0]
        n = int(R.loc[i0, "n"])
        lst = ""
        for k, i in enumerate(R.index[:top], 1):
            o = opts[i - 1]
            mv = (f"<span class='mv'>{'▲' if rank_c[i] > k else '▼'} {abs(rank_c[i] - k)} vs control</span>"
                  if a != "control" and rank_c[i] != k else "")
            lst += (f"<li><div class='opt'><b>{k}.</b> {E(short(o, 110))}<div class='ppl'>{E(people_of(o))}</div></div>"
                    f"<div class='pv'>{pct(R.loc[i, 'mean'])}{minibar(R.loc[i, 'mean'], vmax, ARM[a][0])}{mv}</div></li>")
        rng = (f"mean of {n} runs; range {pct(R.loc[i0, 'min'])}–{pct(R.loc[i0, 'max'])}" if n > 1 else "one run")
        cols.append(f"<div class='card arm'><div class='armh'>{legend([(a, ARM[a][2])])}<div class='td'>{E(ARM[a][3])}</div></div>"
                    f"<div class='lead'><div class='tl'>Most likely named discovery</div><div class='leadp'>{pct(R.loc[i0, 'mean'])}</div>"
                    f"<div class='leadd'>{E(short(opts[i0 - 1], 150))}</div><div class='ppl'>{E(people_of(opts[i0 - 1]))}</div>"
                    f"<div class='td'>{rng}</div></div>"
                    f"<div class='oth'>“Other”: <b>{pct(M[a].loc[other, 'mean'])}</b></div><ol class='rk'>{lst}</ol></div>")
    return ("<h4 class='sec'>What each arm predicts</h4><div class='" + ("four" if len(arms) == 4 else "three") + "'>"
            + "".join(cols) + "</div>")


RUNNAME = {"main": "main-evidence run", "balanced": "one-main-source run"}


def diff_list(d, arm="main", top=6):
    opts = d["question"]["options"]
    col, dcol = COLS[arm]
    e = d["eff"].assign(ad=lambda x: x[dcol].abs()).sort_values("ad", ascending=False).head(top)
    li = ""
    for r in e.itertuples():
        o = opts[r.option - 1]
        name = "Other" if o == "Other" else short(o, 110)
        v, dv = getattr(r, col), getattr(r, dcol)
        badge = ("<span class='bd out'>outside the control range</span>" if getattr(r, f"{arm}_outside")
                 else "<span class='bd'>within the control range</span>")
        other = (f" · cards as main evidence {pct(r.main_p)}" if arm == "balanced" else
                 (f" · cards as one main source {pct(r.balanced_p)}" if hasattr(r, "balanced_p") else ""))
        li += (f"<li><div class='opt'><b>{E(name)}</b><div class='ppl'>{E(people_of(o))}</div></div>"
               f"<div class='chg'><span class='from'>{pct(r.control_mean)}</span> → <span class='to'>{pct(v)}</span>"
               f"<span class='dl'>{'▲' if dv > 0 else '▼'} {pp(dv, 1)}</span>{badge}"
               f"<div class='td'>control range {pct(r.control_min)}–{pct(r.control_max)} · cards as a cross-check "
               f"{pct(r.cards_mean)}{other}</div></div></li>")
    return (f"<h4 class='sec'>Where the {RUNNAME[arm]} departs from control</h4><div class='card'><p class='muted'>The six "
            f"largest changes ({RUNNAME[arm].replace(' run', '')} run − control mean). A change counts as larger than run-to-run "
            "noise only when the run lies outside the range of the five control runs.</p><ol class='dlist'>" + li + "</ol></div>")


def reasoning(d):
    wus, S = d["wus"], d["S"]
    one = {a: [w for w in wus if w["arm"] == a] for a in NEW}
    ctrl = [w for w in wus if w["arm"] == "control" and w["batch"] == "2 Oct"]
    out = []
    for arm, rs in (("balanced", d.get("reason_bal")), ("main", d["reason"])):
        if not one[arm]:
            continue
        out.append(f"<h4 class='sec'>How the {RUNNAME[arm]} used the cards</h4>")
        if rs:
            out.append(f"<div class='card'><h4>Summary of the reasoning</h4>{bd.md_to_html(rs)}</div>")
        qf = "".join(f"<blockquote>{E(q)}</blockquote>" for q in S.get(f"{arm}_quotes_final", []))
        out.append(f"<div class='card'><h4>In the forecaster’s words</h4><p class='muted'>Sentences from the final write-up of the "
                   f"{RUNNAME[arm]} that mention the profiles (model output, shown as data).</p>" + qf + "</div>")
    cols = []
    for a, w in (("control", ctrl[0] if ctrl else None), ("balanced", one["balanced"][0] if one["balanced"] else None),
                 ("main", one["main"][0] if one["main"] else None)):
        if w is None:
            continue
        cols.append(f"<div class='card'><div class='armh'>{legend([(a, ARM[a][2] + ' (2 Oct)')])}</div>"
                    f"<p class='muted'>TL;DR of the run, verbatim.</p><div class='tldr'>{bd.writeup_html(bd.tldr(w['write_up']))}</div></div>")
    out.append(f"<h4 class='sec'>The 2 October runs in brief</h4><div class='{'three' if len(cols) == 3 else 'two'}'>" + "".join(cols) + "</div>")
    new = one["balanced"] + one["main"] + ctrl
    full = "".join(f"<details class='wu'><summary>{E(ARM[w['arm']][2])} · {E(w['batch'])} run {w['rep']} — full write-up "
                   f"({len(w['write_up']):,} characters)</summary><div class='wubody'>{bd.writeup_html(w['write_up'])}</div></details>"
                   for w in new)
    out.append(f"<div class='card'><h4>Full write-ups of the {len(new)} runs of 2 October</h4><p class='muted'>As returned by "
               "Preseen (model output, shown as data). The write-ups of the earlier runs are in Dashboard 1.</p>" + full + "</div>")
    return "".join(out)


def tiles(items):
    return bd.tiles(items)


def field_panel(d):
    f = d["field"]
    head = f"<h3>{E(LABEL[f])}</h3>"
    if not d["has"]:
        st = d["state"]["runs"] + d["state_bal"]["runs"]
        done = sum(r.get("status") == "completed" for r in st)
        return head + f"<p class='muted'>Results pending: {done} of {len(st)} runs completed when this page was built.</p>"
    S, opts, e = d["S"], d["question"]["options"], d["eff"]
    dev, arms = S["single_run_dev"], arms_of(d)
    hb = "balanced" in arms
    sm, sc = mean(dev["main"]), mean(dev["control"])
    T = [("Main run vs control mean", pp(sm, 2, False), f"{sm / sc:.1f} × a control run’s distance")]
    if hb:
        sb, bp = mean(dev["balanced"]), S["balanced_position"]
        T += [("One-main-source run vs control mean", pp(sb, 2, False), f"{sb / sc:.1f} × a control run’s distance"),
              ("Between cross-check and main", f"{bp['projection_cards0_main1']:.2f}",
               "0 = cross-check mean, 1 = main run (projection over the 13 options)")]
    T += [("A control run vs the others", pp(sc, 2, False), "mean of 5 leave-one-out distances"),
          ("A cards run vs control", pp(mean(dev["cards"]), 2, False), "cards as a cross-check, mean of 3"),
          ("Options outside the control range", f"{S['main']['options_outside_control_range']} of {len(opts)}",
           f"main run; cross-check {S['cards']['options_outside_control_range']}"
           + (f", one main source {S['balanced']['options_outside_control_range']}" if hb else "")),
          ("“Other”", " → ".join(pct(S[a]["other"]) for a in ("control", "balanced", "main") if a in arms),
           "control → one main source → main" if hb else "control → main"),
          ("Follows the cards?", f"{S['main']['delta_vs_impact_share']['spearman']:+.2f}",
           f"Spearman, change vs laureate comparison, main run; cross-check {S['cards']['delta_vs_impact_share']['spearman']:+.2f}"
           + (f", one main source {S['balanced']['delta_vs_impact_share']['spearman']:+.2f}" if hb else ""))]
    out = [head, tiles(T)]
    out += [arm_compare(d)] + ([diff_list(d, "balanced")] if hb else []) + [diff_list(d, "main")]
    ta = [a for a in arms if a != "control"]
    out += ["<h4 class='sec'>All options</h4><figure class='card'><figcaption><b>Probability of each option, by arm.</b> Hollow "
            "marks: individual runs; filled marks: the arm’s mean (the 2 October arms have one run each). Hover or focus a mark "
            "for its value.</figcaption>",
            legend([(a, arm_label(a, S["runs"][a])) for a in arms]),
            dot_plot(d), "</figure>",
            "<figure class='card'><figcaption><b>Change against control per option.</b> The grey bar is the range of the five "
            "control runs (minimum to maximum), centred on their mean; a marker outside the bar moved by more than the control "
            "runs differ from each other.</figcaption>",
            legend([(a, f"{ARM[a][2]} − control ({S['runs'][a]} run{'s' if S['runs'][a] != 1 else ''})") for a in ta]
                   + [("band", "Control range around its mean")]),
            effect_plot(d), "</figure>"]
    imp_c, imp_m = S["cards"]["delta_vs_impact_share"], S["main"]["delta_vs_impact_share"]
    inv_c, inv_m = S["cards"]["delta_vs_inventions_share"], S["main"]["delta_vs_inventions_share"]
    lc, lm = S["control"]["level_vs_impact_share"], S["main"]["level_vs_impact_share"]
    imp_b = S["balanced"]["delta_vs_impact_share"] if hb else None
    out += ["<figure class='card'><figcaption><b>Does the change follow the cards?</b> Each named option once per arm: its change "
            "against control (vertical) and how far its people stand above the field’s 2000–2025 laureates at prize time on median "
            "impact, the headline number of every card (horizontal). Numbers label the main-evidence run’s marks with the option "
            f"number. Spearman correlation with the change: cross-check arm {imp_c['spearman']:+.2f} (p = {imp_c['p']:.2f}), "
            + (f"one-main-source run {imp_b['spearman']:+.2f} (p = {imp_b['p']:.2f}), " if hb else "")
            + f"main-evidence run {imp_m['spearman']:+.2f} (p = {imp_m['p']:.2f}); n = {imp_m['n']} options.</figcaption>",
            legend([(a, f"{ARM[a][2]} − control") for a in ta]),
            scatter(d), "</figure>"]
    rows = "".join(
        f"<tr><td>{r.option}</td><td>{'Other' if opts[r.option - 1] == 'Other' else E(short(opts[r.option - 1], 200)) + '<br><span class=muted>' + E(people_of(opts[r.option - 1])) + '</span>'}</td>"
        f"<td class='num'>{pct(r.control_mean)}</td><td class='num'>{pct(r.control_min)}–{pct(r.control_max)}</td>"
        f"<td class='num'>{pct(r.cards_mean)}</td>"
        + (f"<td class='num'>{pct(r.balanced_p)}</td>" if hb else "")
        + f"<td class='num'>{pct(r.main_p)}</td>"
        + (f"<td class='num'>{pp(r.diff_balanced)}</td>" if hb else "")
        + f"<td class='num'>{pp(r.diff_main)}</td>"
        + f"<td>{', '.join(n for a, n in (('balanced', 'one main source'), ('main', 'main')) if a in arms and getattr(r, f'{a}_outside'))}</td></tr>"
        for r in e.sort_values("option").itertuples())
    out.append("<details class='card'><summary>Table view: probabilities and differences by option</summary><div class='tw'><table>"
               "<thead><tr><th>#</th><th>Option (discovery and people)</th><th>Control mean</th><th>Control range</th>"
               "<th>Cards as a cross-check</th>" + ("<th>Cards as one main source</th>" if hb else "")
               + "<th>Cards as main evidence</th>" + ("<th>One main source − control</th>" if hb else "")
               + "<th>Main − control</th><th>Outside the control range</th></tr></thead>"
               "<tbody>" + rows + "</tbody></table></div></details>")
    out.append(reasoning(d))
    t = d["terms"]
    keys = [("sub: supplied bibliometrics", "References to the supplied bibliometrics (subforecasts)"),
            ("sub: percentile", "“percentile” (subforecasts)"), ("sub: patent", "“patent” / “invention” (subforecasts)"),
            ("sub: textbook/book", "“textbook” / “book” (subforecasts)"), ("sub: laureate", "“laureate” (subforecasts)"),
            ("supplied bibliometrics", "References to the supplied bibliometrics (final write-up)"),
            ("premise", "“premise” / “assumption” (final write-up)"), ("chars", "Length of the final write-up (characters)")]
    trs = "".join(f"<tr><td>{E(b)}</td>" + "".join(f"<td class='num'>{t.loc[a2, k]:,.1f}</td>" for a2 in arms) + "</tr>"
                  for k, b in keys if k in t.columns)
    short_arm = {"control": "Control", "cards": "Cross-check", "balanced": "One main source", "main": "Main"}
    out.append("<div class='two'><div class='card'><h4>Mentions per run</h4><p class='muted'>Both instruction notes ask the run "
               "to name the profile evidence behind each leading option, so their counts are expected to rise; they show uptake, "
               "not an effect.</p><div class='tw'><table><thead><tr><th>Term</th>"
               + "".join(f"<th>{short_arm[a]}</th>" for a in arms) + "</tr></thead><tbody>" + trs + "</tbody></table></div></div>"
               "<div class='card'><h4>Further diagnostics</h4><ul>"
               f"<li>Correlation of the probabilities themselves with the laureate comparison on impact (named options): control "
               f"{lc['spearman']:+.2f}, main-evidence run {lm['spearman']:+.2f}</li>"
               f"<li>Change vs the laureate comparison on citing inventions: cross-check {inv_c['spearman']:+.2f}, main {inv_m['spearman']:+.2f}</li>"
               + "<li>Entropy of the forecast: " + ", ".join(f"{short_arm[a].lower()} {S[a]['entropy_bits']:.2f}" for a in arms)
               + " bits</li>"
               + "<li>Rank correlation with the control means: "
               + ", ".join(f"{short_arm[a].lower()} {S[a]['spearman_vs_control']:.2f}" for a in ta) + "</li>"
               + (f"<li>One-main-source run against the other two context arms: {pp(S['balanced_position']['mean_abs_vs_cards'], 2, False)} "
                  f"per option from the cross-check mean, {pp(S['balanced_position']['mean_abs_vs_main'], 2, False)} from the main run; "
                  f"rank correlation {S['balanced_position']['spearman_vs_cards']:.2f} and "
                  f"{S['balanced_position']['spearman_vs_main']:.2f}</li>" if hb else "")
               + 
               f"<li>Time drift: the 2 October control run differs from the 1 October control mean by "
               f"{pp(S['drift_2oct_control_vs_1oct_mean'], 2, False)} per option ({S['drift_2oct_control_outside_1oct_range']} of "
               f"{len(opts)} options outside the 1 October range)</li>"
               + "".join(f"<li>Spread between the {RUNNAME[a]}’s subforecasts: {pp(S[f'{a}_subforecast_sd_mean'], 2, False)} per "
                         f"option (sd); “Other” in the subforecasts: {', '.join(pct(x) for x in S[f'{a}_subforecast_other'])}</li>"
                         for a in ("balanced", "main") if f"{a}_subforecast_sd_mean" in S)
               + "</ul></div></div>")
    return "\n".join(out)


CSS2 = r"""
:root{--s3:#1baf7a;--s4:#8a5cd1}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--s3:#199e70;--s4:#9d78e2}}
:root[data-theme="dark"]{--s3:#199e70;--s4:#9d78e2}
nav.top{top:env(safe-area-inset-top,0px)}
.c3.solid{fill:var(--s3);stroke:var(--surface);stroke-width:2}.c3.hollow{fill:var(--surface);stroke:var(--s3);stroke-width:1.5}
.c4.solid{fill:var(--s4);stroke:var(--surface);stroke-width:2}.c4.hollow{fill:var(--surface);stroke:var(--s4);stroke-width:1.5}
.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}@media (max-width:900px){.three{grid-template-columns:1fr}}
.four{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}@media (max-width:1100px){.four{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:640px){.four{grid-template-columns:1fr}}
.two>*,.three>*,.four>*{min-width:0}
.armh .td{margin:-6px 0 8px}
.hero .big2{font-size:44px;font-weight:600;line-height:1;font-variant-numeric:tabular-nums}
.heroes{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:12px 0}
.heroes .card{margin:0}.heroes .fl{color:var(--ink2);font-size:13px;margin-bottom:6px}
.heroes .vs{color:var(--muted);font-size:13px;margin-top:6px}
.cardnote p{margin:0 0 8px}
"""


def build(out_path, frag_path=None):
    D = {f: load_field(f) for f in FIELDS}
    done = [f for f in FIELDS if D[f]["has"]]
    n_runs = sum(len(D[f]["state"]["runs"]) + len(D[f]["state_bal"]["runs"]) for f in FIELDS)
    n_done = sum(r.get("status") == "completed" for f in FIELDS for r in D[f]["state"]["runs"] + D[f]["state_bal"]["runs"])
    hb = any("balanced" in D[f]["S"]["single_run_dev"] for f in done)
    gen = pd.Timestamp.now(tz="America/Chicago").strftime("%d %B %Y, %H:%M %Z")
    H = ["<title>Nobel 2026 Dashboard2</title>", f"<style>{bd.CSS}{CSS2}</style>",
         "<div id='tip' role='status'></div><div class='wrap'>",
         "<header><h1>Told to rely on the profile cards, does the forecast follow them?</h1>",
         f"<p class='sub'>Dashboard2 · follow-up to the Preseen context experiment on the 2026 Nobel Prizes · Physiology or "
         f"Medicine, Physics, Chemistry · built {E(gen)} · {n_done} of {n_runs} new runs completed</p></header>",
         "<nav class='top'><a href='#overview'>Overview</a><a href='#results'>Results by field</a><a href='#instruction'>The instruction</a>"
         "<a href='#method'>Method</a><a href='#caveats'>Caveats</a><a href='#files'>Files</a>"
         "<button id='theme' type='button'>Dark theme</button></nav>"]

    H.append("<section id='overview'><h2>Overview</h2><div class='card'><p>In the first experiment (Dashboard 1) the profile "
             "cards, attached as context to be considered, moved Preseen’s forecasts less than repeated runs without them differ "
             "from each other, and the forecaster said it used them only as a secondary cross-check. Here the same cards go onto "
             "new copies of the same questions together with one more note, attached as an assumption to apply: <i>the profiles "
             "are the main evidence for comparing the named options</i>. One new control run and one run with the instruction were "
             "made per field on 2 October 2026 and compared with the five control runs and the three cross-check runs. A fourth "
             "arm, added the same day, softens the note: <i>the profiles are one of the main sources of evidence</i>, weighed "
             "comparably with prizes, news, predictions and the prize’s history, which the forecaster is asked to use actively "
             "(one run per field).</p>"
             + legend([(a, arm_label(a)) for a in ARM]) + "</div>")
    if done:
        cards = ""
        for f in done:
            S = D[f]["S"]
            dev = S["single_run_dev"]
            sm, sc, scd = dev["main"][0], mean(dev["control"]), mean(dev["cards"])
            bal = (f"<div class='big2' style='margin-top:8px'>{dev['balanced'][0] / sc:.1f}×</div><div class='vs'>one-main-source "
                   f"run ({pp(dev['balanced'][0], 2, False)})</div>" if "balanced" in dev else "")
            cards += (f"<div class='card'><div class='fl'>{E(LABEL[f])}</div><div class='big2'>{sm / sc:.1f}×</div>"
                      f"<div class='vs'>main-evidence run vs a control run’s distance from the control mean "
                      f"({pp(sm, 2, False)} vs {pp(sc, 2, False)}); a cross-check run: {scd / sc:.1f}×</div>{bal}</div>")
        H.append("<h3>How far one run lands from the control mean</h3><div class='heroes'>" + cards + "</div>")
        rows = []
        for f in done:
            dev = D[f]["S"]["single_run_dev"]
            rows.append({"field": f, **{a: mean(dev[a]) for a in ARM if a in dev}})
        H.append("<figure class='card'><figcaption><b>Distance of one run from the control mean</b>, mean over the 13 options "
                 "(percentage points). Control: each of the five control runs against the mean of the other four. Cross-check: each "
                 "of the three runs of 1 October with the cards considered. One main source and main: the one run with each "
                 "instruction note.</figcaption>"
                 + legend([(a, ARM[a][2]) for a in ARM if hb or a != "balanced"]) + field_bars(rows) + "</figure>")
        pr = ""
        for f in done:
            d, S = D[f], D[f]["S"]
            opts = d["question"]["options"]
            cells = []
            AA = [a for a in ARM if hb or a != "balanced"]
            for a in AA:
                if a not in S:
                    cells.append("<span class='muted'>pending</span>")
                    continue
                i0, p0 = S[a]["leader"], S[a]["leader_p"]
                cells.append(f"<b>{pct(p0)}</b> {E(short(opts[i0 - 1], 70))}<br><span class='muted'>{E(people_of(opts[i0 - 1]))}</span>")
            pr += (f"<tr><td>{E(LABEL[f])}</td>" + "".join(f"<td>{c}</td>" for c in cells)
                   + f"<td class='num'>{' · '.join(pct(S[a]['other']) if a in S else '–' for a in AA)}</td></tr>")
        oth = " · ".join({"control": "control", "cards": "cross-check", "balanced": "one main source", "main": "main"}[a] for a in AA)
        H.append("<h3>Who each arm predicts</h3><div class='card'><div class='tw'><table><thead><tr><th>Field</th>"
                 + "".join(f"<th>{ARM[a][2] if a != 'control' else 'Control'}</th>" for a in AA)
                 + f"<th>“Other” ({oth})</th></tr></thead><tbody>" + pr + "</tbody></table></div></div>")
        fr = ""
        for f in done:
            S = D[f]["S"]
            TA = [a for a in ("cards", "balanced", "main") if hb or a != "balanced"]
            g = lambda a, fn: fn(S[a]) if a in S else "–"
            fr += (f"<tr><td>{E(LABEL[f])}</td>"
                   f"<td class='num'>{' · '.join(str(g(a, lambda x: x['options_outside_control_range'])) for a in TA)}</td>"
                   f"<td class='num'>{' · '.join(g(a, lambda x: format(x['delta_vs_impact_share']['spearman'], '+.2f')) for a in TA)}</td>"
                   f"<td class='num'>{' · '.join(g(a, lambda x: format(x['level_vs_impact_share']['spearman'], '+.2f')) for a in ['control'] + TA[1:])}</td>"
                   f"<td class='num'>{' · '.join(g(a, lambda x: format(x['spearman_vs_control'], '.2f')) for a in TA)}</td>"
                   + (f"<td class='num'>{S['balanced_position']['projection_cards0_main1']:.2f}</td>" if hb else "") + "</tr>")
        lab = "cross-check · one main source · main" if hb else "cross-check · main"
        lab2 = "control · one main source · main" if hb else "control · main"
        H.append("<h3>Does the forecast follow the cards?</h3><div class='card'><div class='tw'><table><thead><tr><th>Field</th>"
                 f"<th>Options outside the control range ({lab})</th><th>Change vs laureate comparison on impact, "
                 f"Spearman ({lab})</th><th>Probability vs laureate comparison, Spearman ({lab2})</th>"
                 f"<th>Rank correlation with control ({lab})</th>"
                 + ("<th>One main source between cross-check (0) and main (1)</th>" if hb else "")
                 + "</tr></thead><tbody>" + fr + "</tbody></table></div>"
                 "<p class='muted'>The laureate comparison of an option is the mean, over its named people, of the share of the "
                 "field’s 2000–2025 laureates (at prize time) whose median impact percentile the person exceeds, as printed on the "
                 "cards. Twelve named options per field; with one run per 2 October arm these are descriptive numbers, not tests. "
                 "The position of the one-main-source run is the projection of its change from the cross-check mean onto the line "
                 "from the cross-check mean to the main run, over all 13 options.</p></div>")
    else:
        H.append("<p class='muted'>Results pending.</p>")
    H.append("</section>")

    H.append("<section id='results'><h2>Results by field</h2><div class='tabs' id='fieldtabs' role='tablist'>")
    for k, f in enumerate(FIELDS):
        H.append(f"<button type='button' role='tab' id='tab-{f}' aria-controls='panel-{f}' aria-selected='{'true' if k == 0 else 'false'}'>{TAB[f]}</button>")
    H.append("</div>")
    for k, f in enumerate(FIELDS):
        H.append(f"<div class='panel' id='panel-{f}' role='tabpanel' aria-labelledby='tab-{f}'{'' if k == 0 else ' hidden'}>"
                 + field_panel(D[f]) + "</div>")
    H.append("</section>")

    note = (HERE / "instruction" / "00_instruction.md").read_text()
    paras = "".join(f"<p>{E(p.strip())}</p>" for p in note.split("\n") if p.strip() and not p.startswith("- "))
    items = "".join(f"<li>{E(p[2:].strip())}</li>" for p in note.split("\n") if p.startswith("- "))
    H.append("<section id='instruction'><h2>The instruction</h2><div class='two'><div class='card'><h4>The note, as attached</h4>"
             "<p class='muted'><code>instruction/00_instruction.md</code> · <code>treatment=assume_true</code> · added before the "
             "definitions note and the cards</p><div class='cardnote'>" + paras + "<ul>" + items + "</ul></div></div>"
             "<div class='card'><h4>Why it is worded this way</h4><p>Each sentence answers a reason the forecaster gave on 1 October "
             "for keeping the cards secondary.</p><div class='tw'><table><thead><tr><th>Reason given in the cross-check runs</th>"
             "<th>Answer in the note</th></tr></thead><tbody>"
             "<tr><td>Percentiles among past laureates are not calibrated selection probabilities</td><td>Translating the profiles "
             "into probabilities is part of the task</td></tr>"
             "<tr><td>Author attribution cannot be audited (e.g. a publication record starting in 1950 for a person born in 1948)</td>"
             "<td>Take the figures as given</td></tr>"
             "<tr><td>The records end in 2021 and miss recent awards and approvals</td><td>Do not discount for that; recent "
             "information is a secondary adjustment</td></tr>"
             "<tr><td>Outside recognition (Lasker, Breakthrough, Clarivate) is the better signal</td><td>Prizes, news, predictions "
             "and prize history only as a secondary adjustment</td></tr>"
             "<tr><td>The cards cover only the people named in the options</td><td>Judge named options by their named people; "
             "judge “Other” as otherwise and use the cards to divide the rest</td></tr></tbody></table></div>"
             "<p class='muted'>The note names no committee, model or experiment and gives no direction (it does not say which "
             "measure or which people should count more). The last sentence asks the forecaster to name the profile evidence "
             "behind its leading options, so the uptake can be read in the write-up.</p></div></div>")
    nb = BAL / "instruction" / "00_instruction.md"
    if nb.exists():
        note = nb.read_text()
        paras = "".join(f"<p>{E(p.strip())}</p>" for p in note.split("\n") if p.strip() and not p.startswith("- "))
        items = "".join(f"<li>{E(p[2:].strip())}</li>" for p in note.split("\n") if p.startswith("- "))
        H.append("<div class='two' style='margin-top:12px'><div class='card'><h4>The softer note: cards as one main source</h4>"
                 "<p class='muted'><code>preseen_cards_balanced/instruction/00_instruction.md</code> · <code>treatment=assume_true</code> "
                 "· attached first, then the same cards</p><div class='cardnote'>" + paras + "<ul>" + items + "</ul></div></div>"
                 "<div class='card'><h4>What changed against the main-evidence note</h4><div class='tw'><table><thead><tr>"
                 "<th>Main-evidence note</th><th>One-main-source note</th></tr></thead><tbody>"
                 "<tr><td>The profiles are <i>the main</i> evidence</td><td>The profiles are <i>one of the main</i> sources, alongside "
                 "the other evidence</td></tr>"
                 "<tr><td>Prizes, news, predictions, prize history only as a secondary adjustment</td><td>Use them actively; profiles "
                 "get weight comparable to the other main evidence, and neither replaces the other</td></tr>"
                 "<tr><td>Judge “Other” as otherwise and use the cards to divide the rest</td><td>For “Other” and for unnamed "
                 "contributors, rely on the other evidence</td></tr>"
                 "<tr><td>Name the profile evidence behind each leading option</td><td>Name the profile evidence and the other "
                 "evidence behind each leading option</td></tr>"
                 "<tr><td>Take the figures as given</td><td>Unchanged</td></tr></tbody></table></div>"
                 "<p class='muted'>Several sentences change at once, so the one-main-source arm measures the softer note as a "
                 "whole, not any one sentence.</p></div></div>")
    H.append("</section>")

    H.append("<section id='method'><h2>Method</h2><div class='card'><ul>"
             "<li><b>Same as Dashboard 1:</b> the question text, options and resolution criteria (copied unchanged), the 101 cards "
             "and definitions notes (copied unchanged, <code>treatment=consider</code>, same seeded order), the Preseen client "
             "(unchanged copy), private questions, <code>allow_incomplete_context=false</code>, an idempotency key on every request.</li>"
             "<li><b>Different:</b> one extra note on the treat question, the instruction above, attached first with "
             "<code>treatment=assume_true</code> (the setting a premise note took effect with in the Mojsov check of 1 October); "
             "new question copies per arm because context notes apply to every later run of a question.</li>"
             "<li><b>Runs:</b> one control and one main-evidence run per field, submitted together on 2 October 2026 at about "
             "09:05 CDT (Medicine, Physics, Chemistry in parallel), well before the announcements (5, 6 and 7 October). A read-back "
             "of the notes confirmed 0 notes on each control question and 1 + 31 / 35 / 35 on the treat questions, with no duplicates.</li>"
             "<li><b>Fourth arm (one main source):</b> new private copies of the same questions with the softer note "
             "(<code>treatment=assume_true</code>) and the same cards, one run per field, submitted together on 2 October 2026 at "
             "about 09:54 CDT; the client confirmed 1 + 31 / 35 / 35 notes before each run. No new control run: the five control "
             "runs are its baseline.</li>"
             "<li><b>Yardsticks:</b> because the main arm has one run, its distance from the control mean is compared with the same "
             "distance for single control runs (each against the mean of the other four) and for the single cross-check runs. The "
             "pairwise control spread of Dashboard 1 is kept in <code>summary.json</code>. Options are “outside the control range” "
             "when the run lies below the lowest or above the highest of the five control runs.</li>"
             "<li><b>Direction:</b> the Spearman correlation, over the twelve named options, between an option’s change and the "
             "laureate comparison printed on its people’s cards (impact; citing inventions as a second measure), as in Dashboard 1.</li>"
             "</ul></div></section>")
    H.append("<section id='caveats'><h2>Caveats</h2><div class='card'><ul>"
             "<li><b>One run per arm.</b> A single main-evidence run per field; its distance from control is compared with single "
             "control runs, but the comparison is descriptive.</li>"
             "<li><b>Two changes at once.</b> The note both raises the cards and lowers outside evidence (awards, news). Without a "
             "placebo arm (the same note with the cards’ numbers shuffled across people) a move away from the award-driven ranking "
             "cannot be separated from following these particular numbers; the correlation with the laureate comparison is the "
             "check on the second.</li>"
             "<li><b>A day apart.</b> The baseline runs are from 1 October and the new runs from 2 October; the new control run "
             "measures the drift.</li>"
             "<li><b>Card errors are kept.</b> The cards are unchanged, including known weaknesses (e.g. a merged OpenAlex record "
             "for Robert Langer, thin profiles for Pascal Mayer, Rafi Bistritzer and Naoko Kurahashi Neilson), and the note asks the "
             "forecaster to take the figures as given.</li>"
             "<li><b>Scope sentence.</b> Asking to judge named options by their named people departs slightly from the resolution "
             "rule (resolution by discovery, whoever shares it); it keeps alternative rosters such as Drucker for GLP-1 from "
             "re-entering through the back door.</li>"
             "<li><b>The fourth arm came later.</b> The one-main-source note was written after the main-evidence results were "
             "seen, as a follow-up question (where does the forecast land between the two?); it is not a pre-planned dose arm, "
             "and its runs are about 50 minutes later than the main-evidence runs.</li></ul></div></section>")
    H.append("<section id='files'><h2>Files</h2><div class='card'><ul>"
             "<li><code>experiment/preseen_cards_main/SPEC.md</code> design · <code>LOG.md</code> every step · "
             "<code>instruction/00_instruction.md</code> the note · <code>run_field.sh</code> the run sequence</li>"
             "<li><code>questions/</code>, <code>cards/</code>, <code>nobel_preseen_exp.py</code> unchanged copies from "
             "<code>experiment/preseen/</code></li>"
             "<li><code>preseen_exp/&lt;field&gt;/</code> client state and run JSONs (not versioned) · <code>results/&lt;field&gt;/</code> "
             "analysis tables, write-ups, reasoning summaries · <code>results/pooled.csv</code></li>"
             "<li><code>experiment/preseen_cards_balanced/</code>: the fourth arm (SPEC.md, LOG.md, instruction note, "
             "run_field.sh, run JSONs under <code>preseen_exp/</code>); its tables are written into <code>results/&lt;field&gt;/</code> "
             "here by <code>analyze_main.py</code></li>"
             "<li>This page: <code>build_dashboard2.py</code> → <code>results/dashboard2.html</code> · Dashboard 1: "
             "<code>experiment/preseen/results/dashboard.html</code></li></ul></div></section>")
    H.append(f"</div><script>{bd.JS}</script>")
    body = "\n".join(H)
    if frag_path:
        Path(frag_path).parent.mkdir(parents=True, exist_ok=True)
        Path(frag_path).write_text(body, encoding="utf-8")
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
           'content="width=device-width,initial-scale=1,viewport-fit=cover">' + body.replace("<div id='tip'", "</head><body><div id='tip'", 1)
           + "</body></html>")
    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes); fields with results: {done}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(HERE / "results" / "dashboard2.html"))
    ap.add_argument("--fragment", default=None)
    a = ap.parse_args()
    build(Path(a.out), a.fragment)


if __name__ == "__main__":
    main()
