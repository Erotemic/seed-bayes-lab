"""Single source of truth for model defaults, examples, and UI reset behavior."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

# These are illustrative likelihood *scenarios*, not historical estimates.
# The neutral baseline deliberately produces no update for any valid prior.
EVIDENCE_PRESETS: dict[str, dict[str, float]] = {
    "neutral": {
        "likelihood_honest": 0.50,
        "likelihood_failed": 0.50,
        "likelihood_succeeded": 0.50,
    },
    "benign": {
        "likelihood_honest": 0.80,
        "likelihood_failed": 0.60,
        "likelihood_succeeded": 0.20,
    },
    "backdoor": {
        "likelihood_honest": 0.20,
        "likelihood_failed": 0.60,
        "likelihood_succeeded": 0.80,
    },
}

EVIDENCE_PRESET_LABELS = {
    "neutral": "Neutral evidence",
    "benign": "Favors benign",
    "backdoor": "Favors backdoor",
}

DEFAULT_ASSUMPTIONS: dict[str, float | int] = {
    "prior_intent": 0.50,
    "success_given_intent": 0.30,
    **EVIDENCE_PRESETS["neutral"],
    "restricted_bits": 30,
    "unrestricted_bits": 60,
    "compute_bits": 36,
    "rarity_bits": 40,
    "know_restricted": 0.30,
    "know_unrestricted": 0.30,
    "prior_restricted": 0.50,
    "publish_failed": 1.0,
    # Separate alternative explanation of E (neutral by default).
    "restriction_intent": 0.50,
    "restriction_before": 0.50,
    "restriction_evidence_t": 0.50,
    "restriction_evidence_u": 0.50,
    "restriction_success_u": 0.40,
    "restriction_success_t": 0.20,
}


def active_evidence_preset(state: Mapping[str, Any]) -> str | None:
    """Return the matching likelihood scenario, or None for custom sliders."""
    for name, likelihoods in EVIDENCE_PRESETS.items():
        if all(state.get(key) == value for key, value in likelihoods.items()):
            return name
    return None


def apply_evidence_preset(state: MutableMapping[str, Any], name: str) -> None:
    """Change only the three evidence likelihoods, preserving every other dial."""
    if name not in EVIDENCE_PRESETS:
        raise ValueError(f"Unknown evidence preset: {name}")
    state.update(EVIDENCE_PRESETS[name])


def initialize_assumptions(state: MutableMapping[str, Any]) -> None:
    """Insert defaults only if a control has not already been initialized."""
    for key, value in DEFAULT_ASSUMPTIONS.items():
        if key not in state:
            state[key] = value


def reset_assumptions(state: MutableMapping[str, Any]) -> None:
    """Restore every slider to its initial value without touching other state."""
    for key, value in DEFAULT_ASSUMPTIONS.items():
        state[key] = value
