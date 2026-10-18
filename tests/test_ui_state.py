"""Interactive defaults and the identity of the historical observation."""

from pathlib import Path

from seed_bayes_lab.evidence import (
    EVIDENCE_OBSERVATION, EVIDENCE_LIMITS, EVIDENCE_LIKELIHOOD_NOTE,
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
    assert "1,842" in EVIDENCE_OBSERVATION
    assert "skipped" in EVIDENCE_LIMITS
    assert "hypothetical" in EVIDENCE_LIKELIHOOD_NOTE
    assert "stronger assumption" in METHOD_OBSERVATION
    assert len(SOURCES) == 2
    assert all(url.startswith("https://") for _, url in SOURCES)


def test_all_streamlit_sliders_have_resettable_keys():
    app = (Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/app.py").read_text()
    for key in DEFAULT_ASSUMPTIONS:
        assert f'key="{key}"' in app
    assert "on_click=reset_assumptions" in app
