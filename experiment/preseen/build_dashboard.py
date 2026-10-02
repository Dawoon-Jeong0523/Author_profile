#!/usr/bin/env python3
"""build_dashboard.py: one self-contained HTML dashboard of the experiment (results + process + card examples).

    $PY build_dashboard.py [--out results/dashboard.html]

Reads results/<field>/{summary.json, by_option.csv, runs_long.csv, effects.csv, terms.csv}, results/pooled/pooled.csv,
committee/<field>/{ballots.jsonl, candidates.json, merges.yaml}, questions/<field>.json, people/<field>_identity.csv,
cards/<field>/*.md, cards/laureate_reference.csv and config.yaml. Fields without results are shown as pending.
No external scripts, fonts or images: charts are inline SVG; a small script handles the field tabs, tooltips and theme.
"""
import argparse
import csv
import html
import json
import re
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load((HERE / "config.yaml").read_text())
FIELDS = CFG["order"]
LABEL = {"medicine": "Physiology or Medicine", "physics": "Physics", "chemistry": "Chemistry"}
TAB = {"medicine": "Medicine", "physics": "Physics", "chemistry": "Chemistry"}
E = html.escape


def pct(x, d=1):
    return "–" if x is None or pd.isna(x) else f"{100 * x:.{d}f}%"


def pp(x, d=2, sign=True):
    return "–" if x is None or pd.isna(x) else (f"{100 * x:+.{d}f}" if sign else f"{100 * x:.{d}f}") + " pp"


def short(o, n=58):
    t = re.sub(r"^for (the |their |his |her )?", "", o.split(" — ")[0])
    t = t[0].upper() + t[1:]
    return t if len(t) <= n else t[: n - 1] + "…"


def people_of(o):
    return o.split(" — ", 1)[1] if " — " in o else ""


def row_label(i, o, LW, yc):
    """Two-line row label: '<n>. <discovery>' and, smaller, the people named in the option (full option in <title>)."""
    if o == "Other":
        return f'<text class="rowlab" x="{LW - 10}" y="{yc + 4:.1f}" text-anchor="end">{i}. Other<title>Other</title></text>'
    names = people_of(o)
    names = names if len(names) <= 72 else names[:71] + "…"
    return (f'<text class="rowlab" x="{LW - 10}" y="{yc - 2:.1f}" text-anchor="end">{E(f"{i}. {short(o, 50)}")}<title>{E(o)}</title></text>'
            f'<text class="rowsub" x="{LW - 10}" y="{yc + 12:.1f}" text-anchor="end">{E(names)}<title>{E(o)}</title></text>')


def md_to_html(text):
    """Minimal Markdown (#, ##, -, 1., **bold**) for the card files; hard-wrapped lines are joined to their list item or
    paragraph; everything is escaped first."""
    blocks = []                                          # (kind, text): h4, h5, ul, ol, p
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            blocks.append(("blank", ""))
        elif line.startswith("## "):
            blocks.append(("h5", line[3:]))
        elif line.startswith("# "):
            blocks.append(("h4", line[2:]))
        elif re.match(r"^- ", line):
            blocks.append(("ul", line[2:]))
        elif re.match(r"^\d+\. ", line):
            blocks.append(("ol", re.sub(r"^\d+\. ", "", line)))
        elif blocks and blocks[-1][0] in ("ul", "ol", "p"):  # continuation of the previous item or paragraph
            blocks[-1] = (blocks[-1][0], blocks[-1][1] + " " + line.strip())
        else:
            blocks.append(("p", line.strip()))
    out, lst = [], None
    for kind, t in blocks:
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", E(t))
        if lst and kind != lst:
            out.append(f"</{lst}>")
            lst = None
        if kind in ("ul", "ol"):
            if not lst:
                out.append(f"<{kind}>")
                lst = kind
            out.append(f"<li>{t}</li>")
        elif kind in ("h4", "h5", "p"):
            out.append(f"<{kind}>{t}</{kind}>")
    if lst:
        out.append(f"</{lst}>")
    return "\n".join(out)


# ---------------------------------------------------------------- data

def load_field(f):
    r = HERE / "results" / f
    d = {"field": f, "has": (r / "summary.json").exists()}
    d["question"] = json.loads((HERE / "questions" / f"{f}.json").read_text())
    d["cand"] = json.loads((HERE / "committee" / f / "candidates.json").read_text())["options"]
    balls = [json.loads(l) for l in (HERE / "committee" / f / "ballots.jsonl").read_text().splitlines() if l.strip()]
    d["ballots"] = balls
    d["manual"] = yaml.safe_load((HERE / "committee" / f / "merges.yaml").read_text()) or {}
    state = json.loads((HERE / "preseen_exp" / f / "state.json").read_text())
    d["state"] = state
    if d["has"]:
        d["summary"] = json.loads((r / "summary.json").read_text())
        d["by"] = pd.read_csv(r / "by_option.csv")
        d["runs"] = pd.read_csv(r / "runs_long.csv")
        d["eff"] = pd.read_csv(r / "effects.csv")
        d["terms"] = pd.read_csv(r / "terms.csv", index_col=0)
    return d


# ---------------------------------------------------------------- SVG charts

def tri(x, y, r):
    return f"M{x:.1f},{y - r:.1f} L{x + r * 0.95:.1f},{y + r * 0.7:.1f} L{x - r * 0.95:.1f},{y + r * 0.7:.1f} Z"


def ticks(lo, hi, n=5):
    span = hi - lo
    step = [s for s in (0.005, 0.01, 0.02, 0.025, 0.05, 0.1, 0.2) if span / s <= n + 1][0]
    t, out = (int(lo / step) - 1) * step, []
    while t <= hi + 1e-12:
        if t >= lo - 1e-12:
            out.append(round(t, 6))
        t += step
    return out


