"""Build a full self-contained interactive Bayesian explorer, without a server."""

from __future__ import annotations

from argparse import ArgumentParser
from html import escape
from importlib.resources import files
from pathlib import Path
import json

from plotly.offline import get_plotlyjs

from seed_bayes_lab.evidence import (
    EVIDENCE_TITLE, EVIDENCE_SHORT, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS,
    EVIDENCE_LIKELIHOOD_NOTE, METHOD_OBSERVATION, SOURCES,
)
from seed_bayes_lab.sensitivity import BAYES_SLIDERS, SEARCH_SLIDERS, SLIDER_SPECS
from seed_bayes_lab.glossary import (
    BAYES_EVENTS, BAYES_QUANTITIES, SEARCH_EVENTS, SEARCH_QUANTITIES,
    BAYES_PARAMETERS, SEARCH_PARAMETERS,
)
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def _safe_json(value: object) -> str:
    """Embed serialized config in an inline JS script safely."""
    return json.dumps(value, ensure_ascii=True).replace("<", "\\u003c")


def _glossary_table(title: str, items: tuple, *, parameters: bool = False) -> str:
    """Static accessible tables: readable offline even before JS initializes."""
    rows = []
    for entry in items:
        if parameters:
            first = entry.symbol + " / " + SLIDER_SPECS[entry.key].label
            meaning, qualification = entry.definition, entry.qualification
        else:
            first, meaning, qualification = entry.symbol, entry.definition, entry.qualification
        rows.append(
            "<tr><th scope=\"row\"><code>" + escape(first) + "</code></th><td>" +
            escape(meaning) + "</td><td>" + escape(qualification) + "</td></tr>"
        )
    return (
        '<section class="glossary-section"><h3>' + escape(title) + '</h3>'
        '<div class="glossary-overflow"><table><thead><tr>'
        '<th scope="col">Notation</th><th scope="col">Exact definition</th>'
        '<th scope="col">Qualification</th></tr></thead><tbody>'
        + "".join(rows) + '</tbody></table></div></section>'
    )


def _glossary_html() -> str:
    return (
        '<div class="glossary-intro"><h2>Notation and exact events</h2>'
        '<p>The finite Bayes model conditions on the <strong>observed reconstruction E</strong>. '
        'The separate search model conditions on a <strong>genuinely used method T</strong> '
        'among published curves. These are not the same event. All numeric inputs '
        'are assumptions, not historical estimates.</p></div>'
        '<h2 class="glossary-group-title">1. Finite Bayes model</h2>'
        '<p class="intro">The elementary sample space is <code>Ω = {H, F, B}</code>. '
        'Exactly one world holds for the published curve.</p>'
        + _glossary_table('Events and worlds', BAYES_EVENTS)
        + _glossary_table('Probability notation and updates', BAYES_QUANTITIES)
        + _glossary_table('Five input dials', BAYES_PARAMETERS, parameters=True)
        + '<h2 class="glossary-group-title">2. Search and publication model</h2>'
        '<p class="intro">Malicious intent is certain in this toy model. The '
        'design process chooses T or U before attempting to plant a backdoor; '
        'J describes whether the attempt was published.</p>'
        + _glossary_table('Events', SEARCH_EVENTS)
        + _glossary_table('Probabilities and search formulas', SEARCH_QUANTITIES)
        + _glossary_table('Eight input dials', SEARCH_PARAMETERS, parameters=True)
        + '<section class="glossary-section"><h3>Reading the visual endpoint indicators</h3>'
        '<p><strong>↘</strong> means the posterior will decrease from its current '
        'value if you move this one dial to that endpoint; <strong>↗</strong> '
        'means increase, <strong>→</strong> means no change, and <strong>?</strong> '
        'means conditioning is undefined. The nearby percentage is the resulting '
        'posterior at that endpoint.</p>'
        '<p><strong>CAN REVERSE</strong> instead checks the sign of the '
        '<em>evidence update</em>, posterior minus prior, across every position '
        'of that dial. The endpoint icon and the reversal status deliberately '
        'measure different quantities: a changed prior can change the posterior '
        'without reversing the direction of the evidence update.</p></section>'
    )


