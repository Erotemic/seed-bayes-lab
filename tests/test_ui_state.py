"""Interactive defaults and the identity of the historical observation."""

from pathlib import Path

from seed_bayes_lab.evidence import (
    EVIDENCE_SHORT, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS, EVIDENCE_LIKELIHOOD_NOTE,
    METHOD_OBSERVATION, SOURCES,
)
from seed_bayes_lab.ui_state import (
    DEFAULT_ASSUMPTIONS, initialize_assumptions, reset_assumptions,
)


def test_reset_restores_every_control_without_erasing_other_state():
    state = {"custom_state": "preserve", "prior_intent": 0.75}
    initialize_assumptions(state)
    assert state["prior_intent"] == 0.75
    assert len(DEFAULT_ASSUMPTIONS) == 13
    for key in DEFAULT_ASSUMPTIONS:
        state[key] = 0
    reset_assumptions(state)
    assert all(state[k] == v for k, v in DEFAULT_ASSUMPTIONS.items())
    assert state["custom_state"] == "preserve"


def test_evidence_text_distinguishes_observation_from_assumptions():
    assert "lrand48" in EVIDENCE_OBSERVATION
    assert "1997" in EVIDENCE_SHORT
    assert "1,842" in EVIDENCE_OBSERVATION
    assert "skipped" in EVIDENCE_LIMITS
    assert "hypothetical" in EVIDENCE_LIKELIHOOD_NOTE
    assert "stronger assumption" in METHOD_OBSERVATION
    assert len(SOURCES) == 2
    assert all(url.startswith("https://") for _, url in SOURCES)


def test_all_streamlit_sliders_have_resettable_keys():
    app = (Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/app.py").read_text()
    for key in DEFAULT_ASSUMPTIONS:
        assert f'sensitivity_slider("{key}")' in app
    assert 'key=key' in app
    assert "on_click=reset_assumptions" in app
    from seed_bayes_lab.sensitivity import SLIDER_SPECS
    assert set(DEFAULT_ASSUMPTIONS) == set(SLIDER_SPECS)


def test_neutral_illustrative_prior_and_metric_notation():
    assert DEFAULT_ASSUMPTIONS["prior_intent"] == 0.5
    app = (Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/app.py").read_text()
    assert 'c1.metric("P(B)"' in app
    assert 'c2.metric("P(B | E)"' in app
    assert 'c3.metric("P(I | E)"' in app
    assert 'Before observing E' in app
    assert 'After observing E' in app
