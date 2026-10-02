#!/usr/bin/env python3
"""build_dashboard_all.py: one self-contained page for the whole Preseen Nobel 2026 experiment (four arms).

    $PY build_dashboard_all.py [--out dashboard_all.html]

Merges Dashboard 1 (preseen/: control vs cards as context) and Dashboard 2 (preseen_cards_main/ +
preseen_cards_balanced/: the two instruction notes) into one page that explains the design, shows the virtual
committee, its candidate lists and a card, and compares the four arms. Charts: only "All options" (per field).
Reads the per-field tables written by preseen_cards_main/analyze_main.py (all four arms), the committee files and
cards of preseen/, and the reasoning summaries of the three context arms. Styles, chart helpers and scripts are
reused from preseen/build_dashboard.py and preseen_cards_main/build_dashboard2.py.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "preseen"))
sys.path.insert(0, str(HERE / "preseen_cards_main"))
import build_dashboard2 as b2  # noqa: E402  (also imports preseen/build_dashboard as b2.bd)

bd = b2.bd
E, pct, pp, short, people_of = bd.E, bd.pct, bd.pp, bd.short, bd.people_of
FIELDS, LABEL, TAB = b2.FIELDS, b2.LABEL, b2.TAB
ARMS = ["control", "cards", "balanced", "main"]
NAME = {"control": "Control", "cards": "Cards as context", "balanced": "Cards as one main source",
        "main": "Cards as the main evidence"}
SHORTNAME = {"control": "control", "cards": "context", "balanced": "one main source", "main": "main evidence"}
SEES = {"control": "The question only.",
        "cards": "The question + a definitions note + one profile card per named person.",
        "balanced": "The same cards + a note: the cards are <i>one of the main</i> sources, weighed comparably with prizes, "
                    "news and predictions, which it should use actively.",
        "main": "The same cards + a note: the cards are <i>the main</i> evidence; prizes, news and predictions only as a "
                "secondary adjustment."}
WHEN = {"control": "4 runs on 1 Oct + 1 on 2 Oct", "cards": "3 runs on 1 Oct", "balanced": "1 run on 2 Oct",
        "main": "1 run on 2 Oct"}
CARD_EXAMPLES = [("medicine", "karl-deisseroth.md", "Card: Karl Deisseroth (Medicine)"),
                 ("medicine", "00_definitions.md", "Definitions note (Medicine)")]
# the arms' copy of the global b2.ARM labels, so the shared chart helpers print the names used on this page
for a in ARMS:
    cls, shape, _, what = b2.ARM[a]
    b2.ARM[a] = (cls, shape, NAME[a], what)


def mean(x):
    return sum(x) / len(x)


def load():
    D = {f: b2.load_field(f) for f in FIELDS}
    for f in FIELDS:
        D[f]["cand"] = json.loads((HERE / "preseen" / "committee" / f / "candidates.json").read_text())["options"]
        D[f]["ballots"] = [json.loads(l) for l in (HERE / "preseen" / "committee" / f / "ballots.jsonl").read_text().splitlines()
                           if l.strip()]
        rc = HERE / "preseen" / "results" / f / "reasoning_summary.md"
        D[f]["reason_cards"] = rc.read_text() if rc.exists() else None
    return D


def glance(D):
    """Rows = measures, columns = arms; each cell: mean over fields (bold) and the three fields."""
    vals = {}
    for f in FIELDS:
        S, by = D[f]["S"], D[f]["by"]
        dev = S["single_run_dev"]
        sc = mean(dev["control"])
        fav = S["control"]["leader"]
        for a in ARMS:
            v = vals.setdefault(a, {})
            v.setdefault("dist", []).append(mean(dev[a]) / sc)
            v.setdefault("out", []).append(S[a]["options_outside_control_range"] if a != "control" else None)
            v.setdefault("fav", []).append(float(by[(by.arm == a) & (by.option == fav)]["mean"].iloc[0]))
            v.setdefault("other", []).append(S[a]["other"])
            v.setdefault("rho", []).append(S[a]["spearman_vs_control"] if a != "control" else None)

    def cell(xs, fmt):
        if any(x is None for x in xs):
            return "<td class='num muted'>–</td>"
        m = fmt(sum(xs) / len(xs)) if fmt is not str else str(sum(xs))
        return f"<td class='num'><b>{m}</b><div class='td'>{' · '.join(fmt(x) for x in xs)}</div></td>"

    x1 = lambda v: f"{v:.1f}×"
    rows = [("How far one run lands from the control mean, in units of a control run’s own distance", "dist", x1),
            ("Options outside the range of the five control runs (of 13)", "out", lambda v: f"{v:.0f}" if v == int(v) else f"{v:.1f}"),
            ("Probability of the control favourite (GLP-1 · optical lattice clocks · sequencing-by-synthesis)", "fav", pct),
            ("“Other” (a discovery not on the list)", "other", pct),
            ("Rank correlation of the 13 options with the control mean", "rho", lambda v: f"{v:.2f}")]
    head = "".join(f"<th>{b2.legend([(a, NAME[a])])}</th>" for a in ARMS)
    body = "".join(f"<tr><td>{E(lab)}</td>" + "".join(cell(vals[a][k], fm) for a in ARMS) + "</tr>" for lab, k, fm in rows)
    return ("<div class='card'><div class='tw'><table class='glance'><thead><tr><th></th>" + head + "</tr></thead><tbody>" + body
            + "</tbody></table></div><p class='muted'>Bold: mean over the three prizes; small: Medicine · Physics · Chemistry. A control "
            "run’s distance is each control run against the mean of the other four (0.75 / 0.71 / 0.59 percentage points per option), "
            "so the control column is 1.0× by construction.</p></div>")


def who_predicts(D):
    pr = ""
    for f in FIELDS:
        S, opts = D[f]["S"], D[f]["question"]["options"]
        cells = []
        for a in ARMS:
            i0, p0 = S[a]["leader"], S[a]["leader_p"]
            cells.append(f"<b>{pct(p0)}</b> {E(short(opts[i0 - 1], 70))}<br><span class='muted'>{E(people_of(opts[i0 - 1]))}</span>")
        pr += (f"<tr><td>{E(LABEL[f])}</td>" + "".join(f"<td>{c}</td>" for c in cells)
               + f"<td class='num'>{' · '.join(pct(S[a]['other']) for a in ARMS)}</td></tr>")
    return ("<h3>Who each arm predicts</h3><div class='card'><div class='tw'><table><thead><tr><th>Field</th>"
            + "".join(f"<th>{NAME[a]}</th>" for a in ARMS)
            + f"<th>“Other” ({' · '.join(SHORTNAME[a] for a in ARMS)})</th></tr></thead><tbody>" + pr
            + "</tbody></table></div><p class='muted'>The most likely named discovery of each arm (mean over its runs) and its "
            "probability.</p></div>")


def candidate_table(d):
    def by(o):
        return "all three models" if o["consensus"] == "cross-model consensus" else f"{o['n_models']} of 3 models"
    rows = "".join(
        f"<tr><td>{o['rank']}</td><td>{E(short(o['discovery'], 110))}</td><td>{E(', '.join(p['name'] for p in o['people']))}</td>"
        f"<td class='num'>{o['score']:.2f}</td><td>{by(o)}</td></tr>"
        for o in d["cand"] if "score" in o)
    return ("<div class='tw'><table><thead><tr><th>#</th><th>Discovery</th><th>People in the option</th><th>Borda score</th>"
            "<th>Nominated by</th></tr></thead><tbody>" + rows + "</tbody></table></div>")


def field_panel(d):
    f, S, opts = d["field"], d["S"], d["question"]["options"]
    dev = S["single_run_dev"]
    sc = mean(dev["control"])
    T = [(NAME[a], f"{mean(dev[a]) / sc:.1f}× · {S[a]['options_outside_control_range']} of 13",
          f"distance from control · options outside the control range; “Other” {pct(S[a]['other'])}") for a in ARMS if a != "control"]
    out = [f"<h3>{E(LABEL[f])}</h3>", bd.tiles(T), b2.arm_compare(d)]
    out += ["<h4 class='sec'>All options</h4><figure class='card'><figcaption><b>Probability of each option, by arm.</b> Hollow marks: "
            "individual runs (five control, three with cards as context); filled marks: the arm’s mean (the two instruction arms have "
            "one run each). Hover or focus a mark for its value.</figcaption>",
            b2.legend([(a, b2.arm_label(a, S["runs"][a])) for a in ARMS]), b2.dot_plot(d), "</figure>"]
    e = d["eff"].sort_values("option")
    rows = "".join(
        f"<tr><td>{r.option}</td><td>{'Other' if opts[r.option - 1] == 'Other' else E(short(opts[r.option - 1], 120)) + '<br><span class=muted>' + E(people_of(opts[r.option - 1])) + '</span>'}</td>"
        f"<td class='num'>{pct(r.control_mean)}<div class='td'>{pct(r.control_min)}–{pct(r.control_max)}</div></td>"
        + "".join(f"<td class='num'>{pct(getattr(r, b2.COLS[a][0]))}{'<span class=out> ●</span>' if getattr(r, f'{a}_outside') else ''}</td>"
                  for a in ("cards", "balanced", "main")) + "</tr>"
        for r in e.itertuples())
    out.append("<details class='card'><summary>Table: probability of every option in the four arms</summary><div class='tw'><table>"
               "<thead><tr><th>#</th><th>Option</th><th>Control (mean, range)</th>"
               + "".join(f"<th>{NAME[a]}</th>" for a in ("cards", "balanced", "main"))
               + "</tr></thead><tbody>" + rows + "</tbody></table></div><p class='muted'>● = outside the range of the five control "
               "runs.</p></details>")
    rs = [("cards", d.get("reason_cards"), "Dashboard 1 summary of the control and context runs"),
          ("balanced", d.get("reason_bal"), None), ("main", d.get("reason"), None)]
    cols = "".join(f"<div class='card'><div class='armh'>{b2.legend([(a, NAME[a])])}</div>{bd.md_to_html(t)}</div>"
                   for a, t, _ in rs if t)
    out.append("<details class='card'><summary>Why the arms differ: how each run used the cards (summaries of the write-ups)"
               f"</summary><div class='three' style='margin-top:10px'>{cols}</div></details>")
    return "\n".join(out)


CSS3 = r"""
.arms4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0}
@media (max-width:1000px){.arms4{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (max-width:600px){.arms4{grid-template-columns:1fr}}
.arms4 .card{margin:0}.arms4 .step{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.arms4 p{margin:6px 0 0;font-size:14px}.arms4 .when{color:var(--muted);font-size:13px;margin-top:8px}
table.glance td:first-child{max-width:300px}table.glance th{vertical-align:bottom}
.dial{display:flex;align-items:center;gap:8px;margin:4px 0 2px;color:var(--muted);font-size:13px}
.dial .bar{flex:1;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--s1),var(--s2),var(--s4),var(--s3))}
.out{color:var(--s3)}
.take{font-size:17px;line-height:1.5}
"""


def build(out_path):
    D = load()
    cfg = yaml.safe_load((HERE / "preseen" / "config.yaml").read_text())
    price = cfg["pricing"]
    tok = {}
    for f in FIELDS:
        for b in D[f]["ballots"]:
            t = tok.setdefault(b["model"], [0, 0]); t[0] += b.get("input_tokens", 0); t[1] += b.get("output_tokens", 0)
    cost = sum((v[0] * price[m]["input"] + v[1] * price[m]["output"]) / 1e6 for m, v in tok.items())
    n_ballots = sum(len(D[f]["ballots"]) for f in FIELDS)
    n_cards = sum(len(list((HERE / "preseen" / "cards" / f).glob("*.md"))) - 1 for f in FIELDS)
    gen = pd.Timestamp.now(tz="America/Chicago").strftime("%d %B %Y, %H:%M %Z")

    H = ["<title>Nobel 2026 Preseen</title>", f"<style>{bd.CSS}{b2.CSS2}{CSS3}</style>",
         "<div id='tip' role='status'></div><div class='wrap'>",
         "<header><h1>Do bibliometric profile cards change an AI forecast of the 2026 Nobel Prizes?</h1>",
         "<p class='sub'>Four arms on the Preseen forecasting system · Physiology or Medicine, Physics, Chemistry · forecasts made on "
         f"1–2 October 2026, before the announcements of 5–7 October · built {E(gen)}</p></header>",
         "<nav class='top'><a href='#overview'>Overview</a><a href='#design'>Design</a><a href='#committee'>Committee &amp; candidates</a>"
         "<a href='#cards'>Cards</a><a href='#results'>Results</a><a href='#caveats'>Caveats</a>"
         "<button id='theme' type='button'>Dark theme</button></nav>"]

    # ------------------------------------------------------------ overview
    H.append("<section id='overview'><h2>Overview</h2><div class='card'><p class='take'>We asked a forecasting AI the same question — "
             "<i>which discovery will this year’s Nobel Prize be awarded for?</i> — four times per prize, changing only what it is shown "
             "and how it is told to use it. Each person named in the options gets a <b>profile card</b> of bibliometric facts (impact, "
             "defining papers, patents, textbooks, collaboration), each compared with past laureates at the time of their prize.</p>"
             "<div class='dial'><span>no cards</span><span class='bar'></span><span>cards as the main evidence</span></div></div>"
             "<div class='arms4'>")
    for k, a in enumerate(ARMS, 1):
        H.append(f"<div class='card'><div class='step'>Arm {k}</div>{b2.legend([(a, NAME[a])])}<p>{SEES[a]}</p>"
                 f"<div class='when'>{WHEN[a]}</div></div>")
    H.append("</div>")
    H.append("<h3>The four arms at a glance</h3>" + glance(D))
    H.append("<div class='card'><p class='take'><b>Reading.</b> Attached as context to consider, the cards move the forecast no more "
             "than repeated runs without them differ from each other. Told that the cards are one of the main sources, the forecaster "
             "moves about halfway: the award favourites lose about half their probability but mostly stay near the top. Told that the "
             "cards are the main evidence, it moves furthest: the favourites collapse and “Other” grows. How much the same cards matter "
             "is set by the instruction, not by the cards alone.</p></div>")
    H.append(who_predicts(D) + "</section>")

    # ------------------------------------------------------------ design
    notes = {}
    for a, p in (("balanced", HERE / "preseen_cards_balanced" / "instruction" / "00_instruction.md"),
                 ("main", HERE / "preseen_cards_main" / "instruction" / "00_instruction.md")):
        t = p.read_text()
        notes[a] = ("".join(f"<p>{E(x.strip())}</p>" for x in t.split("\n") if x.strip() and not x.startswith("- "))
                    + "<ul>" + "".join(f"<li>{E(x[2:].strip())}</li>" for x in t.split("\n") if x.startswith("- ")) + "</ul>")
    q = D["medicine"]["question"]
    H.append("<section id='design'><h2>Design</h2>"
             "<div class='flow'><span>Virtual committee<br><i>22 specialist personas × 3 LLMs</i></span><i>→</i>"
             "<span>Borda count + review<br><i>12 discoveries + “Other” per prize</i></span><i>→</i>"
             f"<span>Profile cards<br><i>{n_cards} people named in the options</i></span><i>→</i>"
             "<span>The same question, one copy per arm<br><i>private, identical wording</i></span><i>→</i>"
             "<span>Runs on Preseen<br><i>~25 min each, 4 subforecasts</i></span><i>→</i>"
             "<span>Compare with control noise<br><i>per option</i></span></div>"
             "<div class='two' style='margin-top:12px'><div class='card'><h4>The question</h4>"
             f"<p><b>{E(q['title'])}</b></p><p class='muted'>{E(q['description'])}</p>"
             "<p>Options: the committee’s twelve discoveries (with up to three living people each) and “Other”. The question resolves on "
             "the discovery in the official motivation, whoever shares the prize. Its text never mentions the committee, the cards or "
             "the experiment.</p></div>"
             "<div class='card'><h4>Why four copies of one question</h4><p>Context notes attach to a Preseen question and apply to every "
             "later run, so each arm is its own copy of an identically defined question. Arms 1 and 2 ran interleaved on 1 October; "
             "arms 3 and 4 were added on 2 October with one run each (plus one more control run that day, which stayed inside the "
             "1 October control range).</p>"
             "<h4>The yardstick</h4><p>Runs of the same question differ by chance. The noise unit is how far one control run lies from "
             "the mean of the other four control runs (about 0.6–0.75 percentage points per option). An arm’s run is compared in "
             "that unit; an option “moved” when it leaves the range of the five control runs.</p></div></div>"
             "<details class='card'><summary>The two instruction notes, as attached (arms 3 and 4)</summary><div class='two' "
             "style='margin-top:10px'>"
             f"<div><div class='armh'>{b2.legend([('balanced', NAME['balanced'])])}</div><div class='cardnote'>{notes['balanced']}</div></div>"
             f"<div><div class='armh'>{b2.legend([('main', NAME['main'])])}</div><div class='cardnote'>{notes['main']}</div></div>"
             "</div><p class='muted'>Both are attached first with <code>treatment=assume_true</code>; the cards follow with "
             "<code>treatment=consider</code> in the same seeded order as in arm 2.</p></details></section>")

    # ------------------------------------------------------------ committee and candidates
    pers = "".join(f"<tr><td>{E(LABEL[f])}</td><td class='num'>{len(cfg['fields'][f]['personas'])}</td>"
                   f"<td>{E('; '.join(cfg['fields'][f]['personas']))}</td></tr>" for f in FIELDS)
    models = ", ".join(f"<code>{E(m)}</code>" for m in cfg["models"].values())
    H.append("<section id='committee'><h2>Committee &amp; candidates</h2><div class='two'><div class='card'><h4>A virtual Nobel "
             "committee</h4><p>Each persona is “a senior member of the Nobel Committee for ⟨field⟩ whose own expertise is ⟨specialty⟩”, "
             "mirroring the specialties of the real 2026 committees (no names). Every persona ran once on each of three models from "
             f"different providers ({models}), without web access, and nominated up to five discoveries with 1–3 living people. "
             f"{n_ballots} ballots, all valid; cost ${cost:.2f}.</p>"
             f"<div class='tw'><table><thead><tr><th>Prize</th><th>Personas</th><th>Specialties</th></tr></thead><tbody>{pers}</tbody>"
             "</table></div></div><div class='card'><h4>From ballots to twelve options</h4><p>A nomination at rank r earns 6 − r points; "
             "each model’s points are divided by its number of ballots so the three models count equally. Nominations sharing a person "
             "are merged, and a recorded review splits umbrella nominations and fixes wording. Three nominees had died and were "
             "replaced by the next living person (Habener → Knudsen for GLP-1, Eshhar → Rosenberg for CAR-T, Rose → Krivanek for "
             "electron optics).</p><p class='muted'>The top twelve per prize became the options; everything else is “Other”.</p></div>"
             "</div><div class='tabs' id='candtabs' role='tablist'>")
    for k, f in enumerate(FIELDS):
        H.append(f"<button type='button' role='tab' id='ctab-{f}' aria-controls='cpanel-{f}' aria-selected='{'true' if k == 0 else 'false'}'>{TAB[f]}</button>")
    H.append("</div>")
    for k, f in enumerate(FIELDS):
        H.append(f"<div class='panel card' id='cpanel-{f}' role='tabpanel'{'' if k == 0 else ' hidden'}>{candidate_table(D[f])}</div>")
    H.append("</section>")

    # ------------------------------------------------------------ cards
    H.append("<section id='cards'><h2>Cards</h2><div class='card'><p>One card per named person (about 300–500 words, fixed template): "
             "affiliation and option, impact (median five-year citation percentile, share of works in the cohort’s top 10 % and 1 %), "
             "three defining works, technological translation (citing inventions, own patents), textbook reach and collaboration. Every "
             "headline number is set against the field’s 2000–2025 laureates measured at their prize year. Sources: OpenAlex, "
             "PatentsView and Reliance on Science, works and patents up to 2021. A definitions note comes first and ends with “These "
             "are descriptive bibliometric measures, not forecasts.”</p></div><div class='tabs' id='cardtabs' role='tablist'>")
    for k, (f, fn, lab) in enumerate(CARD_EXAMPLES):
        H.append(f"<button type='button' role='tab' id='kt-{k}' aria-controls='kp-{k}' aria-selected='{'true' if k == 0 else 'false'}'>{E(lab)}</button>")
    H.append("</div>")
    for k, (f, fn, lab) in enumerate(CARD_EXAMPLES):
        H.append(f"<div class='panel card' id='kp-{k}' role='tabpanel'{'' if k == 0 else ' hidden'}><p class='muted'><code>cards/{f}/{fn}</code>, "
                 f"exactly as attached</p><div class='cardnote'>{bd.md_to_html((HERE / 'preseen' / 'cards' / f / fn).read_text())}</div></div>")
    H.append("</section>")

    # ------------------------------------------------------------ results
    H.append("<section id='results'><h2>Results by prize</h2><p class='muted'>Per prize: how far each arm moved, its top five, and every "
             "option in all four arms.</p><div class='tabs' id='fieldtabs' role='tablist'>")
    for k, f in enumerate(FIELDS):
        H.append(f"<button type='button' role='tab' id='tab-{f}' aria-controls='panel-{f}' aria-selected='{'true' if k == 0 else 'false'}'>{TAB[f]}</button>")
    H.append("</div>")
    for k, f in enumerate(FIELDS):
        H.append(f"<div class='panel' id='panel-{f}' role='tabpanel' aria-labelledby='tab-{f}'{'' if k == 0 else ' hidden'}>"
                 + field_panel(D[f]) + "</div>")
    H.append("</section>")

    # ------------------------------------------------------------ caveats
    H.append("<section id='caveats'><h2>Caveats</h2><div class='card'><ul>"
             "<li><b>Few runs.</b> Five control and three context runs per prize, one run for each instruction arm: the comparisons are "
             "descriptive, not significance tests.</li>"
             "<li><b>Arms were added one after another.</b> The two instruction arms were written after the context arm’s near-null "
             "result, and the softer note after the main-evidence result; they are follow-up questions, not a pre-planned dose series.</li>"
             "<li><b>Each note changes several things at once</b> (weight of the cards, weight of outside evidence, scope); without a "
             "placebo (the same cards with numbers shuffled across people) moving away from the award favourites cannot be separated "
             "from following these particular numbers.</li>"
             "<li><b>The options are the committee’s.</b> Three correlated language models proposed them; a prize for another discovery "
             "resolves to “Other” in every arm.</li>"
             "<li><b>Card quality.</b> OpenAlex splits and merges authors; some profiles are thin or merged (e.g. Pascal Mayer, Robert "
             "Langer); patent counts from a name search may include namesakes. The notes ask the forecaster to take the figures as given.</li>"
             "<li><b>One forecasting system on two days.</b> The results describe Preseen on 1–2 October 2026. Scores against the actual "
             "prizes follow after 5–7 October.</li></ul></div>"
             "<p class='muted'>Code: <code>experiment/preseen/</code> (committee, cards, arms 1–2), <code>experiment/preseen_cards_main/</code> "
             "and <code>experiment/preseen_cards_balanced/</code> (arms 3–4), analysis <code>preseen_cards_main/analyze_main.py</code>, "
             "this page <code>experiment/build_dashboard_all.py</code>.</p></section>")
    H.append(f"</div><script>{bd.JS}</script>")
    body = "\n".join(H)
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
           'content="width=device-width,initial-scale=1,viewport-fit=cover">' + body.replace("<div id='tip'", "</head><body><div id='tip'", 1)
           + "</body></html>")
    out_path.write_text(doc, encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(HERE / "dashboard_all.html"))
    build(Path(ap.parse_args().out))


if __name__ == "__main__":
    main()
