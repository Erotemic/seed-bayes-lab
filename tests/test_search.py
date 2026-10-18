import math
import random

import pytest

from seed_bayes_lab.search import (
    effective_search_success,
    independent_search_success,
    method_observation_update,
    planted_success,
    publish_probability,
)


def test_exact_small_trial_counts():
    for k in (1, 5, 10, 20):
        q = 2 ** (-k)
        for b in (0, 1, 3, 8):
            expected = 1 - (1 - q) ** (2 ** b)
            got = independent_search_success(k, b)
            assert got == pytest.approx(expected, abs=1e-14)


def test_stability_for_extremely_rare_targets():
    # Naively computing (1 - 2^-100)^2^30 yields zero from cancellation.
    p = independent_search_success(100, 30)
    assert p > 0
    assert p == pytest.approx(2 ** -70, rel=1e-12)
    assert independent_search_success(20, 50) == pytest.approx(1.0)


def test_freedom_and_budget_monotonicity():
    for k in (10, 20, 30, 40, 70):
        restricted = effective_search_success(k, freedom_bits=25, budget_bits=50)
        unrestricted = effective_search_success(k, freedom_bits=70, budget_bits=50)
        assert restricted <= unrestricted + 1e-15
        budget_limited = effective_search_success(k, 25, 20)
        assert budget_limited <= restricted + 1e-15


def test_when_compute_limited_methods_are_equivalent():
    for k in range(15, 70, 5):
        a = effective_search_success(k, freedom_bits=30, budget_bits=18)
        b = effective_search_success(k, freedom_bits=60, budget_bits=18)
        assert a == b


def test_method_discovery_lowers_success_for_narrower_search():
    generator = random.Random(20261018)
    for _ in range(1000):
        st = generator.random()
        su = generator.uniform(st, 1.0)
        a = generator.uniform(0.01, 0.99)
        rho = generator.uniform(0.001, 1.0)
        res = method_observation_update(a, st, su, rho)
        assert res.before is not None and res.after is not None
        assert res.after <= res.before + 1e-13


def test_conditioning_on_success_only_eliminates_direction():
    result = method_observation_update(
        prior_restricted=0.4, restricted_success=0.001,
        unrestricted_success=0.9, publish_if_failed=0.0,
    )
    assert result.before == pytest.approx(1.0)
    assert result.after == pytest.approx(1.0)
    assert result.delta == pytest.approx(0.0)


def test_method_success_can_increase_with_conditional_capability():
    # The algorithmic candidate set is narrower but someone who knows an
    # attack is much more likely to choose the restricted method in this model.
    rarity = 25
    st = planted_success(rarity, 30, 36, know_attack=0.9)
    su = planted_success(rarity, 60, 36, know_attack=0.01)
    result = method_observation_update(0.5, st, su)
    assert st > su
    assert result.delta > 0


def test_zero_probability_observation_is_undefined():
    res = method_observation_update(0.0, 0.3, 0.6)
    assert res.after is None
    res = method_observation_update(0.5, 0.0, 0.0, publish_if_failed=0.0)
    assert res.before is None
    assert res.after is None


def test_publication_extremes():
    for s in [0.001, 0.2, 0.9, 1]:
        assert publish_probability(s, 0) == pytest.approx(s)
        assert publish_probability(s, 1) == pytest.approx(1)
    with pytest.raises(ValueError):
        independent_search_success(20, -1)
    with pytest.raises(ValueError):
        method_observation_update(1.5, 0.2, 0.3)