def dot_plot(d):
    """Probability of every option: control and treat runs (hollow) and means (filled)."""
    opts = d["question"]["options"]
    K1, W, LW, RH, T = len(opts), 860, 430, 44, 14
    runs, by = d["runs"], d["by"]
    xmax = max(runs.p.max() * 1.08, 0.05)
    X = lambda v: LW + (W - LW - 20) * v / xmax
    H = T + K1 * RH + 34
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Option probabilities by arm, {E(LABEL[d["field"]])}">']
    for t in ticks(0, xmax):
        s.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{T + K1 * RH + 16}" text-anchor="middle">{100 * t:.0f}%</text>')
    s.append(f'<line class="axis" x1="{LW}" x2="{W - 20}" y1="{T + K1 * RH}" y2="{T + K1 * RH}"/>')
    for i, o in enumerate(opts, 1):
        yc = T + (i - 0.5) * RH
        s.append(row_label(i, o, LW, yc))
        for arm, dy, cls in (("control", -6, "c1"), ("treat", 6, "c2")):
            R = runs[(runs.arm == arm) & (runs.option == i)]
            for r in R.itertuples():
                x, y = X(r.p), yc + dy
                mark = (f'<circle class="{cls} hollow" cx="{x:.1f}" cy="{y:.1f}" r="3.6"/>' if arm == "control"
                        else f'<path class="{cls} hollow" d="{tri(x, y, 4.2)}"/>')
                tip = f"{100 * r.p:.1f}%|{arm} run {r.rep}|{o}"
                s.append(mark + f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="9" data-tip="{E(tip)}"/>')
            M = by[(by.arm == arm) & (by.option == i)]
            if len(M):
                m = M.iloc[0]
                x, y = X(m["mean"]), yc + dy
                mark = (f'<circle class="{cls} solid" cx="{x:.1f}" cy="{y:.1f}" r="5.5"/>' if arm == "control"
                        else f'<path class="{cls} solid" d="{tri(x, y, 6.5)}"/>')
                tip = (f"{100 * m['mean']:.1f}%|{arm} mean of {int(m['n'])} runs "
                       f"(range {100 * m['min']:.1f}–{100 * m['max']:.1f}%)|{o}")
                s.append(mark + f'<circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="12" tabindex="0" data-tip="{E(tip)}"/>')
    s.append("</svg>")
    return "".join(s)


def effect_plot(d):
    """Treat − control per option against the control arm's run-to-run range (centred on the control mean)."""
    e = d["eff"][d["eff"].arm == "treat"].sort_values("option")
    opts = d["question"]["options"]
    K1, W, LW, RH, T = len(opts), 860, 430, 40, 14
    lo = min((e.control_min - e.control_mean).min(), e["diff"].min()) * 1.15
    hi = max((e.control_max - e.control_mean).max(), e["diff"].max()) * 1.15
    X = lambda v: LW + (W - LW - 20) * (v - lo) / (hi - lo)
    H = T + K1 * RH + 34
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Treat minus control per option, {E(LABEL[d["field"]])}">']
    for t in ticks(lo, hi):
        s.append(f'<line class="grid" x1="{X(t):.1f}" x2="{X(t):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{T + K1 * RH + 16}" text-anchor="middle">{"0" if abs(t) < 1e-9 else f"{100 * t:+.0f}"} pp</text>')
    s.append(f'<line class="zero" x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{T - 6}" y2="{T + K1 * RH}"/>')
    for r in e.itertuples():
        i, o = r.option, opts[r.option - 1]
        yc = T + (i - 0.5) * RH
        s.append(row_label(i, o, LW, yc))
        x0, x1 = X(r.control_min - r.control_mean), X(r.control_max - r.control_mean)
        s.append(f'<rect class="band" x="{x0:.1f}" y="{yc - 6:.1f}" width="{max(x1 - x0, 1):.1f}" height="12" rx="3"/>')
        x = X(r.diff)
        tip = (f"{100 * r.diff:+.2f} pp|treat {100 * r.arm_mean:.1f}% vs control {100 * r.control_mean:.1f}% "
               f"(control range {100 * r.control_min:.1f}–{100 * r.control_max:.1f}%)"
               + ("; outside the control range" if r.outside_control_range else "") + f"|{o}")
        s.append(f'<path class="c2 solid" d="{tri(x, yc, 6.5)}"/>'
                 f'<circle class="hit" cx="{x:.1f}" cy="{yc:.1f}" r="12" tabindex="0" data-tip="{E(tip)}"/>')
    s.append("</svg>")
    return "".join(s)


def pooled_bars(rows):
    """Per field: control run-to-run spread vs mean |treat − control| (thin horizontal bars, values at the tips)."""
    W, LW, BH, GAP, T = 820, 200, 14, 6, 10
    vmax = max(max(r["noise"], r["effect"]) for r in rows) * 1.25
    X = lambda v: LW + (W - LW - 90) * v / vmax
    H = T + len(rows) * (2 * BH + GAP + 22) + 10
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Treatment effect versus control noise, by field">']
    y = T
    for r in rows:
        fl = LABEL[r["field"]]
        s.append(f'<text class="rowlab" x="{LW - 12}" y="{y + BH + 6}" text-anchor="end">{E(fl)}</text>')
        for key, cls, name in (("noise", "c1", "control run-to-run spread"), ("effect", "c2", "mean |treat − control|")):
            w = X(r[key]) - LW
            s.append(f'<path class="{cls} solid bar" d="M{LW},{y} h{max(w - 4, 0):.1f} q4,0 4,4 v{BH - 8} q0,4 -4,4 h{-max(w - 4, 0):.1f} Z"/>'
                     f'<text class="val" x="{LW + w + 6:.1f}" y="{y + BH - 3}">{100 * r[key]:.2f} pp</text>'
                     f'<rect class="hit" x="{LW}" y="{y - 3}" width="{max(w, 24):.1f}" height="{BH + 6}" tabindex="0" '
                     f'data-tip="{E(f"{100 * r[key]:.2f} pp|{name}|{fl}")}"/>')
            y += BH + GAP
        y += 22 - GAP
    s.append("</svg>")
    return "".join(s)


def means(d):
    by = d["by"]
    return (by[by.arm == "control"].set_index("option"), by[by.arm == "treat"].set_index("option"))


def minibar(v, vmax, cls):
    w = max(2, 120 * v / vmax)
    return (f'<svg class="mb" viewBox="0 0 124 10" aria-hidden="true"><rect class="mbt" x="0" y="2" width="124" height="6" rx="3"/>'
            f'<rect class="{cls} solid bar" x="0" y="2" width="{w:.1f}" height="6" rx="3"/></svg>')


def arm_compare(d, top=5):
    """Side by side: what each arm predicts (named discoveries with people and probabilities, plus Other)."""
    opts = d["question"]["options"]
    C, T = means(d)
    other = len(opts)
    rc = C.drop(index=other).sort_values("mean", ascending=False)
    rt = T.drop(index=other).sort_values("mean", ascending=False)
    rank_c = {i: k for k, i in enumerate(rc.index, 1)}
    vmax = max(rc["mean"].max(), rt["mean"].max())
    cols = []
    for arm, R, M, cls, title in (("control", rc, C, "c1", "Control — no context"), ("treat", rt, T, "c2", "Treat — with profile cards")):
        i0 = R.index[0]
        o0 = opts[i0 - 1]
        lst = ""
        for k, i in enumerate(R.index[:top], 1):
            o = opts[i - 1]
            move = ""
            if arm == "treat" and rank_c[i] != k:
                move = f"<span class='mv'>{'▲' if rank_c[i] > k else '▼'} {abs(rank_c[i] - k)} vs control</span>"
            lst += (f"<li><div class='opt'><b>{k}.</b> {E(short(o, 120))}<div class='ppl'>{E(people_of(o))}</div></div>"
                    f"<div class='pv'>{pct(M.loc[i, 'mean'])}{minibar(M.loc[i, 'mean'], vmax, cls)}{move}</div></li>")
        cols.append(
            f"<div class='card arm'><div class='armh'>{legend([(cls, 'circle' if arm == 'control' else 'tri', title)])}</div>"
            f"<div class='lead'><div class='tl'>Most likely named discovery</div><div class='leadp'>{pct(M.loc[i0, 'mean'])}</div>"
            f"<div class='leadd'>{E(short(o0, 160))}</div><div class='ppl'>{E(people_of(o0))}</div>"
            f"<div class='td'>mean of {int(M.loc[i0, 'n'])} runs; range {pct(M.loc[i0, 'min'])}–{pct(M.loc[i0, 'max'])}</div></div>"
            f"<div class='oth'>“Other” (a discovery not on the list): <b>{pct(M.loc[other, 'mean'])}</b></div>"
            f"<ol class='rk'>{lst}</ol></div>")
    return "<h4 class='sec'>What each arm predicts</h4><div class='two'>" + "".join(cols) + "</div>"


def diff_list(d, top=5):
    """The largest control → treat differences, with the people and whether they exceed the control range."""
    opts = d["question"]["options"]
    e = d["eff"][d["eff"].arm == "treat"].assign(ad=lambda x: x["diff"].abs()).sort_values("ad", ascending=False).head(top)
    li = ""
    for r in e.itertuples():
        o = opts[r.option - 1]
        name = "Other" if o == "Other" else short(o, 120)
        badge = ("<span class='bd out'>outside the control range</span>" if r.outside_control_range
                 else "<span class='bd'>within the control range</span>")
        li += (f"<li><div class='opt'><b>{E(name)}</b><div class='ppl'>{E(people_of(o))}</div></div>"
               f"<div class='chg'><span class='from'>{pct(r.control_mean)}</span> → <span class='to'>{pct(r.arm_mean)}</span>"
               f"<span class='dl'>{'▲' if r.diff > 0 else '▼'} {pp(r.diff, 1)}</span>{badge}"
               f"<div class='td'>control range {pct(r.control_min)}–{pct(r.control_max)}</div></div></li>")
    return ("<h4 class='sec'>Where control and treat differ</h4><div class='card'><p class='muted'>The five largest changes "
            "(treat mean − control mean). A change counts as larger than run-to-run noise only when the treat mean lies outside "
            "the range of the control runs.</p><ol class='dlist'>" + li + "</ol></div>")


def inline_md(t):
    """Escape, then **bold**, `code`, and [text](http…) links (other link targets become plain text)."""
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener noreferrer nofollow" target="_blank">\1</a>', t)
    t = re.sub(r"\[([^\]]+)\]\((#[^)\s]*)\)", r"\1", t)
    return t


def writeup_html(text):
    """Markdown of a Preseen write-up (headings, paragraphs, lists, pipe tables, links); model output, rendered as data."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[2:]]
            out.append("<div class='tw'><table><thead><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table></div>")
            continue
        if re.match(r"^#{1,4} ", ln):
            out.append(f"<h5>{inline_md(ln.lstrip('#').strip())}</h5>")
        elif re.match(r"^\s*[-*] ", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                items.append(re.sub(r"^\s*[-*] ", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline_md(x)}</li>" for x in items) + "</ul>")
            continue
        elif re.match(r"^\s*\d+\. ", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\. ", lines[i]):
                items.append(re.sub(r"^\s*\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline_md(x)}</li>" for x in items) + "</ol>")
            continue
        elif ln.strip():
            para = [ln.strip()]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#{1,4} |\s*[-*] |\s*\d+\. |\|)", lines[i + 1]):
                i += 1
                para.append(lines[i].strip())
            out.append(f"<p>{inline_md(' '.join(para))}</p>")
        i += 1
    return "\n".join(out)


def tldr(text):
    m = re.search(r"^## TL;DR\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else text[:600]


def reasoning(d):
    """Why each arm ranks the discoveries as it does: our summary, each run's TL;DR (verbatim), the full write-ups."""
    f = d["field"]
    note = HERE / "results" / f / "reasoning_summary.md"
    runs = []
    for p in sorted((HERE / "preseen_exp" / f / "runs").glob("*.json")):
        t = json.loads(p.read_text())
        if t.get("status") == "completed":
            arm, rep = p.name.split("_rep")[0], int(p.name.split("_rep")[1][:2])
            runs.append((arm, rep, t["forecast"].get("write_up") or "", t.get("created_at", "")[:16].replace("T", " ")))
    cols = []
    for arm, cls, title in (("control", "c1", "Control — no context"), ("treat", "c2", "Treat — with profile cards")):
        items = "".join(f"<div class='tldr'><div class='td'>{arm} run {rep} · submitted {E(ts)} UTC</div>{writeup_html(tldr(w))}</div>"
                        for a, rep, w, ts in runs if a == arm)
        cols.append(f"<div class='card'><div class='armh'>{legend([(cls, 'circle' if arm == 'control' else 'tri', title)])}</div>"
                    f"<p class='muted'>The TL;DR of every run, in the forecaster’s own words.</p>{items}</div>")
    full = "".join(f"<details class='wu'><summary>{E(arm)} run {rep} — full write-up ({len(w):,} characters)</summary>"
                   f"<div class='wubody'>{writeup_html(w)}</div></details>" for arm, rep, w, ts in runs)
    summary = (f"<div class='card'><h4>Summary of the reasoning</h4>{md_to_html(note.read_text())}</div>" if note.exists() else "")
    return ("<h4 class='sec'>Why each arm ranks the discoveries this way</h4>" + summary + "<div class='two'>" + "".join(cols)
            + "</div><div class='card'><h4>Full write-ups</h4><p class='muted'>Each run’s final write-up as returned by Preseen "
              "(model output, shown as data; links point to the sources it cited).</p>" + full + "</div>")


# ---------------------------------------------------------------- page sections

def tiles(items):
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><div class="tl">{E(a)}</div><div class="tv">{E(b)}</div>'
        + (f'<div class="td">{E(c)}</div>' if c else "") + "</div>" for a, b, c in items) + "</div>"


