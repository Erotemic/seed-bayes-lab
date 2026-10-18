"""Build a self-contained offline Plotly demonstration dashboard."""

from __future__ import annotations

from argparse import ArgumentParser
from html import escape
from pathlib import Path

import plotly.io as pio

from seed_bayes_lab.evidence import (
    EVIDENCE_TITLE, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS,
    EVIDENCE_LIKELIHOOD_NOTE, SOURCES,
)
from seed_bayes_lab.model import Likelihoods, Prior
from seed_bayes_lab.plots import budget_slider_figure, direction_heatmap, evidence_sweep


def render_html(destination: str | Path) -> Path:
    """Generate interactive HTML without a running Streamlit server or CDN."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    prior = Prior.from_intent_success(intent=0.2, success_given_intent=0.3)
    likelihoods = Likelihoods(honest=0.8, attempted_failed=0.6, succeeded=0.2)
    figures = [
        budget_slider_figure(),
        evidence_sweep(prior, likelihoods),
        direction_heatmap(prior, likelihoods.honest),
    ]
    sections = [
        pio.to_html(fig, full_html=False, include_plotlyjs="inline" if i == 0 else False,
                    config={"displaylogo": False, "responsive": True}, auto_play=False)
        for i, fig in enumerate(figures)
    ]
    # This offline page has no editable Bayes sliders: only the budget slider
    # affects the first chart; the remaining charts have hover/zoom controls.
    # A real Reset button restores the initial frame and plot ranges.
    observation = escape(EVIDENCE_OBSERVATION).replace(
        "`lrand48`", "<code>lrand48</code>"
    )
    limits = escape(EVIDENCE_LIMITS).replace("**", "")
    likelihood_note = escape(EVIDENCE_LIKELIHOOD_NOTE).replace("**", "")
    sources = " | ".join(
        f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'
        for label, url in SOURCES
    )
    html = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Seed Bayes Lab · Offline demo</title>
<style>
:root{color-scheme:light}body{margin:0;background:#f6f8fb;color:#19263d;font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:1100px;margin:0 auto;padding:32px 22px 70px}header{margin-bottom:27px}
h1{font-size:2.1rem;margin:0 0 8px}h2{font-size:1.05rem}p{max-width:880px;color:#4c5a6e}
section{background:#fff;border:1px solid #dde3eb;border-radius:14px;padding:14px 14px 4px;margin-bottom:22px}
.note{font-size:0.94rem;background:#eaf0f7;padding:14px 17px;border-radius:10px}
.evidence{border-left:4px solid #3b76b7;padding:14px 22px}.evidence p{margin:8px 0 13px}
button{background:#234d80;border:0;border-radius:9px;color:white;padding:10px 17px;font:inherit;cursor:pointer}
button:focus-visible{outline:3px solid #a3c8fa;outline-offset:3px}
button:hover{background:#16395f}.actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:10px 0 18px}
</style></head><body><main><header><h1>Seed Bayes Lab</h1>
<p>Interactive sensitivity analysis of hypothetical curve-selection mechanisms. All numerical values are scenario assumptions, not empirical estimates about NIST P-256.</p>
<section class="evidence"><h2>%%EVIDENCE_TITLE%%</h2>
<p>%%EVIDENCE_OBSERVATION%%</p>
<p><strong>What E does not establish:</strong> %%EVIDENCE_LIMITS%%</p>
<p><strong>Interpretation of likelihoods:</strong> %%EVIDENCE_NOTE%%</p>
<p>%%EVIDENCE_SOURCES%%</p></section>
<p class="note">Drag the <strong>compute-budget slider</strong> in the first chart. The other charts support hover, zoom, and legend controls. For fully editable assumptions, run the Python Streamlit app.</p>
<div class="actions"><button id="reset-all" type="button">Reset interactive charts</button>
<span>Restores the budget slider to 2<sup>36</sup> and resets chart zoom.</span></div>
</header>
<section><h2>1 · Effective search freedom</h2>%%FIG0%%</section>
<section><h2>2 · Bayesian evidence likelihood</h2>%%FIG1%%</section>
<section><h2>3 · Direction of the update</h2>%%FIG2%%</section>
<p>Model and source code: see the accompanying repository README and <code>docs/model.md</code>.</p>
</main>
<script>
document.getElementById('reset-all').addEventListener('click', function () {
  const figures = Array.from(document.querySelectorAll('.plotly-graph-div'));
  if (!window.Plotly || figures.length !== 3) return;
  const resetLayouts = [
    {'xaxis.autorange': true, 'yaxis.range': [0, 1.02]},
    {'xaxis.range': [0, 1], 'yaxis.range': [0, 1]},
    {'xaxis.autorange': true, 'yaxis.autorange': true},
  ];
  figures.forEach(function (fig, i) {
    Plotly.relayout(fig, resetLayouts[i]);
  });
  const initialBudget = '36';
  Plotly.animate(figures[0], [initialBudget], {
    mode: 'immediate', frame: {duration: 0, redraw: true},
    transition: {duration: 0}
  }).then(function () {
    Plotly.relayout(figures[0], {'sliders[0].active': 5});
  });
});
</script></body></html>"""
    for token, value in (
        ("%%EVIDENCE_TITLE%%", escape(EVIDENCE_TITLE)),
        ("%%EVIDENCE_OBSERVATION%%", observation),
        ("%%EVIDENCE_LIMITS%%", limits),
        ("%%EVIDENCE_NOTE%%", likelihood_note),
        ("%%EVIDENCE_SOURCES%%", sources),
    ):
        html = html.replace(token, value)
    for i, section in enumerate(sections):
        html = html.replace(f"%%FIG{i}%%", section)
    destination.write_text(html, encoding="utf-8")
    return destination


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("destination", nargs="?", default="examples/interactive_demo.html")
    args = parser.parse_args()
    print(render_html(args.destination))


if __name__ == "__main__":
    main()
