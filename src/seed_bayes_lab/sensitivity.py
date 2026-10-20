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
import math
from typing import Mapping

import magnet_theory as theory

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.restriction import restriction_update
from seed_bayes_lab.search import method_observation_update, planted_success, publish_probability

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

RESTRICTION_SLIDERS = (
    SliderSpec("restriction_intent", "P(I): malicious intent", 0.0, 1.0, 0.01, "restriction"),
    SliderSpec("restriction_baseline_success", "P(B | I, not T): baseline success", 0.0, 1.0, 0.01, "restriction"),
    SliderSpec("restriction_before", "P(T | I): restriction belief before E", 0.0, 1.0, 0.01, "restriction"),
    SliderSpec("restriction_after", "P(T | I,E): restriction belief after E", 0.0, 1.0, 0.01, "restriction"),
    SliderSpec("restriction_ratio", "r: relative success when restricted", 0.0, 1.0, 0.01, "restriction"),
)

SLIDER_SPECS = {s.key: s for s in (*BAYES_SLIDERS, *SEARCH_SLIDERS, *RESTRICTION_SLIDERS)}


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


def restriction_result(values: Mapping[str, float | int]):
    """Evaluate the standalone effective-restriction explanation of E."""
    return restriction_update(
        values["restriction_intent"], values["restriction_baseline_success"],
        values["restriction_before"], values["restriction_after"],
        values["restriction_ratio"],
    )


def restriction_delta(values: Mapping[str, float | int]) -> float:
    return restriction_result(values).delta


def restriction_posterior(values: Mapping[str, float | int]) -> float:
    return restriction_result(values).after


def direction(delta: float | None) -> str:
    if delta is None:
        return "undefined"
    if delta < -TOLERANCE:
        return "decrease"
    if delta > TOLERANCE:
        return "increase"
    return "unchanged"


@dataclass(frozen=True)
class BreakEvenRegion:
    """Where the evidence update is zero when only one input varies.

    An isolated zero has start=end. A nonzero-width region represents a
    sampled interval of equality, not an arbitrary root selected from it.
    `interpolated` distinguishes a crossing between selectable UI positions.
    """

    start: float
    end: float
    interpolated: bool = False

    @property
    def is_interval(self) -> bool:
        return self.end > self.start + 1e-9


@theory.approximates(
    "SeedBayes.Bayes.BreakEven",
    note="UI root finding evaluates the Lean Bayes delta numerator in floating point",
)
@theory.checks(
    "SeedBayes.Bayes.BreakEven::hE",
    note="Returns None if evidence mass is zero in the Bayes branch",
)
@theory.approximates(
    "SeedBayes.Publication.BreakEven",
    note="UI root finding evaluates rho*(1-alpha)*(st-su) in floating point",
)
@theory.checks(
    "SeedBayes.Publication.BreakEven::hPt",
    note="Returns None for zero P(J|T) in the publication branch",
)
@theory.checks(
    "SeedBayes.Publication.BreakEven::hJ",
    note="Returns None for zero P(J) in the publication branch",
)
def _zero_numerator(values: Mapping[str, float | int], group: str) -> float | None:
    """Numerator of the signed evidence update, with conditioning checked.

    A numerator is preferable to testing whether a very small posterior
    difference falls below the *display* tolerance: negligible changes are
    not automatically mathematical break-even points.
    """
    if group == "restriction":
        result = restriction_result(values)
        # The exact polynomial derived in SeedBayes.Restriction. All settings
        # are defined, even at a zero prior (when the ratio is undefined).
        return result.delta
    if group == "bayes":
        intent = float(values["prior_intent"])
        success = float(values["success_given_intent"])
        honest = 1.0 - intent
        failed = intent * (1.0 - success)
        backdoor = intent * success
        lh = float(values["likelihood_honest"])
        lf = float(values["likelihood_failed"])
        lb = float(values["likelihood_succeeded"])
        evidence = honest * lh + failed * lf + backdoor * lb
        if evidence <= 0:
            return None
        # Exact finite-model identity: equal nonzero likelihoods make E
        # independent of the world, whatever the prior masses. Avoid
        # spurious roots caused by cancellation in floating-point arithmetic.
        if lh == lf == lb:
            return 0.0
        # delta = backdoor * ((honest+failed)*lb - honest*lh - failed*lf)/evidence
        return backdoor * ((honest + failed) * lb - honest * lh - failed * lf)

    st = planted_success(
        values["rarity_bits"], values["restricted_bits"],
        values["compute_bits"], values["know_restricted"],
    )
    su = planted_success(
        values["rarity_bits"], values["unrestricted_bits"],
        values["compute_bits"], values["know_unrestricted"],
    )
    a = float(values["prior_restricted"])
    rho = float(values["publish_failed"])
    pt = publish_probability(st, rho)
    pu = publish_probability(su, rho)
    published = a * pt + (1.0 - a) * pu
    if a <= 0 or pt <= 0 or published <= 0:
        return None
    # delta = rho*(1-a)*(st-su)/(pt*published)
    if rho == 0 or a == 1:
        return 0.0
    difference = st - su
    # The floating-point search probability saturates at 1 for large trial
    # counts. If knowledge probabilities are identical, unequal finite trial
    # counts nonetheless imply STRICT inequality mathematically (q in (0,1)).
    # Preserve its sign to avoid drawing a spurious interval of equality.
    kt, ku = float(values["know_restricted"]), float(values["know_unrestricted"])
    nt = min(float(values["restricted_bits"]), float(values["compute_bits"]))
    nu = min(float(values["unrestricted_bits"]), float(values["compute_bits"]))
    if difference == 0.0 and kt == ku and kt > 0 and nt != nu:
        return math.copysign(math.ulp(0.0), nt - nu)
    return rho * (1.0 - a) * difference