def legend(items):
    return '<div class="legend">' + "".join(
        f'<span class="lk"><svg width="18" height="12" aria-hidden="true">'
        + (f'<circle class="{c} solid" cx="9" cy="6" r="5"/>' if shape == "circle" else
           f'<path class="{c} solid" d="{tri(9, 7, 5.5)}"/>' if shape == "tri" else
           f'<rect class="{c} solid bar" x="1" y="2" width="16" height="8" rx="2"/>' if shape == "rect" else
           f'<rect class="band" x="1" y="2" width="16" height="8" rx="2"/>')
        + f"</svg>{E(t)}</span>" for c, shape, t in items) + "</div>"


def field_panel(d):
    f = d["field"]
    head = f'<h3>{E(LABEL[f])}</h3>'
    if not d["has"]:
        st = d["state"]["runs"]
        done = sum(r.get("status") == "completed" for r in st)
        return head + f'<p class="muted">Results pending: {done} of {len(st)} submitted runs completed when this page was built.</p>'
    S, opts = d["summary"], d["question"]["options"]
    T = S["treat"]
    e = d["eff"][d["eff"].arm == "treat"]
    n = S["runs"]
    out = [head, tiles([
        ("Control run-to-run spread", pp(S["control_run_to_run_mean_abs_diff"], 2, False), "mean |control − control| per option"),
        ("Mean |treat − control|", pp(T["mean_abs_diff_vs_control"], 2, False),
         f'{T["mean_abs_diff_vs_control"] / S["control_run_to_run_mean_abs_diff"]:.2f} × the control spread'),
        ("Options outside the control range", f'{T["options_outside_control_range"]} of {len(opts)}', ""),
        ("“Other”", f'{pct(T["other_control"])} → {pct(T["other_treat"])}', "control → treat"),
        ("Rank correlation", f'{T["spearman_rank_control_vs_arm"]:.2f}', "Spearman, control vs treat means"),
        ("Runs", f'{n.get("control", 0)} control · {n.get("treat", 0)} treat', "control 1 before any context"),
    ])]
    out += [arm_compare(d), diff_list(d), reasoning(d)]
    out += ['<h4 class="sec">All options</h4><figure class="card"><figcaption><b>Probability of each option, by arm.</b> Hollow marks: individual runs; '
            'filled marks: mean over runs. Hover or focus a mark for its value.</figcaption>',
            legend([("c1", "circle", f'Control (no context, {n.get("control", 0)} runs)'),
                    ("c2", "tri", f'Treat (profile cards, {n.get("treat", 0)} runs)')]),
            dot_plot(d), "</figure>"]
    out += ['<figure class="card"><figcaption><b>Treat minus control per option.</b> The grey bar is the control arm’s '
            'run-to-run range (minimum to maximum over the control runs), centred on the control mean; a marker outside '
            'the bar moved by more than the control runs differ from each other.</figcaption>',
            legend([("c2", "tri", "Treat mean − control mean"), ("band", "band", "Control range (min–max) around its mean")]),
            effect_plot(d), "</figure>"]
    rows = []
    for r in e.sort_values("option").itertuples():
        o = opts[r.option - 1]
        cell = "Other" if o == "Other" else (f"{E(short(o, 200))}<br><span class='muted'>{E(people_of(o))}</span>")
        rows.append(f"<tr><td>{r.option}</td><td>{cell}</td>"
                    f"<td class='num'>{pct(r.control_mean)}</td><td class='num'>{pct(r.control_min)}–{pct(r.control_max)}</td>"
                    f"<td class='num'>{pct(r.arm_mean)}</td><td class='num'>{pp(r.diff)}</td>"
                    f"<td>{'yes' if r.outside_control_range else ''}</td></tr>")
    out.append('<details class="card"><summary>Table view: probabilities and differences by option</summary><div class="tw"><table>'
               "<thead><tr><th>#</th><th>Option (discovery and people)</th><th>Control mean</th><th>Control range</th><th>Treat mean</th>"
               "<th>Treat − control</th><th>Outside range</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div></details>")
    t = d["terms"]
    keys = [("sub: supplied bibliometrics", "References to the supplied bibliometrics"), ("sub: percentile", "“percentile”"),
            ("sub: patent", "“patent” / “invention”"), ("sub: textbook/book", "“textbook” / “book”"),
            ("sub: disruption", "“disruption”"), ("sub: co-author", "“co-author”"), ("sub: laureate", "“laureate”"),
            ("supplied bibliometrics", "Final write-up: references to the supplied bibliometrics")]
    trs = "".join(f"<tr><td>{E(b)}</td><td class='num'>{t.loc['control', a]:.2f}</td><td class='num'>{t.loc['treat', a]:.2f}</td></tr>"
                  for a, b in keys if a in t.columns)
    q = "".join(f"<blockquote>{E(x)}</blockquote>" for x in S.get("uptake_quotes", []))
    out.append('<div class="two"><div class="card"><h4>Did the forecaster use the cards?</h4>'
               '<p>Mentions per run in the four subforecast write-ups (and in the final write-up, last row).</p>'
               '<div class="tw"><table><thead><tr><th>Term</th><th>Control</th><th>Treat</th></tr></thead><tbody>' + trs +
               '</tbody></table></div></div><div class="card"><h4>How the treat subforecasts describe the cards</h4>'
               '<p class="muted">Sentences quoted from the treat runs’ subforecast write-ups (model output, shown as data).</p>'
               + q + "</div></div>")
    cs, cv = S.get("exploratory_card_strength", {}), S["committee_vs_preseen"]
    imp = cs.get("impact_share", {})
    sub = S.get("subforecast_mean_abs_diff", {})
    out.append('<div class="two"><div class="card"><h4>Committee versus forecaster (control arm)</h4><ul>'
               f'<li>Spearman correlation of the committee’s Borda score with the control probabilities: <b>{cv["spearman_borda_vs_control"]:.2f}</b></li>'
               f'<li>With the number of models nominating: <b>{cv["spearman_n_models_vs_control"]:.2f}</b></li>'
               f'<li>Mean control probability of options nominated by all three models: <b>{pct(cv["control_mean_cross_model_consensus"])}</b>'
               + (f'; by one model only: <b>{pct(cv["control_mean_single_model"])}</b>' if cv.get("control_mean_single_model") is not None else "")
               + '</li></ul></div><div class="card"><h4>Further diagnostics</h4><ul>'
               f'<li>Entropy of the forecast: {T["entropy_bits_control"]:.2f} → {T["entropy_bits_treat"]:.2f} bits</li>'
               + (f'<li>Time drift, control run 1 (before any context) vs later control runs: {pp(S["drift_control_rep1_vs_later_mean_abs_diff"], 2, False)} per option</li>'
                  if "drift_control_rep1_vs_later_mean_abs_diff" in S else "")
               + (f'<li>Mean |treat − control| within subforecasts 1–4: ' + ", ".join(pp(sub[k], 2, False) for k in sorted(sub)) + "</li>" if sub else "")
               + (f'<li><i>Exploratory, not pre-specified:</i> Spearman correlation between an option’s shift and how its people '
                  f'compare with the field’s laureates on impact: {imp["spearman"]:.2f} (p = {imp["p"]:.2f}, n = {imp["n"]})</li>' if imp else "")
               + "</ul></div></div>")
    return "\n".join(out)


