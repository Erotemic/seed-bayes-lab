"""Bayesian effective-restriction model with six probability-valued inputs.

I: intent; B: successfully planted backdoor; T: genuinely binding restriction;
E: the actual seed-provenance evidence. This is an ALTERNATIVE explanation
of E to the three-world likelihood model, not an additional Bayes multiplier.

Input probabilities:
  p = P(I), t = P(T | I), eT = P(E | I,T), eU = P(E | I,not T),
  sT = P(B | I,T), sU = P(B | I,not T).

Assume E and B are conditionally independent given I,T, and given I,not T.
Also assume P(E | not I) = t*eT + (1-t)*eU; this ensures P(I|E)=P(I).
For positive evidence mass D = t*eT+(1-t)*eU:
  t1 = P(T|I,E) = t*eT / D
  before = p*((1-t)*sU+t*sT)
  after = p*((1-t1)*sU+t1*sT)
  delta = p*t*(1-t)*(eT-eU)*(sT-sU)/D.
No posterior exists when D=0. None of these parameters is historically calibrated.
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
    """Probabilities and Bayesian update for the alternative restriction model."""

    before: float
    after: float | None
    delta: float | None
    belief_after: float | None
    evidence_mass: float

    @property
    def multiplier(self) -> float | None:
        """Posterior/prior; undefined when evidence is impossible or prior zero."""
        return self.after / self.before if self.after is not None and self.before > 0 else None


@theory.approximates(
    "SeedBayes.Restriction.Posterior",
    note="Bayes-derived P(T|I,E) and the marginal backdoor update",
)
@theory.checks("SeedBayes.Restriction.Posterior::hD",
               note="Undefined if the observed evidence has zero probability")
@theory.approximates("SeedBayes.Restriction.Delta",
                     note="Computes the proved rational delta directly")
def restriction_update(
    intent: float,
    belief_before: float,
    evidence_restricted: float,
    evidence_unrestricted: float,
    success_unrestricted: float,
    success_restricted: float,
) -> RestrictionUpdate:
    """Compute P(B), P(B|E), and P(T|I,E) from six probabilities.

    Unlike the old relative-success ratio, both attack success rates are
    explicit probabilities and may be ordered either way. This exposes the
    monotonicity assumption instead of silently enforcing it.
    """
    p = _unit("intent", intent)
    t = _unit("belief_before", belief_before)
    e_t = _unit("evidence_restricted", evidence_restricted)
    e_u = _unit("evidence_unrestricted", evidence_unrestricted)
    s_u = _unit("success_unrestricted", success_unrestricted)
    s_t = _unit("success_restricted", success_restricted)

    before = p * ((1 - t) * s_u + t * s_t)
    d = t * e_t + (1 - t) * e_u
    if d == 0:
        return RestrictionUpdate(before, None, None, None, d)
    posterior_t = t * e_t / d
    after = p * ((1 - posterior_t) * s_u + posterior_t * s_t)
    # Algebraic numerator avoids cancellation in P(B|E) - P(B).
    delta = p * t * (1 - t) * (e_t - e_u) * (s_t - s_u) / d
    return RestrictionUpdate(before, after, delta, posterior_t, d)


def restriction_support_warning(intent: float, belief_before: float,
                                evidence_restricted: float,
                                evidence_unrestricted: float) -> str | None:
    """Call out conditioning on zero-probability intent and impossible E."""
    t = belief_before
    d = t * evidence_restricted + (1 - t) * evidence_unrestricted
    if d == 0:
        return "The evidence has probability zero under this model; no posterior is defined."
    if intent == 0:
        return ("P(T|I) conditions on a zero-probability intent event. "
                "The success and conditional-evidence inputs are counterfactual here.")
    return None


def restriction_delta_numerator(
    intent: float, belief_before: float, evidence_restricted: float,
    evidence_unrestricted: float, success_unrestricted: float,
    success_restricted: float,
) -> float | None:
    """Provably sign-equivalent polynomial numerator; None when P(E)=0."""
    p, t, e_t, e_u, s_u, s_t = (float(x) for x in (
        intent, belief_before, evidence_restricted, evidence_unrestricted,
        success_unrestricted, success_restricted,
    ))
    d = t * e_t + (1 - t) * e_u
    if not d > 0:
        return None
    return p * t * (1 - t) * (e_t - e_u) * (s_t - s_u)
