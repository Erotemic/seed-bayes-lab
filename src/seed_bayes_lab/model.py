"""A three-world Bayesian model with an explicit evidence likelihood.

The worlds are mutually exclusive and exhaustive:
    honest:                 no deliberate backdoor attempt
    attempted_failed:       deliberate attempt, without a planted backdoor
    succeeded:              deliberate attempt, with a planted backdoor

"Succeeded" and "backdoored" refer ONLY to a deliberately selected weakness;
this model says nothing about accidental mathematical vulnerabilities.

A likelihood is the probability of the observed evidence conditional on a world.
All posterior calculations are conditional on the evidence actually occurring.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


def _prob(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite probability in [0, 1], got {value}")
    return value


@dataclass(frozen=True)
class Prior:
    """Prior mass on (honest, failed attempt, successful planted backdoor)."""

    honest: float
    attempted_failed: float
    succeeded: float

    def __post_init__(self) -> None:
        for name in ("honest", "attempted_failed", "succeeded"):
            _prob(name, getattr(self, name))
        if not math.isclose(
            self.honest + self.attempted_failed + self.succeeded,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-10,
        ):
            raise ValueError("The three prior masses must sum to one")

    @classmethod
    def from_intent_success(cls, intent: float, success_given_intent: float) -> Prior:
        """Build a prior from P(intent) and P(backdoor | intent)."""
        intent = _prob("intent", intent)
        success_given_intent = _prob("success_given_intent", success_given_intent)
        return cls(
            honest=1.0 - intent,
            attempted_failed=intent * (1.0 - success_given_intent),
            succeeded=intent * success_given_intent,
        )

    @property
    def intent(self) -> float:
        return self.attempted_failed + self.succeeded

    @property
    def backdoor(self) -> float:
        return self.succeeded

    @property
    def success_given_intent(self) -> float | None:
        return self.succeeded / self.intent if self.intent > 0 else None


@dataclass(frozen=True)
class Likelihoods:
    """Likelihood of the recovered evidence in each of the three worlds.

    These are model assumptions, not empirical estimates about NIST curves.
    """

    honest: float
    attempted_failed: float
    succeeded: float

    def __post_init__(self) -> None:
        for name in ("honest", "attempted_failed", "succeeded"):
            _prob(name, getattr(self, name))


@dataclass(frozen=True)
class Update:
    """All computed probabilities from conditioning on one piece of evidence."""

    prior: Prior
    likelihoods: Likelihoods
    evidence_probability: float
    posterior: Prior

    @property
    def prior_backdoor(self) -> float:
        return self.prior.backdoor

    @property
    def posterior_backdoor(self) -> float:
        return self.posterior.backdoor

    @property
    def prior_intent(self) -> float:
        return self.prior.intent

    @property
    def posterior_intent(self) -> float:
        return self.posterior.intent

    @property
    def conditional_success_before(self) -> float | None:
        return self.prior.success_given_intent

    @property
    def conditional_success_after(self) -> float | None:
        return self.posterior.success_given_intent

    @property
    def probability_multiplier(self) -> float | None:
        """P(backdoor | evidence) / P(backdoor), if the prior is nonzero."""
        return self.posterior_backdoor / self.prior_backdoor if self.prior_backdoor > 0 else None

    @property
    def intent_multiplier(self) -> float | None:
        return self.posterior_intent / self.prior_intent if self.prior_intent > 0 else None

    @property
    def success_multiplier(self) -> float | None:
        before = self.conditional_success_before
        after = self.conditional_success_after
        if before is None or before == 0 or after is None:
            return None
        return after / before

    @property
    def likelihood_given_no_backdoor(self) -> float | None:
        """P(E | not B), averaging honest and failed-attempt worlds."""
        no_backdoor_mass = self.prior.honest + self.prior.attempted_failed
        if no_backdoor_mass == 0:
            return None
        return (
            self.prior.honest * self.likelihoods.honest
            + self.prior.attempted_failed * self.likelihoods.attempted_failed
        ) / no_backdoor_mass

    @property
    def bayes_factor_backdoor(self) -> float | None:
        """P(E | B) / P(E | not B), when the latter is defined.

        Can be infinity if the evidence is impossible without a backdoor.
        This does not itself specify prior probabilities.
        """
        if self.prior.backdoor == 0 or self.prior.backdoor == 1:
            return None
        denominator = self.likelihood_given_no_backdoor
        if denominator is None:
            return None
        if denominator == 0:
            return math.inf if self.likelihoods.succeeded > 0 else None
        return self.likelihoods.succeeded / denominator

    @property
    def delta_backdoor(self) -> float:
        return self.posterior_backdoor - self.prior_backdoor

    def direction(self, abs_tol: float = 1e-13) -> str:
        delta = self.delta_backdoor
        if delta < -abs_tol:
            return "decrease"
        if delta > abs_tol:
            return "increase"
        return "unchanged"


def update(prior: Prior, likelihoods: Likelihoods) -> Update:
    """Bayesian update for the observed evidence, conditioned on occurrence.

    Raises ValueError when the observation has prior probability zero. In
    particular, it does not silently turn undefined posteriors into zero.
    """
    weighted = (
        prior.honest * likelihoods.honest,
        prior.attempted_failed * likelihoods.attempted_failed,
        prior.succeeded * likelihoods.succeeded,
    )
    z = math.fsum(weighted)
    if z <= 0:
        raise ValueError("The observed evidence has probability zero under this model")
    posterior = Prior(*(w / z for w in weighted))
    return Update(prior, likelihoods, z, posterior)


def posterior_backdoor(prior: Prior, likelihoods: Likelihoods) -> float:
    return update(prior, likelihoods).posterior_backdoor