def candidate_table(d):
    rows = "".join(
        f"<tr><td>{o['rank']}</td><td>{E(short(o['discovery'], 100))}</td><td>{E(', '.join(p['name'] for p in o['people']))}</td>"
        f"<td class='num'>{o['score']:.2f}</td><td class='num'>{o['n_models']}</td><td class='num'>{o['n_personas']}</td>"
        f"<td>{'all three' if o['consensus'] == 'cross-model consensus' else ''}</td></tr>"
        for o in d["cand"] if "score" in o)
    return ('<div class="tw"><table><thead><tr><th>#</th><th>Discovery</th><th>People shown</th><th>Borda score</th>'
            '<th>Models</th><th>Personas</th><th>Consensus</th></tr></thead><tbody>' + rows + "</tbody></table></div>")


CSS = r"""
:root{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;
--band:#e1e0d9;--s1:#2a78d6;--s2:#eb6834;--border:rgba(11,11,11,.10);--accent:#2a78d6;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--surface:#1a1a19;--page:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--axis:#383835;--band:#383835;--s1:#3987e5;--s2:#d95926;--border:rgba(255,255,255,.10);--accent:#3987e5;color-scheme:dark}}
:root[data-theme="dark"]{--surface:#1a1a19;--page:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;
--band:#383835;--s1:#3987e5;--s2:#d95926;--border:rgba(255,255,255,.10);--accent:#3987e5;color-scheme:dark}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:24px 16px 64px}
header h1{font-size:28px;line-height:1.2;margin:0 0 6px}header .sub{color:var(--ink2);margin:0}
nav.top{position:sticky;top:0;z-index:5;background:var(--page);border-bottom:1px solid var(--border);margin:18px -16px 0;padding:8px 16px;
display:flex;gap:16px;flex-wrap:wrap;align-items:center}
nav.top a{color:var(--ink2);text-decoration:none;font-size:14px}nav.top a:hover{color:var(--ink)}
nav.top button{margin-left:auto}
h2{font-size:22px;margin:40px 0 10px}h3{font-size:19px;margin:22px 0 10px}h4{font-size:16px;margin:0 0 8px}h5{font-size:14px;margin:12px 0 4px}
p{margin:0 0 10px}.muted{color:var(--muted)}a{color:var(--accent)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;margin:12px 0}
figure.card{margin:12px 0}figcaption{color:var(--ink2);font-size:14px;margin-bottom:8px}
.hero{display:flex;gap:24px;align-items:flex-end;flex-wrap:wrap}
.hero .big{font-size:56px;font-weight:600;line-height:1}.hero .cap{color:var(--ink2);max-width:520px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin:10px 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px}
.tl{color:var(--ink2);font-size:13px}.tv{font-size:22px;font-weight:600;margin-top:2px}.td{color:var(--muted);font-size:12px;margin-top:2px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 4px}
button{font:inherit;font-size:14px;color:var(--ink);background:var(--surface);border:1px solid var(--border);border-radius:999px;
padding:6px 14px;cursor:pointer}button[aria-selected="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.panel[hidden]{display:none}
svg{width:100%;height:auto;display:block}
svg text{fill:var(--ink);font-size:12px}svg .tick,svg .val{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
svg .rowlab{fill:var(--ink);font-size:12.5px}svg .rowsub{fill:var(--muted);font-size:11px}
.grid{stroke:var(--grid);stroke-width:1}.axis{stroke:var(--axis);stroke-width:1}.zero{stroke:var(--axis);stroke-width:1.5}
.band{fill:var(--band)}
.c1.solid{fill:var(--s1);stroke:var(--surface);stroke-width:2}.c2.solid{fill:var(--s2);stroke:var(--surface);stroke-width:2}
.bar.solid{stroke:none}
.c1.hollow{fill:var(--surface);stroke:var(--s1);stroke-width:1.5}.c2.hollow{fill:var(--surface);stroke:var(--s2);stroke-width:1.5}
.hit{fill:transparent;cursor:pointer}.hit:focus{outline:none;stroke:var(--ink);stroke-width:1.5}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--ink2);margin:0 0 6px}
.lk{display:inline-flex;align-items:center;gap:6px}.lk svg{width:18px;height:12px;flex:none}
#tip{position:fixed;pointer-events:none;z-index:10;background:var(--surface);color:var(--ink);border:1px solid var(--border);
border-radius:8px;padding:8px 10px;font-size:13px;max-width:340px;box-shadow:0 4px 18px rgba(0,0,0,.12);display:none}
#tip b{display:block;font-size:15px}#tip .t2{color:var(--ink2)}#tip .t3{color:var(--muted);font-size:12px;margin-top:2px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media (max-width:760px){.two{grid-template-columns:1fr}}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);vertical-align:top}th{color:var(--ink2);font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
details summary{cursor:pointer;color:var(--ink2);font-weight:600}
blockquote{margin:8px 0;padding:6px 12px;border-left:3px solid var(--grid);color:var(--ink2);font-size:14px}
.steps{counter-reset:s;list-style:none;padding:0;margin:0}.steps>li{counter-increment:s;position:relative;padding-left:42px;margin:0 0 18px}
.steps>li::before{content:counter(s);position:absolute;left:0;top:0;width:28px;height:28px;border-radius:50%;background:var(--ink);
color:var(--surface);display:flex;align-items:center;justify-content:center;font-weight:600;font-size:14px}
.cardnote{background:var(--page);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-size:13.5px;max-height:520px;overflow:auto}
.cardnote h4{font-size:15px}.cardnote ul,.cardnote ol{padding-left:20px;margin:4px 0 8px}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0 4px}
.flow span{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:13px}
.flow i{color:var(--muted);font-style:normal}
h4.sec{font-size:17px;margin:22px 0 6px}.tldr{border-top:1px solid var(--grid);padding:8px 0}.tldr p{font-size:14px;margin:4px 0}
details.wu{border-top:1px solid var(--grid);padding:8px 0}details.wu summary{font-weight:500}
.wubody{font-size:14px;max-height:640px;overflow:auto;padding:8px 4px}.wubody h5{font-size:14.5px;margin:14px 0 4px}
.wubody table{font-size:12.5px}
.arm .armh .legend{font-size:15px;color:var(--ink);font-weight:600;margin-bottom:10px}
.lead{border-bottom:1px solid var(--grid);padding-bottom:10px;margin-bottom:8px}
.leadp{font-size:40px;font-weight:600;line-height:1.1;margin-top:2px}.leadd{font-weight:600;margin-top:4px}
.ppl{color:var(--ink2);font-size:13px}.oth{font-size:14px;color:var(--ink2);margin:6px 0 8px}
ol.rk,ol.dlist{list-style:none;padding:0;margin:0}
ol.rk li,ol.dlist li{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-top:1px solid var(--grid)}
ol.rk .opt,ol.dlist .opt{flex:1;font-size:14px}.pv{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;font-size:14px}
svg.mb{width:124px;height:10px;display:block;margin:4px 0 0 auto}.mbt{fill:var(--grid)}
.mv{display:block;font-size:12px;color:var(--ink2);margin-top:2px}
.chg{text-align:right;white-space:nowrap;font-size:14px;font-variant-numeric:tabular-nums}
.chg .to{font-weight:600}.dl{display:inline-block;margin-left:10px;font-weight:600}
.bd{display:block;font-size:12px;color:var(--ink2);margin-top:3px}.bd.out{font-weight:600;color:var(--ink)}
@media (max-width:760px){ol.rk li,ol.dlist li{flex-direction:column}.pv,.chg{text-align:left}svg.mb{margin-left:0}}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;background:var(--page);padding:1px 4px;border-radius:4px}
"""

