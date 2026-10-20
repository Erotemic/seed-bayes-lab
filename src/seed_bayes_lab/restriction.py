"""An alternative, assumption-driven explanation of an evidence update.

Let I be intent, T mean a genuinely restrictive selection process and B mean
successful deliberate backdooring. The model holds P(I) constant under E and
assumes that E changes backdoor success only by changing P(T | I) from t0 to t1.
Conditional on I and not T the success chance is s; conditional on I and T it
is r*s, independent of E given (I,T). Publication selection is not modeled.

This is NOT another multiplier to apply to the three-world Bayes likelihood
model. Both are alternative explanations of the SAME historical observation.
The parameters are uncalibrated hypothetical assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import magnet_theory as theory


def _unit(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a finite probability in [0,1], got {value}")
    return value


@dataclass(frozen=True)
class RestrictionUpdate:
    """Marginal probability of B before and after E in the toy restriction model."""

    before: float
    after: float
    delta: float
    factor_before: float
    factor_after: float

    @property
    def multiplier(self) -> float | None:
        """Posterior/prior; undefined if the prior is zero."""
        return self.after / self.before if self.before > 0 else None


@theory.approximates(
    "SeedBayes.Restriction.Delta",
    note="Floating-point realization of the exact restriction belief update",
)
@theory.checks("SeedBayes.Restriction.NonIncrease::hp")
@theory.checks("SeedBayes.Restriction.NonIncrease::hs")
@theory.checks("SeedBayes.Restriction.NonIncrease::hr")
def restriction_update(
    intent: float,
    baseline_success: float,
    belief_before: float,
    belief_after: float,
    relative_success: float,
) -> RestrictionUpdate:
    """Compute P(B), P(B|E) under the stated effective-restriction assumptions.

    `belief_before` and `belief_after` are P(T|I) and P(T|I,E), NOT likelihoods
    of the historical evidence. `relative_success` is P(B|I,T)/P(B|I,not T)
    when baseline_success > 0, constrained to [0,1] here.
    """
    p = _unit("intent", intent)
    s = _unit("baseline_success", baseline_success)
    t0 = _unit("belief_before", belief_before)
    t1 = _unit("belief_after", belief_after)
    r = _unit("relative_success", relative_success)
    f0 = 1.0 - t0 * (1.0 - r)
    f1 = 1.0 - t1 * (1.0 - r)
    before = p * s * f0
    after = p * s * f1
    # Evaluate the proved polynomial directly rather than subtracting two
    # nearly equal probabilities when the evidence update is small.
    delta = -(p * s) * (t1 - t0) * (1.0 - r)
    return RestrictionUpdate(before, after, delta, f0, f1)


def restriction_support_warning(intent: float, belief_before: float,
                                belief_after: float) -> str | None:
    """Flag conditional-probability boundaries not achievable by ordinary Bayes.

    The algebra is defined at these values, but with P(E|I)>0 a zero- or
    one-probability prior event cannot become a different posterior value.
    """
    if intent == 0:
        return ("P(T|I) conditions on a zero-probability intent event. "
                "The success parameters are only counterfactual in this setting.")
    if ((belief_before == 0 and belief_after != 0) or
        (belief_before == 1 and belief_after != 1)):
        return ("This t0/t1 pair cannot arise by conditioning on a "
                "positive-probability observation: certainty (0 or 1) "
                "cannot move to another probability under Bayes' rule. "
                "The displayed algebra is a counterfactual comparison only.")
    return None


def restriction_delta_numerator(
    intent: float,
    baseline_success: float,
    belief_before: float,
    belief_after: float,
    relative_success: float,
) -> float:
    """Polynomial update (denominator 1); zero exactly at a break-even."""
    return restriction_update(
        intent, baseline_success, belief_before, belief_after, relative_success
    ).delta
