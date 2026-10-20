"""Interactive defaults and the identity of the historical observation."""

from pathlib import Path

from seed_bayes_lab.evidence import (
    EVIDENCE_SHORT, EVIDENCE_OBSERVATION, EVIDENCE_LIMITS, EVIDENCE_LIKELIHOOD_NOTE,
    METHOD_OBSERVATION, SOURCES,
)
from seed_bayes_lab.ui_state import (
    DEFAULT_ASSUMPTIONS, EVIDENCE_PRESETS, active_evidence_preset,
    apply_evidence_preset, initialize_assumptions, reset_assumptions,
)


def test_reset_restores_every_control_without_erasing_other_state():
    state = {"custom_state": "preserve", "prior_intent": 0.75}
    initialize_assumptions(state)
    assert state["prior_intent"] == 0.75
    assert len(DEFAULT_ASSUMPTIONS) == 18
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


def test_evidence_defaults_neutral_but_not_empirically_calibrated():
    from seed_bayes_lab.model import Likelihoods, Prior, update
    assert active_evidence_preset(DEFAULT_ASSUMPTIONS) == "neutral"
    for intent, success in ((0.5, 0.3), (0.1, 0.9), (1.0, 0.4)):
        p = Prior.from_intent_success(intent, success)
        likelihoods = Likelihoods(*EVIDENCE_PRESETS["neutral"].values())
        res = update(p, likelihoods)
        assert abs(res.posterior_backdoor - res.prior_backdoor) < 1e-14


def test_preset_changes_only_likelihoods_and_custom_is_detected():
    state = dict(DEFAULT_ASSUMPTIONS)
    state["prior_intent"] = 0.73
    state["compute_bits"] = 42
    apply_evidence_preset(state, "benign")
    assert active_evidence_preset(state) == "benign"
    assert state["prior_intent"] == 0.73
    assert state["compute_bits"] == 42
    apply_evidence_preset(state, "backdoor")
    assert active_evidence_preset(state) == "backdoor"
    state["likelihood_succeeded"] = 0.79
    assert active_evidence_preset(state) is None
    reset_assumptions(state)
    assert active_evidence_preset(state) == "neutral"
