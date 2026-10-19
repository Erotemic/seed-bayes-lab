"""One-control-at-a-time tests of Bayesian update direction.

For each dial, keep all others fixed and enumerate every position of its UI
slider.  The sign refers to the change caused by *the observation*,
    delta = posterior P(B | E) - prior P(B),
not to the change from today's slider position to another position.

The search tab analogously uses
    delta = P(B | published, T) - P(B | published).
Undefined conditioning is never counted as zero or as a sign reversal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.search import method_observation_update, planted_success

TOLERANCE = 1e-13


@dataclass(frozen=True)
class SliderSpec:
    key: str
    label: str
    minimum: float | int
    maximum: float | int
    step: float | int
    group: str

    def positions(self) -> tuple[float | int, ...]:
        n = round((self.maximum - self.minimum) / self.step)
        assert abs(self.minimum + n * self.step - self.maximum) < 1e-9
        if isinstance(self.minimum, int) and isinstance(self.step, int):
            return tuple(self.minimum + i * self.step for i in range(n + 1))
        return tuple(round(self.minimum + i * self.step, 10) for i in range(n + 1))


BAYES_SLIDERS = (
    SliderSpec("prior_intent", "P(I): malicious intent", 0.0, 1.0, 0.01, "bayes"),
    SliderSpec("success_given_intent", "P(B | I): attack succeeds", 0.0, 1.0, 0.01, "bayes"),
    SliderSpec("likelihood_honest", "P(E | honest)", 0.0, 1.0, 0.01, "bayes"),
    SliderSpec("likelihood_failed", "P(E | attempted but failed)", 0.0, 1.0, 0.01, "bayes"),
    SliderSpec("likelihood_succeeded", "P(E | successful backdoor)", 0.0, 1.0, 0.01, "bayes"),
)

SEARCH_SLIDERS = (
    SliderSpec("restricted_bits", "Timestamp method freedom (bits)", 5, 60, 1, "search"),
    SliderSpec("unrestricted_bits", "Alternative method freedom (bits)", 5, 80, 1, "search"),
    SliderSpec("compute_bits", "Evaluation budget (bits)", 5, 80, 1, "search"),
    SliderSpec("rarity_bits", "Secret vulnerability rarity k (bits)", 5, 80, 1, "search"),
    SliderSpec("know_restricted", "P(attack known | method T)", 0.0, 1.0, 0.01, "search"),
    SliderSpec("know_unrestricted", "P(attack known | method U)", 0.0, 1.0, 0.01, "search"),
    SliderSpec("prior_restricted", "P(method T), before publication", 0.0, 1.0, 0.01, "search"),
    SliderSpec("publish_failed", "P(publish | failed attempt)", 0.0, 1.0, 0.01, "search"),
)

SLIDER_SPECS = {s.key: s for s in (*BAYES_SLIDERS, *SEARCH_SLIDERS)}


def bayes_delta(values: Mapping[str, float | int]) -> float | None:
    """Signed impact of observation E, or None for impossible evidence."""
    prior = Prior.from_intent_success(values["prior_intent"], values["success_given_intent"])
    likelihoods = Likelihoods(
        values["likelihood_honest"], values["likelihood_failed"],
        values["likelihood_succeeded"],
    )
    try:
        return update(prior, likelihoods).delta_backdoor
    except ValueError:
        return None


def bayes_posterior(values: Mapping[str, float | int]) -> float | None:
    """P(B | E) at the supplied slider configuration, or None."""
    prior = Prior.from_intent_success(values["prior_intent"], values["success_given_intent"])
    likelihoods = Likelihoods(
        values["likelihood_honest"], values["likelihood_failed"],
        values["likelihood_succeeded"],
    )
    try:
        return update(prior, likelihoods).posterior_backdoor
    except ValueError:
        return None


def search_delta(values: Mapping[str, float | int]) -> float | None:
    """Signed effect of observing T after publication; None when undefined."""
    st = planted_success(
        values["rarity_bits"], values["restricted_bits"],
        values["compute_bits"], values["know_restricted"],
    )
    su = planted_success(
        values["rarity_bits"], values["unrestricted_bits"],
        values["compute_bits"], values["know_unrestricted"],
    )
    return method_observation_update(
        values["prior_restricted"], st, su, values["publish_failed"]
    ).delta


def search_posterior(values: Mapping[str, float | int]) -> float | None:
    """P(B | published,T) at the supplied slider configuration, or None."""
    st = planted_success(
        values["rarity_bits"], values["restricted_bits"],
        values["compute_bits"], values["know_restricted"],
    )
    su = planted_success(
        values["rarity_bits"], values["unrestricted_bits"],
        values["compute_bits"], values["know_unrestricted"],
    )
    return method_observation_update(
        values["prior_restricted"], st, su, values["publish_failed"]
    ).after


def direction(delta: float | None) -> str:
    if delta is None:
        return "undefined"
    if delta < -TOLERANCE:
        return "decrease"
    if delta > TOLERANCE:
        return "increase"
    return "unchanged"


@dataclass(frozen=True)
class DialSensitivity:
    """Direction changes reachable by adjusting exactly one slider."""

    spec: SliderSpec
    current_delta: float | None
    left_delta: float | None
    right_delta: float | None
    current_posterior: float | None
    left_posterior: float | None
    right_posterior: float | None
    minimum_delta: float | None
    maximum_delta: float | None
    directions: frozenset[str]
    undefined_positions: int

    @property
    def current_direction(self) -> str:
        return direction(self.current_delta)

    @property
    def can_reverse(self) -> bool:
        opposite = {"increase": "decrease", "decrease": "increase"}
        return opposite.get(self.current_direction) in self.directions

    @property
    def can_reach_equality(self) -> bool:
        return self.current_direction in {"increase", "decrease"} and "unchanged" in self.directions

    @property
    def status(self) -> str:
        if self.current_direction == "undefined":
            return "Current conditioning undefined"
        if self.can_reverse:
            return "CAN REVERSE"
        if self.current_direction == "unchanged":
            attainable = self.directions - {"unchanged", "undefined"}
            if len(attainable) == 2:
                return "Can increase or decrease"
            if attainable:
                return "Can " + next(iter(attainable))
            return "Remains unchanged"
        if self.can_reach_equality:
            return "Can reach equality (not reverse)"
        return "Cannot reverse"


def analyze_slider(values: Mapping[str, float | int], key: str) -> DialSensitivity:
    """Enumerate the exact UI lattice, including both endpoints.

    The MIN/MAX deltas are evidence updates at those *fixed* settings:
        P(B | E, slider=end) - P(B | slider=end)
    (or the analogous publication-conditioned delta in the search tab).
    Changing this slider's current position must not change either endpoint;
    changing any other slider may change both. Detect interior reversals as
    well. Undefined conditioning is excluded from extrema, never set to zero.
    """
    spec = SLIDER_SPECS[key]
    evaluator = bayes_delta if spec.group == "bayes" else search_delta
    posterior_evaluator = bayes_posterior if spec.group == "bayes" else search_posterior
    current = evaluator(values)
    current_posterior = posterior_evaluator(values)
    all_deltas: list[float] = []
    signs = set()
    undefined = 0
    endpoints = []
    endpoint_posteriors = []
    for position in spec.positions():
        trial = dict(values)
        trial[key] = position
        delta = evaluator(trial)
        if delta is not None:
            all_deltas.append(delta)
            signs.add(direction(delta))
        else:
            undefined += 1
        if position == spec.minimum or position == spec.maximum:
            endpoints.append(delta)
            endpoint_posteriors.append(posterior_evaluator(trial))
    assert len(endpoints) == len(endpoint_posteriors) == 2
    return DialSensitivity(
        spec, current, endpoints[0], endpoints[1],
        current_posterior, endpoint_posteriors[0], endpoint_posteriors[1],
        min(all_deltas) if all_deltas else None,
        max(all_deltas) if all_deltas else None,
        frozenset(signs), undefined,
    )


def format_delta_pp(delta: float | None) -> str:
    """Signed *percentage points*, not percent change or posterior probability."""
    if delta is None:
        return "undefined"
    if direction(delta) == "unchanged":
        return "≈0 pp"
    points = delta * 100
    magnitude = abs(points)
    if magnitude < 0.001:
        numeric = f"{magnitude:.2g}"
    else:
        numeric = f"{magnitude:.2f}"
    return ("↗ +" if points > 0 else "↘ −") + numeric + " pp"


def formatted_sensitivity(s: DialSensitivity) -> str:
    """Short explanation suitable for an individual Streamlit control."""
    left, right = s.spec.minimum, s.spec.maximum
    return (
        f"◂ at {left:g}: {format_delta_pp(s.left_delta)}   ·   "
        f"**{s.status}**   ·   "
        f"at {right:g}: {format_delta_pp(s.right_delta)} ▸"
    )
