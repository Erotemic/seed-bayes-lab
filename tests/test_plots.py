from pathlib import Path

import plotly.graph_objects as go

from seed_bayes_lab.demo import render_html
from seed_bayes_lab.model import Likelihoods, Prior
from seed_bayes_lab.plots import budget_slider_figure, direction_heatmap, evidence_sweep, search_sweep


def test_all_plotly_figures_are_serializable():
    prior = Prior.from_intent_success(0.3, 0.4)
    likelihoods = Likelihoods(0.7, 0.2, 0.5)
    figs = [
        budget_slider_figure(),
        direction_heatmap(prior, 0.8),
        evidence_sweep(prior, likelihoods),
        search_sweep(),
    ]
    for fig in figs:
        assert isinstance(fig, go.Figure)
        assert fig.to_json()
    assert len(figs[0].frames) > 2


def test_offline_html_is_self_contained(tmp_path: Path):
    target = tmp_path / "demo.html"
    render_html(target)
    html = target.read_text(encoding="utf-8")
    assert "plotly.js" in html.lower()
    assert "Seed Bayes Lab" in html
    assert 'id="reset-all"' in html
    assert "Reset all assumptions" in html
    assert "window.SeedBayesOffline.mount(" in html
    assert "CAN REVERSE" in html
    assert "Update \\u0394 range:" in html
    assert "Observed evidence E: reconstructed seed provenance" in html
    assert "lrand48" in html
    assert "What E does not establish:" in html
    assert "P(E | honest)" in html
    assert "anthropic.com/research/ecdsa-curve-origins" in html
    assert "success_given_intent" in html
    assert "publish_failed" in html
    assert '<script src="https://cdn.plot.ly' not in html
    assert len(html) > 100_000