JS = r"""
(function(){
  var tip=document.getElementById('tip');
  function show(el,ev){
    var parts=(el.getAttribute('data-tip')||'').split('|');
    tip.textContent='';
    var b=document.createElement('b');b.textContent=parts[0]||'';tip.appendChild(b);
    if(parts[1]){var s=document.createElement('div');s.className='t2';s.textContent=parts[1];tip.appendChild(s);}
    if(parts[2]){var t=document.createElement('div');t.className='t3';t.textContent=parts[2];tip.appendChild(t);}
    tip.style.display='block';
    var r=el.getBoundingClientRect(),x=ev&&ev.clientX!=null?ev.clientX:r.left+r.width/2,y=ev&&ev.clientY!=null?ev.clientY:r.top;
    var w=tip.offsetWidth,h=tip.offsetHeight;
    tip.style.left=Math.max(8,Math.min(window.innerWidth-w-8,x+14))+'px';
    tip.style.top=Math.max(8,(y-h-12<8?y+18:y-h-12))+'px';
  }
  function hide(){tip.style.display='none';}
  document.querySelectorAll('[data-tip]').forEach(function(el){
    el.addEventListener('pointermove',function(e){show(el,e);});
    el.addEventListener('pointerleave',hide);
    el.addEventListener('focus',function(){show(el,null);});
    el.addEventListener('blur',hide);
  });
  document.querySelectorAll('.tabs').forEach(function(bar){
    var btns=bar.querySelectorAll('button');
    btns.forEach(function(btn){btn.addEventListener('click',function(){
      btns.forEach(function(b){b.setAttribute('aria-selected',b===btn?'true':'false');
        var p=document.getElementById(b.getAttribute('aria-controls'));if(p){p.hidden=(b!==btn);}});
      try{localStorage.setItem('tab-'+bar.id,btn.id);}catch(e){}
    });});
    try{var saved=localStorage.getItem('tab-'+bar.id);if(saved&&document.getElementById(saved)){document.getElementById(saved).click();}}catch(e){}
  });
  var tb=document.getElementById('theme');
  function cur(){return document.documentElement.getAttribute('data-theme')||(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}
  function label(){tb.textContent=cur()==='dark'?'Light theme':'Dark theme';}
  try{var th=localStorage.getItem('theme');if(th){document.documentElement.setAttribute('data-theme',th);}}catch(e){}
  label();
  tb.addEventListener('click',function(){var n=cur()==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);
    try{localStorage.setItem('theme',n);}catch(e){}label();});
})();
"""


