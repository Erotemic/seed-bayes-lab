"""Illustrative search/selection models, explicitly separate from Bayes' theorem.

The independence / rarity assumptions in this module are NOT empirical facts
about real elliptic curves. They are user-adjustable hypotheses.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


def _unit_interval(name: str, p: float) -> float:
    p = float(p)
    if not math.isfinite(p) or p < 0.0 or p > 1.0:
        raise ValueError(f"{name} must be in [0,1]")
    return p


def _nonnegative_bits(name: str, bits: float) -> float:
    bits = float(bits)
    if not math.isfinite(bits) or bits < 0.0 or bits > 900:
        raise ValueError(f"{name} must be finite and between 0 and 900")
    return bits


def independent_search_success(rarity_bits: float, trials_bits: float) -> float:
    """Numerically stable 1 - (1 - 2^(-k))^(2^b).

    ``trials_bits`` may be nonintegral (effective search effort). The formula
    then interpolates real-valued search effort; for literal independent trials,
    use an integer number of attempts.
    """
    k = _nonnegative_bits("rarity_bits", rarity_bits)
    b = _nonnegative_bits("trials_bits", trials_bits)
    q = math.exp2(-k)
    if q == 1:
        return 1.0
    # The expm1/log1p combination avoids catastrophic cancellation in the tail.
    return -math.expm1(math.exp2(b) * math.log1p(-q))


def effective_search_success(
    rarity_bits: float, freedom_bits: float, budget_bits: float
) -> float:
    """Search succeeds among min(2^freedom, 2^budget) independent candidates."""
    freedom = _nonnegative_bits("freedom_bits", freedom_bits)
    budget = _nonnegative_bits("budget_bits", budget_bits)
    return independent_search_success(rarity_bits, min(freedom, budget))


def planted_success(
    rarity_bits: float, freedom_bits: float, budget_bits: float, know_attack: float
) -> float:
    """P(knowing a recognizable attack) times conditional search success."""
    return _unit_interval("know_attack", know_attack) * effective_search_success(
        rarity_bits, freedom_bits, budget_bits
    )


def publish_probability(success: float, publish_if_failed: float) -> float:
    """P(published) if successful attempts always publish.

    A failed attempt publishes with the user-defined probability rho.
    rho=1: always publish, including failures.
    rho=0: only successful backdoors get published.
    """
    s = _unit_interval("success", success)
    rho = _unit_interval("publish_if_failed", publish_if_failed)
    return s + (1.0 - s) * rho


@dataclass(frozen=True)
class MethodUpdate:
    """Observe method T among already-published outputs.

    The method is chosen ex ante: P(T)=alpha, and P(U)=1-alpha. Each method
    has a specified success chance. All successful attempts are published; failed
    attempts publish with common probability rho. Observation E identifies T.
    """

    prior_restricted: float
    restricted_success: float
    unrestricted_success: float
    publish_if_failed: float
    probability_published: float
    probability_published_and_restricted: float
    before: float | None
    after: float | None

    @property
    def delta(self) -> float | None:
        if self.before is None or self.after is None:
            return None
        return self.after - self.before

    @property
    def method_probability_given_published(self) -> float | None:
        if self.probability_published == 0:
            return None
        return self.probability_published_and_restricted / self.probability_published


def method_observation_update(
    prior_restricted: float,
    restricted_success: float,
    unrestricted_success: float,
    publish_if_failed: float = 1.0,
) -> MethodUpdate:
    """Compute P(backdoor | published) and P(backdoor | published, method=T).

    Raises no exception for conditioning on probability-zero events; instead
    the corresponding result is None, so it cannot be presented as evidence.
    """
    a = _unit_interval("prior_restricted", prior_restricted)
    st = _unit_interval("restricted_success", restricted_success)
    su = _unit_interval("unrestricted_success", unrestricted_success)
    rho = _unit_interval("publish_if_failed", publish_if_failed)
    pt = publish_probability(st, rho)
    pu = publish_probability(su, rho)
    all_pub = a * pt + (1.0 - a) * pu
    t_pub = a * pt
    before = (a * st + (1.0 - a) * su) / all_pub if all_pub > 0 else None
    after = st / pt if pt > 0 and a > 0 else None
    return MethodUpdate(a, st, su, rho, all_pub, t_pub, before, after)