def break_even_regions(values: Mapping[str, float | int], key: str) -> tuple[BreakEvenRegion, ...]:
    """Find zero-update points and intervals with the other dials fixed.

    Inspect the full selectable lattice and refine any sign crossing by
    bisection on a continuous extension of the selected parameter. An
    interpolated point may not be *selectable* on a stepped slider; the UI
    labels it approximately. Undefined conditioning never creates a marker.
    Adjacent exactly-zero samples form an equality interval. This algorithm
    does not claim to find unobserved tangencies between grid positions.
    """
    spec = SLIDER_SPECS[key]
    positions = spec.positions()
    driver = []
    for position in positions:
        candidate = dict(values)
        candidate[key] = position
        driver.append(_zero_numerator(candidate, spec.group))

    result: list[BreakEvenRegion] = []
    idx = 0
    while idx < len(positions):
        if driver[idx] is not None and driver[idx] == 0.0:
            end = idx
            while end + 1 < len(positions) and driver[end + 1] == 0.0:
                end += 1
            result.append(BreakEvenRegion(float(positions[idx]), float(positions[end])))
            idx = end + 1
        else:
            idx += 1

    for idx in range(len(positions) - 1):
        lhs, rhs = driver[idx], driver[idx + 1]
        if lhs is None or rhs is None or lhs == 0 or rhs == 0 or (lhs > 0) == (rhs > 0):
            continue
        low, high = float(positions[idx]), float(positions[idx + 1])
        sign_low = lhs > 0
        for _ in range(55):
            mid = (low + high) / 2
            if mid == low or mid == high:
                break
            candidate = dict(values)
            candidate[key] = mid
            mid_value = _zero_numerator(candidate, spec.group)
            if mid_value is None:
                # Cannot infer a zero by crossing a forbidden conditioning point.
                break
            if mid_value == 0.0:
                low = high = mid
                break
            if (mid_value > 0) == sign_low:
                low = mid
            else:
                high = mid
        root = (low + high) / 2
        candidate = dict(values)
        candidate[key] = root
        if _zero_numerator(candidate, spec.group) is not None:
            result.append(BreakEvenRegion(root, root, interpolated=True))

    return tuple(sorted(result, key=lambda region: region.start))


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
    break_evens: tuple[BreakEvenRegion, ...]

    @property
    def current_direction(self) -> str:
        return direction(self.current_delta)

    @property
    def can_reverse(self) -> bool:
        opposite = {"increase": "decrease", "decrease": "increase"}
        return opposite.get(self.current_direction) in self.directions

    @property
    def can_reach_equality(self) -> bool:
        return (self.current_direction in {"increase", "decrease"}
                and any(not root.interpolated for root in self.break_evens))

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
    evaluators = {
        "bayes": (bayes_delta, bayes_posterior),
        "search": (search_delta, search_posterior),
        "restriction": (restriction_delta, restriction_posterior),
    }
    evaluator, posterior_evaluator = evaluators[spec.group]
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
        frozenset(signs), undefined, break_even_regions(values, key),
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