def build(out_path):
    D = {f: load_field(f) for f in FIELDS}
    done = [f for f in FIELDS if D[f]["has"]]
    pooled = [{"field": f, "noise": D[f]["summary"]["control_run_to_run_mean_abs_diff"],
               "effect": D[f]["summary"]["treat"]["mean_abs_diff_vs_control"]} for f in done]
    n_runs = sum(len(D[f]["state"]["runs"]) for f in FIELDS)
    n_done = sum(r.get("status") == "completed" for f in FIELDS for r in D[f]["state"]["runs"])
    ratio = sum(r["effect"] for r in pooled) / sum(r["noise"] for r in pooled) if pooled else None
    price = CFG["pricing"]
    tok = {}
    for f in FIELDS:
        for b in D[f]["ballots"]:
            t = tok.setdefault(b["model"], [0, 0]); t[0] += b.get("input_tokens", 0); t[1] += b.get("output_tokens", 0)
    cost = sum((v[0] * price[m]["input"] + v[1] * price[m]["output"]) / 1e6 for m, v in tok.items())
    ref = pd.read_csv(HERE / "cards" / "laureate_reference.csv")
    people = {f: len(list(csv.DictReader(open(HERE / "people" / f"{f}_identity.csv")))) for f in FIELDS}
    gen = pd.Timestamp.now(tz="America/Chicago").strftime("%d %B %Y, %H:%M %Z")

    H = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>Nobel 2026 context experiment</title>", f"<style>{CSS}</style></head><body><div id='tip' role='status'></div><div class='wrap'>",
         "<header><h1>Do bibliometric profiles change an AI forecast of the 2026 Nobel Prizes?</h1>",
         f"<p class='sub'>A controlled context experiment on the Preseen forecasting system · Physiology or Medicine, Physics, Chemistry · "
         f"built {E(gen)} · {n_done} of {n_runs} runs completed</p></header>",
         "<nav class='top'><a href='#overview'>Overview</a><a href='#results'>Results by field</a><a href='#process'>How the experiment works</a>"
         "<a href='#cards'>Card examples</a><a href='#caveats'>Caveats</a><a href='#files'>Files</a>"
         "<button id='theme' type='button'>Dark theme</button></nav>"]

    # overview
    H.append("<section id='overview'><h2>Overview</h2>")
    H.append("<div class='card'><p>For each prize, the same multiple-choice question (“Which discovery will the 2026 Nobel Prize in … be "
             "awarded for?”, twelve candidate discoveries plus “Other”) was created twice on Preseen. The <b>control</b> question has no "
             "context. The <b>treat</b> question carries one profile card for every person named in the options, built from OpenAlex, "
             "PatentsView and Reliance on Science, plus a definitions note. Both were run repeatedly and interleaved; the question is "
             "whether the cards move the forecast by more than repeated control runs differ from each other.</p></div>")
    if pooled:
        H.append("<div class='card hero'><div class='big'>" + f"{ratio:.2f}×" + "</div><div class='cap'><b>Mean |treat − control| as a "
                 "multiple of the control run-to-run spread</b>, summed over the fields with results (" + ", ".join(LABEL[f] for f in done)
                 + "). Below 1 means that, on average, adding the cards moved an option less than two control runs differ from each other.</div></div>")
        H.append("<figure class='card'><figcaption><b>Treatment effect versus control noise, by field</b> (percentage points per option, "
                 "averaged over the 13 options).</figcaption>" + legend([("c1", "rect", "Control run-to-run spread"),
                 ("c2", "rect", "Mean |treat − control|")]) + pooled_bars(pooled) + "</figure>")
    rows = ""
    for f in FIELDS:
        if not D[f]["has"]:
            rows += f"<tr><td>{E(LABEL[f])}</td><td colspan='5' class='muted'>pending</td></tr>"
            continue
        S, T = D[f]["summary"], D[f]["summary"]["treat"]
        rows += (f"<tr><td>{E(LABEL[f])}</td><td class='num'>{pp(S['control_run_to_run_mean_abs_diff'], 2, False)}</td>"
                 f"<td class='num'>{pp(T['mean_abs_diff_vs_control'], 2, False)}</td><td class='num'>{T['options_outside_control_range']}</td>"
                 f"<td class='num'>{pct(T['other_control'])} → {pct(T['other_treat'])}</td>"
                 f"<td class='num'>{T['spearman_rank_control_vs_arm']:.2f}</td></tr>")
    pr = ""
    for f in FIELDS:
        if not D[f]["has"]:
            pr += f"<tr><td>{E(LABEL[f])}</td><td colspan='3' class='muted'>pending</td></tr>"
            continue
        opts = D[f]["question"]["options"]
        C, T = means(D[f])
        cells = []
        for M in (C, T):
            R = M.drop(index=len(opts)).sort_values("mean", ascending=False)
            i0 = R.index[0]
            cells.append(f"<b>{pct(M.loc[i0, 'mean'])}</b> {E(short(opts[i0 - 1], 90))}<br><span class='muted'>{E(people_of(opts[i0 - 1]))}</span>")
        pr += (f"<tr><td>{E(LABEL[f])}</td><td>{cells[0]}</td><td>{cells[1]}</td>"
               f"<td class='num'>{pct(C.loc[len(opts), 'mean'])} → {pct(T.loc[len(opts), 'mean'])}</td></tr>")
    H.append("<h3>Who each arm predicts</h3><div class='card'><div class='tw'><table><thead><tr><th>Field</th>"
             "<th>Control: most likely named discovery</th><th>Treat: most likely named discovery</th><th>“Other” control → treat</th>"
             "</tr></thead><tbody>" + pr + "</tbody></table></div></div>")
    H.append("<h3>Effect versus noise</h3><div class='card'><div class='tw'><table><thead><tr><th>Field</th><th>Control spread</th><th>Mean |treat − control|</th>"
             "<th>Options outside control range</th><th>“Other” control → treat</th><th>Rank correlation</th></tr></thead><tbody>"
             + rows + "</tbody></table></div></div></section>")

    # results by field
    H.append("<section id='results'><h2>Results by field</h2><div class='tabs' id='fieldtabs' role='tablist'>")
    for k, f in enumerate(FIELDS):
        H.append(f"<button type='button' role='tab' id='tab-{f}' aria-controls='panel-{f}' aria-selected='{'true' if k == 0 else 'false'}'>{TAB[f]}</button>")
    H.append("</div>")
    for k, f in enumerate(FIELDS):
        H.append(f"<div class='panel' id='panel-{f}' role='tabpanel' aria-labelledby='tab-{f}'{'' if k == 0 else ' hidden'}>"
                 + field_panel(D[f]) + "</div>")
    H.append("</section>")

    # process
    pers = "".join(f"<tr><td>{E(LABEL[f])}</td><td>{E('; '.join(CFG['fields'][f]['personas']))}</td></tr>" for f in FIELDS)
    manual = {f: D[f]["manual"] for f in FIELDS}
    mrows = "".join(f"<tr><td>{E(LABEL[f])}</td>" + "".join(f"<td class='num'>{len(manual[f].get(k) or [])}</td>" for k in
                    ("split", "aliases", "wording_from", "people", "deceased")) + "</tr>" for f in FIELDS)
    trows = "".join(f"<tr><td><code>{E(m)}</code></td><td class='num'>{v[0]:,}</td><td class='num'>{v[1]:,}</td>"
                    f"<td class='num'>${(v[0] * price[m]['input'] + v[1] * price[m]['output']) / 1e6:.2f}</td></tr>" for m, v in tok.items())
    refrows = "".join(f"<tr><td>{E(LABEL[f])}</td><td class='num'>{len(g)}</td><td class='num'>{g.impact_median.median():.3f}</td>"
                      f"<td class='num'>{pct(g.top10.median())}</td><td class='num'>{g.citing_inventions.median():.0f}</td>"
                      f"<td class='num'>{g.own_patents.median():.0f}</td><td class='num'>{g.citing_books.median():.0f}</td></tr>"
                      for f, g in ((f, ref[ref.field == f]) for f in FIELDS))
    q = D["medicine"]["question"]
    H.append("<section id='process'><h2>How the experiment works</h2>"
             "<div class='flow'><span>Virtual committee<br><i>personas × 3 LLMs</i></span><i>→</i><span>Borda aggregation<br><i>+ merge review</i></span>"
             "<i>→</i><span>Preseen question<br><i>12 discoveries + Other</i></span><i>→</i><span>Control question<br><i>no context</i></span>"
             "<i>+</i><span>Treat question<br><i>+ profile cards</i></span><i>→</i><span>Repeated, interleaved runs<br><i>→ analysis</i></span></div>"
             "<p class='muted'>Profile branch: names in the options → OpenAlex author profiles → laureate reference at prize time → fixed-template cards → context notes on the treat question.</p>"
             "<ol class='steps'>")
    H.append("<li><h3>A virtual Nobel committee nominates candidates</h3>"
             "<p>Each persona is “a senior member of the Nobel Committee for ⟨field⟩ whose own expertise is ⟨specialty⟩”, mirroring the "
             "specialties of the actual 2026 committees (no names, no impersonation). Every persona was run once on each of three models "
             "from different providers — Anthropic <code>claude-opus-5-5</code>, OpenAI <code>gpt-5.5-2026-04-23</code>, Google "
             "<code>gemini-3.1-pro-preview</code> — with the same prompt, provider-default settings, and no tools, web search or grounding. "
             "The prompt gave the date context, the rules of the prize (the will’s wording, at most three living laureates, a possible "
             "split between two discoveries) and the field’s prizes 2000–2025 with their official motivations, and asked for up to five "
             "ranked nominations as strict JSON (discovery in the style of a prize motivation, 1–3 living people with affiliations, key "
             "papers if known, a two-sentence rationale).</p>"
             f"<div class='tw'><table><thead><tr><th>Field</th><th>Persona specialties</th></tr></thead><tbody>{pers}</tbody></table></div>"
             f"<p>All {sum(len(D[f]['ballots']) for f in FIELDS)} persona × model ballots were valid on the first attempt (run on 1 October 2026, "
             f"14:17–14:36 CDT). Total committee cost: <b>${cost:.2f}</b>.</p>"
             f"<div class='tw'><table><thead><tr><th>Model</th><th>Input tokens</th><th>Output tokens</th><th>Cost</th></tr></thead><tbody>{trows}</tbody></table></div></li>")
    H.append("<li><h3>Ballots are aggregated into twelve options</h3>"
             "<p>A nomination at rank r earns 6 − r points; each model’s points are divided by its number of valid ballots, so the three "
             "models count equally (S<sub>j</sub> = Σ<sub>m</sub> P<sub>m,j</sub> / B<sub>m</sub>). Nominations that share a person "
             "(first initial + surname, split by middle initials when two people share a key) are merged automatically; a recorded review "
             "then splits umbrella nominations that chain two discoveries, splits discoveries linked only through one person, fixes wording "
             "taken from an outlier, settles ties for the third person, and records aliases. Every decision and its reason is in "
             "<code>committee/&lt;field&gt;/merges.yaml</code> and <code>review.md</code>.</p>"
             f"<div class='tw'><table><thead><tr><th>Field</th><th>Splits</th><th>Aliases</th><th>Wording</th><th>People (ties)</th><th>Deceased</th></tr></thead><tbody>{mrows}</tbody></table></div>"
             "<p><b>Living check.</b> Every shown person was screened against Wikidata and checked on the web where needed; three had died "
             "and were replaced in the option text by the next living person: Joel F. Habener (GLP-1, d. 2025-12-28 → Lotte Bjerre Knudsen), "
             "Zelig Eshhar (CAR-T, d. 2025-07-03 → Steven A. Rosenberg), Harald Rose (aberration-corrected electron optics, d. 2026-07-27 → "
             "Ondrej L. Krivanek).</p>"
             "<details><summary>Candidate lists of the three fields</summary>"
             + "".join(f"<h4 style='margin-top:12px'>{E(LABEL[f])}</h4>" + candidate_table(D[f]) for f in FIELDS) + "</details></li>")
    H.append("<li><h3>One question, created twice</h3>"
             f"<p><b>Title:</b> {E(q['title'])}<br><b>Description:</b> {E(q['description'])}<br><b>Resolution:</b> {E(q['resolution_criteria'])}</p>"
             "<p>The question is private, multiple choice, with mutually exclusive and comprehensive options. Its text never mentions the "
             "committee, the models, the profiles or the experiment (checked automatically). Because Preseen context notes attach to a "
             "question and apply to all of its later runs, the arms are two identically defined questions; the client verifies after "
             "creation that their definitions are identical.</p></li>")
    H.append("<li><h3>Author profiles of every named person</h3>"
             f"<p>{sum(people.values())} people (Medicine {people['medicine']}, Physics {people['physics']}, Chemistry {people['chemistry']}; "
             "94 distinct) were resolved to OpenAlex author ids with the repository’s name pipeline; sixteen doubtful or unresolved cases "
             "were decided by hand with candidate tables, OpenAlex topics and ORCID records (e.g. one Emmanuel Mignot profile carries a "
             "namesake’s ORCID; Ching W. Tang and Steven A. Van Slyke are split across several ids). Each person was then profiled on Slurm: "
             "every work and patent scored against its cohort (5-year citations, disruption, Foundation share, citations from books), "
             "patent-to-paper citations and collaboration networks, for works published and patents granted up to 2021.</p></li>")
    H.append("<li><h3>Cards with a laureate reference</h3>"
             "<p>Each card (about 300–500 words, fixed template) gives the person’s affiliation and option, impact (median 5-year citation "
             "percentile, shares in the cohort top 10 % and 1 %), three defining works, technological translation (citing inventions, own "
             "patents), textbook reach and collaboration (Nobel laureate co-authors, people who are both co-authors and co-inventors). Every "
             "headline number is compared with the field’s 2000–2025 laureates <b>measured at the time of their prize</b> (only works and "
             "citations dated before the prize year). A definitions note, added first, ends with “These are descriptive bibliometric "
             "measures, not forecasts.”</p>"
             f"<div class='tw'><table><thead><tr><th>Field</th><th>Laureates</th><th>Impact median</th><th>Top 10 %</th><th>Citing inventions</th><th>Own patents</th><th>Citing books</th></tr></thead><tbody>{refrows}</tbody></table></div>"
             "<p class='muted'>Medians of the laureate reference, at prize time.</p></li>")
    H.append("<li><h3>Repeated, interleaved runs</h3>"
             "<p>Per field: one control run before any context (first look) → context notes added to the treat question "
             "(<code>treatment=consider</code>, definitions first, cards in a fixed seeded order) → three more runs per arm, interleaved in "
             "a random order, at most three active at a time, with an idempotency key on every request. One run takes about 25 minutes "
             "and combines four subforecasts. All runs finished on 1 October, well before the announcements (5, 6 and 7 October).</p></li>")
    H.append("<li><h3>Analysis</h3>"
             "<p>Per option: mean, standard deviation and range per arm; Δ = treat mean − control mean against the control range; the "
             "<b>control run-to-run spread</b> (mean |p<sub>a</sub> − p<sub>b</sub>| over pairs of control runs, averaged over options) as the "
             "noise band; change in “Other”, entropy, rank correlation; which subforecasts moved; mentions of card measures in the write-ups; "
             "time drift between the first control run and the later ones; agreement between the committee and the control forecast. After "
             "the announcements: the log score of the realised option per arm.</p></li></ol></section>")

    # cards
    ex = [("medicine", "00_definitions.md", "Definitions note (Physiology or Medicine)"), ("medicine", "svetlana-mojsov.md", "Physiology or Medicine — Svetlana Mojsov"),
          ("medicine", "karl-deisseroth.md", "Physiology or Medicine — Karl Deisseroth"), ("physics", "john-b-pendry.md", "Physics — John B. Pendry"),
          ("chemistry", "krzysztof-matyjaszewski.md", "Chemistry — Krzysztof Matyjaszewski")]
    H.append("<section id='cards'><h2>Card examples</h2><p>The notes exactly as attached to the treat questions (rendered from Markdown).</p>"
             "<div class='tabs' id='cardtabs' role='tablist'>")
    for k, (f, fn, lab) in enumerate(ex):
        H.append(f"<button type='button' role='tab' id='ctab-{k}' aria-controls='cpanel-{k}' aria-selected='{'true' if k == 0 else 'false'}'>{E(lab.split(' — ')[-1])}</button>")
    H.append("</div>")
    for k, (f, fn, lab) in enumerate(ex):
        H.append(f"<div class='panel card' id='cpanel-{k}' role='tabpanel'{'' if k == 0 else ' hidden'}><p class='muted'>{E(lab)} · "
                 f"<code>cards/{f}/{fn}</code></p><div class='cardnote'>{md_to_html((HERE / 'cards' / f / fn).read_text())}</div></div>")
    H.append("</section>")

    # caveats
    H.append("<section id='caveats'><h2>Caveats</h2><div class='card'><ul>"
             "<li><b>Few runs.</b> Four control and three treat runs per field give a coarse noise band; the comparison is descriptive, not a significance test.</li>"
             "<li><b>A bundle, no placebo.</b> The cards add many numbers at once; the placebo arm (the same cards with numbers shuffled across people) was implemented but switched off, so “more text about these people” cannot be separated from “these numbers”.</li>"
             "<li><b>The options are the committee’s.</b> Three correlated language models generated them; a prize for another discovery resolves to “Other” in both arms. Three nominees had died after the models’ training data.</li>"
             "<li><b>Profile quality.</b> OpenAlex splits and merges authors; some profiles are thin (Pascal Mayer, Bistritzer, Kurahashi Neilson) or undercounted (Mignot); patent counts from the PatentsView name search and id-matched laureate co-authors may include namesakes.</li>"
             "<li><b>One forecasting system.</b> The results describe Preseen on 1 October 2026; the subforecasts report that they gave the supplied bibliometrics little quantitative weight.</li>"
             "<li><b>Exploratory analyses</b> (the correlation of shifts with the laureate comparison) were not pre-specified.</li></ul>"
             "<p class='muted'>Incidents during implementation (API keys and quotas, the OpenAlex daily budget, a stale shared cache that required one rebuild job, the Wikidata rate limit, a pause of the Preseen submissions) are logged in <code>LOG.md</code> and described in the manuscript.</p></div></section>")
    H.append("<section id='files'><h2>Files</h2><div class='card'><ul>"
             "<li><code>experiment/preseen/SPEC.md</code> protocol · <code>LOG.md</code> every step with time, command, outcome and decision · <code>config.yaml</code></li>"
             "<li><code>committee/&lt;field&gt;/</code> ballots, merges, candidate lists, review · <code>questions/&lt;field&gt;.json</code></li>"
             "<li><code>people/</code> identity tables and decisions · <code>cards/</code> cards and the laureate reference</li>"
             "<li><code>preseen_exp/&lt;field&gt;/</code> client state and every run JSON · <code>results/&lt;field&gt;/</code> analysis tables, figures, Korean summaries</li>"
             "<li><code>manuscript/preseen_nobel2026_experiment.tex</code> the detailed write-up · this page: <code>build_dashboard.py</code></li></ul></div></section>")
    H.append(f"</div><script>{JS}</script></body></html>")
    out_path.write_text("\n".join(H), encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes); fields with results: {done}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(HERE / "results" / "dashboard.html"))
    build(Path(ap.parse_args().out))


if __name__ == "__main__":
    main()