def render_html(destination: str | Path) -> Path:
    """Export a shareable offline HTML with 13 live dials and a glossary tab.

    Bayes and search formulas in offline.js mirror the tested Python model;
    a parity test executes them using Node. Plotly is bundled inline.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "defaults": DEFAULT_ASSUMPTIONS,
        "specs": [
            {"key": spec.key, "label": spec.label, "min": spec.minimum,
             "max": spec.maximum, "step": spec.step, "group": spec.group}
            for spec in (*BAYES_SLIDERS, *SEARCH_SLIDERS)
        ],
    }
    js = files("seed_bayes_lab").joinpath("offline.js").read_text(encoding="utf-8")
    limits = escape(EVIDENCE_LIMITS).replace("**", "")
    note = escape(EVIDENCE_LIKELIHOOD_NOTE).replace("**", "")
    observation = escape(EVIDENCE_OBSERVATION).replace(
        "`lrand48`", "<code>lrand48</code>"
    )
    refs = " · ".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'{escape(label)}</a>' for label, url in SOURCES
    )
    html = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Seed Bayes Lab · Interactive offline explorer</title>
<style>
:root{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#243247;background:#f7f8fa}
*{box-sizing:border-box}body{margin:0;line-height:1.48}main{max-width:1440px;margin:auto;padding:28px 28px 68px}
h1{font-size:2rem;letter-spacing:-.035em;margin:0}h2{font-size:1.21rem;margin:0 0 9px}h3{font-size:1.02rem;margin:14px 0 8px}
header{margin-bottom:18px}.subtitle{color:#57657b;max-width:890px;margin:7px 0 18px}
.evidence{padding:17px 21px;background:#fff;border:1px solid #dce3ed;border-radius:12px}
.evidence p{font-size:.925rem;color:#526075;margin:7px 0;max-width:1100px}.evidence h2{font-size:1.08rem}
.evidence details{margin-top:7px;color:#526075}.evidence summary{cursor:pointer;font-size:.83rem;font-weight:650;color:#245e9b}
.evidence a{color:#245e9b}.evidence a:focus-visible{outline:2px solid #27639c}
.actions{display:flex;flex-wrap:wrap;gap:13px;align-items:center;margin:18px 0}
button{font:inherit;cursor:pointer}button:focus-visible,input:focus-visible{outline:3px solid #92b9eb;outline-offset:3px}
button.primary{border:0;border-radius:8px;background:#225992;padding:9px 17px;color:white;font-weight:600}
button.primary:hover{background:#184575}.helper{color:#65758a;font-size:.85rem}
.tabbar{display:flex;gap:8px;border-bottom:1px solid #cfd7e2;margin:8px 0 18px}
.tabbar button{border:0;background:transparent;color:#647187;font-weight:600;padding:12px 18px;border-bottom:3px solid transparent}
.tabbar button[aria-selected=true]{color:#194e83;border-bottom-color:#2364a4}
[hidden]{display:none!important}
.intro{font-size:.9rem;color:#59697c;max-width:1120px;margin:0 0 16px}
.workspace{display:grid;grid-template-columns:minmax(325px,430px) minmax(0,1fr);gap:20px;align-items:start}
.controls{padding:18px;background:white;border:1px solid #dce3ed;border-radius:12px}
.controls>.detail{font-size:.86rem;color:#5e6c82;margin:2px 0 14px}
.dial{padding:12px 0 14px;border-top:1px solid #ebeff3}
.dial-header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.dial-header label{font-size:.90rem;font-weight:600;color:#2c3c51}
.dial-value{font-variant-numeric:tabular-nums;white-space:nowrap;color:#195a99;font-size:.92rem}
.dial-rail{display:grid;grid-template-columns:minmax(100px,1fr) minmax(100px,1.25fr) minmax(100px,1fr);align-items:center;gap:9px;margin-top:8px}
.dial-slider-wrap{min-width:0;display:flex;align-items:center;padding:0 1px}
.dial-slider-wrap input[type=range]{width:100%;margin:0;accent-color:#366da3;cursor:pointer}
.dial-extreme{border:1px solid #e0e5ec;background:#f9fafc;border-radius:10px;padding:8px 7px;min-width:0;min-height:76px;transition:background .15s}
.extreme-label{font-size:.66rem;letter-spacing:.035em;color:#667588;font-weight:720}
.extreme-main{display:flex;align-items:center;gap:5px;margin:4px 0;font-variant-numeric:tabular-nums}
.extreme-icon{border-radius:50%;width:25px;height:25px;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center;background:#e9edf2;color:#536378;font-size:17px;font-weight:800}
.extreme-number{font-size:.85rem;font-weight:740;white-space:nowrap}
.extreme-posterior{font-size:.66rem;font-variant-numeric:tabular-nums;color:#647386;white-space:nowrap;letter-spacing:-.01em}
.dial-extreme.decrease .extreme-icon{background:#daece5;color:#207357}
.dial-extreme.increase .extreme-icon{background:#fae4de;color:#b04b32}
.dial-extreme.undefined .extreme-icon{background:#fff1da;color:#9f6720}
.dial-rail .dial-extreme:last-child{text-align:right}
.dial-rail .dial-extreme:last-child .extreme-main{justify-content:flex-end}
.dial-meta{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:3px 10px;margin-top:7px}
.dial-status{font-size:.71rem;font-weight:750;line-height:1.25;color:#647389}
.dial-status.flip{color:#a4432d}.dial-status.equality{color:#746584}
.dial-range{font-size:.70rem;color:#78869a;font-variant-numeric:tabular-nums}
.view{min-width:0}.summary{background:#fff;border:1px solid #dce3ed;border-radius:12px;padding:16px;margin-bottom:14px}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}
.metric{border:1px solid #e2e7ee;border-radius:8px;padding:10px 8px;min-width:0}
.metric-label{display:block;color:#5f6f83;font-size:.78rem}.metric-value{display:block;font-variant-numeric:tabular-nums;font-weight:750;font-size:1.27rem;overflow-wrap:anywhere}
.metric-value[data-direction=decrease]{color:#2d796a}.metric-value[data-direction=increase]{color:#ae593d}
.flip-summary{font-size:.88rem;margin:11px 0 0;color:#42516a;font-weight:600}
.chart-panel{background:#fff;border:1px solid #e0e5ed;border-radius:12px;padding:7px 12px;margin-bottom:14px}
.chart{min-height:335px;width:100%}
.caveat{padding:15px;background:#ecf1f7;border-radius:9px;color:#4c5d72;font-size:.88rem;margin-top:15px}
.glossary-intro{margin-bottom:20px}.glossary-intro p{max-width:1000px;color:#56677d;font-size:.92rem}
.glossary-group-title{font-size:1.32rem;margin:28px 0 12px;color:#203a56}
.glossary-section{background:white;border:1px solid #dce3ed;border-radius:12px;padding:16px 18px;margin:12px 0 18px}
.glossary-section h3{font-size:1.04rem;margin:0 0 12px}
.glossary-section p{font-size:.9rem;color:#50647d;max-width:1100px}
.glossary-overflow{width:100%;overflow-x:auto}
.glossary-section table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:.84rem;text-align:left}
.glossary-section th,.glossary-section td{vertical-align:top;padding:10px 13px;border-bottom:1px solid #e8ebef}
.glossary-section thead th{color:#53657e;background:#f3f5f8;font-size:.75rem}
.glossary-section tbody th{font-weight:600;width:24%;overflow-wrap:anywhere}
.glossary-section th:nth-child(1){width:25%}.glossary-section th:nth-child(2){width:42%}.glossary-section th:nth-child(3){width:33%}
.glossary-section tr:last-child td,.glossary-section tr:last-child th{border-bottom:0}
.glossary-section code{font-size:.79rem;color:#184f8b;white-space:normal;overflow-wrap:anywhere}
footer{font-size:.85rem;color:#65758a;margin-top:30px}
@media(max-width:1050px){.workspace{grid-template-columns:minmax(310px,1fr) minmax(0,1.3fr)}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:760px){main{padding:17px 14px 50px}.workspace{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.tabbar button{font-size:.84rem;padding:10px 9px}.dial-rail{gap:5px;grid-template-columns:minmax(95px,1fr) minmax(70px,1fr) minmax(95px,1fr)}.glossary-section{padding:11px}}
@media(max-width:430px){.dial-extreme{padding:6px 4px}.extreme-icon{width:21px;height:21px;font-size:15px}.extreme-number{font-size:.73rem}.extreme-posterior{font-size:.61rem}}
</style>
</head><body><main>
<header><h1>Seed Bayes Lab</h1>
<p class="subtitle">Explore how assumptions change the direction and magnitude of a Bayesian update. All probabilities are hypothetical inputs, not estimates of whether a NIST curve is backdoored. Runs entirely offline.</p>
<section class="evidence"><h2>%%EVIDENCE_TITLE%%</h2>
<p>%%EVIDENCE_SHORT%%</p>
<details><summary>Read the full observation, limitations and sources</summary>
<p>%%EVIDENCE_OBSERVATION%%</p>
<p><strong>What E does not establish:</strong> %%EVIDENCE_LIMITS%%</p>
<p><strong>Meaning of evidence likelihoods:</strong> %%EVIDENCE_NOTE%%</p>
<p><strong>Sources:</strong> %%EVIDENCE_SOURCES%%</p></details></section>
<div class="actions"><button type="button" id="reset-all" class="primary">Reset all assumptions</button>
<span class="helper">Resets all 13 sliders, summary values, and charts.</span></div></header>
<div class="tabbar" role="tablist" aria-label="Probability models">
<button type="button" id="tab-bayes" role="tab" aria-controls="panel-bayes" aria-selected="true">Evidence / Bayes</button>
<button type="button" id="tab-search" role="tab" aria-controls="panel-search" aria-selected="false">Search &amp; publication</button>
<button type="button" id="tab-glossary" role="tab" aria-controls="panel-glossary" aria-selected="false">Notation glossary</button>
</div>
<section id="panel-bayes" role="tabpanel" aria-labelledby="tab-bayes">
<p class="intro">Three worlds: no malicious attempt, attempted but failed, successful planted backdoor. Endpoint arrows show how <strong>P(B | E) itself</strong> changes relative to the current posterior if you move that dial to MIN or MAX, leaving others fixed. The separate direction/reversal test refers to <strong>Δupdate = P(B | E) − P(B)</strong>. Both changes are in percentage points.</p>
<div class="workspace">
<div class="controls"><h2>Bayesian assumptions</h2><p class="detail">P(I) starts at 0.50 as a <em>symmetric demonstration prior</em>, not as a measured historical probability or a claim of ignorance.</p><div id="bayes-controls"></div></div>
<div class="view"><div class="summary"><div class="metrics">
<div class="metric"><span class="metric-label">P(B) · before E</span><span class="metric-value" id="bayes-before">—</span></div>
<div class="metric"><span class="metric-label">P(B | E) · after E</span><span class="metric-value" id="bayes-after">—</span></div>
<div class="metric"><span class="metric-label">Δ (percentage points)</span><span class="metric-value" id="bayes-delta">—</span></div>
<div class="metric"><span class="metric-label">P(I | E) · intent after E</span><span class="metric-value" id="bayes-intent-after">—</span></div>
</div><p class="flip-summary" id="bayes-flip-summary"></p></div>
<div class="chart-panel"><div id="bayes-line" class="chart"></div></div>
<div class="chart-panel"><div id="bayes-heatmap" class="chart"></div></div>
</div></div></section>
<section id="panel-search" role="tabpanel" aria-labelledby="tab-search" hidden>
<p class="intro">%%METHOD_OBSERVATION%% In this separate model intent is fixed at 100%; the observation is <strong>T among published curves</strong>. Endpoint arrows measure the change in P(B | published,T) from the current setting. Direction/reversal refers to Δupdate = P(B | published,T) − P(B | published). This is not evidence E.</p>
<div class="workspace">
<div class="controls"><h2>Search and selection assumptions</h2><p class="detail">Candidate rarity, available choices, computing budget, attack knowledge, and publication policy are separately adjustable hypothetical controls.</p><div id="search-controls"></div></div>
<div class="view"><div class="summary"><div class="metrics" style="grid-template-columns:repeat(3,minmax(0,1fr))">
<div class="metric"><span class="metric-label">P(B | published)</span><span class="metric-value" id="search-before">—</span></div>
<div class="metric"><span class="metric-label">P(B | published,T)</span><span class="metric-value" id="search-after">—</span></div>
<div class="metric"><span class="metric-label">Δ (percentage points)</span><span class="metric-value" id="search-delta">—</span></div>
</div><p class="flip-summary" id="search-flip-summary"></p></div>
<div class="chart-panel"><div id="search-curves" class="chart"></div></div>
<div class="caveat">The independent-candidate search model does not capture direct cryptanalytic constructions. At parameter combinations with zero-probability observations, the posterior is <strong>undefined</strong> and is not counted as unchanged.</div>
</div></div></section>
<section id="panel-glossary" role="tabpanel" aria-labelledby="tab-glossary" hidden>%%GLOSSARY_HTML%%</section>
<footer>Endpoint arrows: posterior at that endpoint minus the current posterior, keeping all other controls fixed. "CAN REVERSE" and the update Δ range describe posterior minus prior at each slider setting. Full scans include interior positions; undefined conditioning is not treated as equality. See the notation glossary for every event.</footer>
</main>
<script>%%PLOTLY_JS%%</script>
<script>%%OFFLINE_JS%%</script>
<script>window.SeedBayesOffline.mount(%%CONFIG_JSON%%);</script>
</body></html>'''
    for token, value in (
        ("%%EVIDENCE_TITLE%%", escape(EVIDENCE_TITLE)),
        ("%%EVIDENCE_SHORT%%", escape(EVIDENCE_SHORT)),
        ("%%EVIDENCE_OBSERVATION%%", observation),
        ("%%EVIDENCE_LIMITS%%", limits),
        ("%%EVIDENCE_NOTE%%", note),
        ("%%EVIDENCE_SOURCES%%", refs),
        ("%%METHOD_OBSERVATION%%", escape(METHOD_OBSERVATION).replace("*", "")),
        ("%%PLOTLY_JS%%", get_plotlyjs()),
        ("%%OFFLINE_JS%%", js),
        ("%%CONFIG_JSON%%", _safe_json(config)),
        ("%%GLOSSARY_HTML%%", _glossary_html()),
    ):
        html = html.replace(token, value)
    destination.write_text(html, encoding="utf-8")
    return destination


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("destination", nargs="?", default="examples/interactive_demo.html")
    args = parser.parse_args()
    print(render_html(args.destination))


if __name__ == "__main__":
    main()
