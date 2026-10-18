import math
import random

import pytest

from seed_bayes_lab.model import Likelihoods, Prior, update


def test_exact_three_world_example():
    prior = Prior(0.5, 0.25, 0.25)
    evidence = Likelihoods(0.5, 0.5, 0.25)
    result = update(prior, evidence)
    assert result.evidence_probability == pytest.approx(7 / 16)
    assert result.prior_backdoor == pytest.approx(1 / 4)
    assert result.posterior_backdoor == pytest.approx(1 / 7)
    assert result.prior_intent == pytest.approx(1 / 2)
    assert result.posterior_intent == pytest.approx(3 / 7)
    assert result.conditional_success_after == pytest.approx(1 / 3)
    assert result.bayes_factor_backdoor == pytest.approx(0.5)
    assert result.direction() == "decrease"


def test_factorization_and_bayes_odds_random():
    generator = random.Random(20261018)
    for _ in range(1200):
        prior_values = [generator.uniform(0.001, 1.0) for _ in range(3)]
        z = sum(prior_values)
        prior = Prior(*(x / z for x in prior_values))
        evidence = Likelihoods(*(generator.uniform(0.001, 1.0) for _ in range(3)))
        result = update(prior, evidence)
        assert result.prior_backdoor == pytest.approx(
            result.prior_intent * result.conditional_success_before
        )
        assert result.posterior_backdoor == pytest.approx(
            result.posterior_intent * result.conditional_success_after
        )
        assert result.probability_multiplier == pytest.approx(
            result.intent_multiplier * result.success_multiplier
        )
        prior_odds = result.prior_backdoor / (1 - result.prior_backdoor)
        posterior_odds = result.posterior_backdoor / (1 - result.posterior_backdoor)
        assert posterior_odds == pytest.approx(prior_odds * result.bayes_factor_backdoor)
        ell_b = evidence.succeeded
        ell_no_b = result.likelihood_given_no_backdoor
        observed_direction = result.posterior_backdoor - result.prior_backdoor
        assert (observed_direction < 0) == (ell_b < ell_no_b)
        assert (observed_direction > 0) == (ell_b > ell_no_b)


def test_intent_certain_but_probability_can_still_fall():
    prior = Prior.from_intent_success(intent=1.0, success_given_intent=0.4)
    result = update(prior, Likelihoods(honest=0.9, attempted_failed=0.8, succeeded=0.1))
    assert result.prior_intent == 1.0
    assert result.posterior_intent == pytest.approx(1.0)
    assert result.prior_backdoor == pytest.approx(0.4)
    assert result.posterior_backdoor == pytest.approx(0.04 / (0.48 + 0.04))
    assert result.posterior_backdoor < result.prior_backdoor


def test_intent_certain_but_probability_can_increase():
    prior = Prior.from_intent_success(1.0, 0.4)
    result = update(prior, Likelihoods(0.1, 0.1, 0.9))
    assert result.posterior_backdoor > result.prior_backdoor


def test_equal_likelihoods_do_not_update_any_prior():
    for intent in [0, 0.1, 0.9, 1]:
        for success in [0, 0.2, 1]:
            prior = Prior.from_intent_success(intent, success)
            result = update(prior, Likelihoods(0.23, 0.23, 0.23))
            assert result.posterior_backdoor == pytest.approx(prior.backdoor)
            assert result.posterior_intent == pytest.approx(prior.intent)


def test_impossible_evidence_rejected():
    with pytest.raises(ValueError, match="probability zero"):
        update(Prior(1.0, 0.0, 0.0), Likelihoods(0.0, 1.0, 1.0))


def test_zero_prior_cases_are_not_invented():
    result = update(Prior(1.0, 0.0, 0.0), Likelihoods(0.1, 1.0, 1.0))
    assert result.posterior_backdoor == 0.0
    assert result.probability_multiplier is None
    assert result.conditional_success_after is None
    assert result.bayes_factor_backdoor is None
    result = update(Prior(0.0, 0.0, 1.0), Likelihoods(0.1, 0.2, 0.3))
    assert result.posterior_backdoor == 1.0
    assert result.likelihood_given_no_backdoor is None


def test_input_validation():
    with pytest.raises(ValueError):
        Prior(0.1, 0.1, 0.1)
    with pytest.raises(ValueError):
        Prior(-0.1, 0.1, 1.0)
    with pytest.raises(ValueError):
        Likelihoods(0.2, 1.2, 0.1)
    with pytest.raises(ValueError):
        Prior(float("nan"), 0, 1)
    with pytest.raises(ValueError):
        Prior.from_intent_success(1.2, 0.5)
