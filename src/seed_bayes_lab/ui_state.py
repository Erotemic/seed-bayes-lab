"""Centralized, tested Streamlit slider defaults and reset behavior."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

DEFAULT_ASSUMPTIONS: dict[str, float | int] = {
    "prior_intent": 0.20,
    "success_given_intent": 0.30,
    "likelihood_honest": 0.80,
    "likelihood_failed": 0.60,
    "likelihood_succeeded": 0.20,
    "restricted_bits": 30,
    "unrestricted_bits": 60,
    "compute_bits": 36,
    "rarity_bits": 40,
    "know_restricted": 0.30,
    "know_unrestricted": 0.30,
    "prior_restricted": 0.50,
    "publish_failed": 1.0,
}


def initialize_assumptions(state: MutableMapping[str, Any]) -> None:
    """Insert defaults only if a control has not already been initialized."""
    for key, value in DEFAULT_ASSUMPTIONS.items():
        if key not in state:
            state[key] = value


def reset_assumptions(state: MutableMapping[str, Any]) -> None:
    """Restore every slider to its initial value without touching other state."""
    for key, value in DEFAULT_ASSUMPTIONS.items():
        state[key] = value
