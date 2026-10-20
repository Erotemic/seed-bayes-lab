from pathlib import Path

import pytest
import plotly.graph_objects as go

from seed_bayes_lab.demo import render_html
from seed_bayes_lab.model import Likelihoods, Prior, update
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


def test_every_python_plot_has_explicit_axis_titles():
    """Cover both Streamlit figures and the separate budget-slider figure."""
    prior = Prior.from_intent_success(0.3, 0.4)
    likelihoods = Likelihoods(0.7, 0.2, 0.5)
    figures = {
        "evidence": (evidence_sweep(prior, likelihoods),
                     "P(E | B) - evidence likelihood", "P(B | E) - posterior"),
        "direction": (direction_heatmap(prior, 0.8), "P(E | F)", "P(E | B)"),
        "search": (search_sweep(), "Target rarity k (bits)", "Probability"),
        "budget": (budget_slider_figure(), "Target rarity k (bits)",
                   "P(find at least one target)"),
    }
    for name, (figure, x_label, y_label) in figures.items():
        assert figure.layout.xaxis.title.text == x_label, name
        assert figure.layout.yaxis.title.text == y_label, name
        assert not figure.layout.xaxis.title.text.startswith("Click to"), name
        assert not figure.layout.yaxis.title.text.startswith("Click to"), name


def test_heatmap_colorbar_expresses_update_in_percentage_points():
    prior = Prior.from_intent_success(0.3, 0.4)
    fig = direction_heatmap(prior, 0.8, samples=3)
    heatmap = fig.data[0]
    assert heatmap.colorbar.title.text == "Δ (pp)"
    # At x = 1/2 and y = 1/2, z is posterior-minus-prior in pp.
    result = update(prior, Likelihoods(0.8, 0.5, 0.5))
    assert float(heatmap.z[1][1]) == pytest.approx(result.delta_backdoor * 100)
    assert "pp" in heatmap.hovertemplate


def test_offline_javascript_axes_are_explicit_and_match_python():
    """Assert Plotly.js receives title objects, not ignored title strings."""
    import json
    import shutil
    import subprocess

    if shutil.which("node") is None:
        pytest.skip("Node is optional")
    js = Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/offline.js"
    runner = r'''
      require(process.argv[1]);
      const api = globalThis.SeedBayesOffline;
      const s = {
        prior_intent:0.5,success_given_intent:0.3,
        likelihood_honest:0.9,likelihood_failed:0.8,likelihood_succeeded:0.2,
        restricted_bits:30,unrestricted_bits:60,compute_bits:36,rarity_bits:40,
        know_restricted:0.3,know_unrestricted:0.3,
        prior_restricted:0.5,publish_failed:1
      };
      console.log(JSON.stringify({
        line:api.lineFigure(s)[1],
        heatmap:{layout:api.heatmapFigure(s)[1],
          colorbar:api.heatmapFigure(s)[0][0].colorbar},
        search:api.searchFigure(s)[1]
      }));
    '''
    output = subprocess.run(
        ["node", "-e", runner, str(js)], capture_output=True, text=True, check=True,
    )
    layouts = json.loads(output.stdout)
    expected = {
        "line": ("P(E | B) - evidence likelihood", "P(B | E) - posterior"),
        "heatmap": ("P(E | F)", "P(E | B)"),
        "search": ("Target rarity k (bits)", "Probability"),
    }
    for key, (x_title, y_title) in expected.items():
        layout = layouts[key]["layout"] if key == "heatmap" else layouts[key]
        assert layout["xaxis"]["title"]["text"] == x_title, key
        assert layout["yaxis"]["title"]["text"] == y_title, key
    assert layouts["heatmap"]["colorbar"]["title"]["text"] == "Δ (pp)"


def test_impossible_evidence_heatmap_has_explicit_undefined_state():
    import warnings
    p = Prior.from_intent_success(0.0, 0.3)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figure = direction_heatmap(p, 0.0, samples=5)
    assert not caught
    assert len(figure.data) == 0
    assert "Conditioning undefined" in figure.layout.annotations[0].text
    assert figure.layout.xaxis.title.text == "P(E | F)"
    assert figure.layout.yaxis.title.text == "P(E | B)"


def test_js_impossible_evidence_heatmap_has_explanation():
    import json
    import shutil
    import subprocess
    if shutil.which("node") is None:
        pytest.skip("Node optional")
    js = Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/offline.js"
    cmd = """
      require(process.argv[1]);
      const s = {prior_intent:0,success_given_intent:0.3,
        likelihood_honest:0,likelihood_failed:0.5,likelihood_succeeded:0.5};
      const [data,layout] = globalThis.SeedBayesOffline.heatmapFigure(s);
      console.log(JSON.stringify({count:data.length,message:layout.annotations?.[0]?.text}));
    """
    result = subprocess.run(["node", "-e", cmd, str(js)], text=True,
                            capture_output=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["count"] == 0
    assert "Conditioning undefined" in payload["message"]
