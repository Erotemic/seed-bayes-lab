"""Test one-at-a-time reversal conditions and undefined probabilities."""

from __future__ import annotations

import json
from pathlib import Path
import random
import shutil
import subprocess

import pytest

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.search import method_observation_update, planted_success
from seed_bayes_lab.sensitivity import (
    SLIDER_SPECS, analyze_slider, bayes_delta, search_delta, restriction_delta, direction,
    format_delta_pp,
)
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS, EVIDENCE_PRESETS


def test_every_slider_is_scanned_inclusive_with_defaults():
    assert len(SLIDER_SPECS) == 19
    assert set(SLIDER_SPECS) == set(DEFAULT_ASSUMPTIONS)
    for key, spec in SLIDER_SPECS.items():
        positions = spec.positions()
        assert positions[0] == spec.minimum
        assert positions[-1] == spec.maximum
        assert DEFAULT_ASSUMPTIONS[key] in positions
        result = analyze_slider(DEFAULT_ASSUMPTIONS, key)
        assert result.left_delta is not None or result.undefined_positions > 0
        assert result.current_direction in {"decrease", "unchanged", "increase"}


def test_default_neutral_evidence_does_not_assume_a_direction():
    assert bayes_delta(DEFAULT_ASSUMPTIONS) == pytest.approx(0.0, abs=1e-14)
    scans = {key: analyze_slider(DEFAULT_ASSUMPTIONS, key) for key, spec in
             SLIDER_SPECS.items() if spec.group == "bayes"}
    assert all(not scan.can_reverse for scan in scans.values())
    assert all(scan.current_direction == "unchanged" for scan in scans.values())
    for key in ("likelihood_honest", "likelihood_failed", "likelihood_succeeded"):
        assert {"decrease", "increase"} <= scans[key].directions


def test_benign_preset_preserves_original_demonstration():
    state = {**DEFAULT_ASSUMPTIONS, **EVIDENCE_PRESETS["benign"]}
    flips = [key for key in SLIDER_SPECS if SLIDER_SPECS[key].group == "bayes"
             and analyze_slider(state, key).can_reverse]
    assert flips == ["likelihood_succeeded"]
    intent = analyze_slider(state, "prior_intent")
    assert intent.can_reach_equality
    assert not intent.can_reverse
    assert direction(intent.left_delta) == "unchanged"
    assert direction(intent.right_delta) == "decrease"


def test_default_search_flip_and_interior_extrema():
    flips = [key for key in SLIDER_SPECS if SLIDER_SPECS[key].group == "search"
             and analyze_slider(DEFAULT_ASSUMPTIONS, key).can_reverse]
    assert flips == ["unrestricted_bits", "know_unrestricted"]
    rarity = analyze_slider(DEFAULT_ASSUMPTIONS, "rarity_bits")
    assert direction(rarity.left_delta) == "unchanged"
    assert direction(rarity.right_delta) == "unchanged"
    assert rarity.minimum_delta < -0.05  # genuine interior effect, not at endpoints
    assert not rarity.can_reverse
    publish = analyze_slider(DEFAULT_ASSUMPTIONS, "publish_failed")
    assert publish.minimum_delta < publish.left_delta  # interior strongest effect
    assert publish.minimum_delta < publish.right_delta


def test_zero_probability_conditioning_is_not_equality():
    values = dict(DEFAULT_ASSUMPTIONS)
    values.update(prior_intent=0.0, likelihood_honest=0.0)
    assert bayes_delta(values) is None
    result = analyze_slider(values, "likelihood_honest")
    assert result.current_direction == "undefined"
    assert result.left_delta is None
    assert result.undefined_positions == 1
    assert not result.can_reverse

    values = dict(DEFAULT_ASSUMPTIONS)
    values["prior_restricted"] = 0.0
    assert search_delta(values) is None
    search_result = analyze_slider(values, "prior_restricted")
    assert search_result.left_delta is None
    assert search_result.current_direction == "undefined"
    assert not search_result.can_reverse
    assert "undefined" in format_delta_pp(search_result.left_delta)


def test_100_percent_intent_has_nontrivial_update_but_honest_dial_no_effect():
    values = {**DEFAULT_ASSUMPTIONS, **EVIDENCE_PRESETS["benign"]}
    values["prior_intent"] = 1.0
    assert direction(bayes_delta(values)) == "decrease"
    honest_sweep = analyze_slider(values, "likelihood_honest")
    assert honest_sweep.left_delta == pytest.approx(honest_sweep.right_delta)
    assert honest_sweep.status == "Cannot reverse"
    assert analyze_slider(values, "likelihood_succeeded").can_reverse


def test_search_delta_agrees_with_direct_difference():
    rng = random.Random(20261019)
    for _ in range(500):
        st = rng.uniform(0.001, 0.999)
        su = rng.uniform(0.001, 0.999)
        alpha = rng.uniform(0.001, 0.999)
        rho = rng.uniform(0.001, 1)
        result = method_observation_update(alpha, st, su, rho)
        assert result.delta == pytest.approx(result.after - result.before, abs=5e-13)


def test_deltas_match_original_probability_implementations():
    rng = random.Random(20261019)
    for _ in range(200):
        values = dict(DEFAULT_ASSUMPTIONS)
        for key in values:
            spec = SLIDER_SPECS[key]
            values[key] = rng.choice(spec.positions())
        prior = Prior.from_intent_success(values["prior_intent"], values["success_given_intent"])
        likely = Likelihoods(
            values["likelihood_honest"], values["likelihood_failed"],
            values["likelihood_succeeded"],
        )
        expected = update(prior, likely).delta_backdoor
        assert bayes_delta(values) == pytest.approx(expected)
        st = planted_success(values["rarity_bits"],values["restricted_bits"],
                             values["compute_bits"],values["know_restricted"])
        su = planted_success(values["rarity_bits"],values["unrestricted_bits"],
                             values["compute_bits"],values["know_unrestricted"])
        expected_method = method_observation_update(
            values["prior_restricted"],st,su,values["publish_failed"]
        ).delta
        assert search_delta(values) == pytest.approx(expected_method)
        d = (values["restriction_before"] * values["restriction_evidence_t"]
             + (1 - values["restriction_before"]) * values["restriction_evidence_u"])
        if d == 0:
            assert restriction_delta(values) is None
        else:
            assert restriction_delta(values) == pytest.approx(
                values["restriction_intent"] * values["restriction_before"]
                * (1 - values["restriction_before"])
                * (values["restriction_evidence_t"] - values["restriction_evidence_u"])
                * (values["restriction_success_t"] - values["restriction_success_u"])
                / d
            )


@pytest.mark.skipif(shutil.which("node") is None, reason="Node is optional")
def test_offline_javascript_agrees_with_python():
    """Numerical consistency between static HTML and Python implementations."""
    rng = random.Random(20261019)
    cases = []
    for _ in range(100):
        trial = dict(DEFAULT_ASSUMPTIONS)
        for key in trial:
            trial[key] = rng.choice(SLIDER_SPECS[key].positions())
        cases.append(trial)
    script = Path(__file__).resolve().parents[1] / "src/seed_bayes_lab/offline.js"
    node_code = '''
        require(process.argv[1]);
        const cases = JSON.parse(process.argv[2]);
        const {finiteBayes,methodUpdate,restrictionUpdate} = globalThis.SeedBayesOffline;
        console.log(JSON.stringify(cases.map(s => {
            const b=finiteBayes(s),m=methodUpdate(s),r=restrictionUpdate(s);
            return [b.before,b.after,b.delta,m.before,m.after,m.delta,r.before,r.after,r.delta];
        })));
    '''
    response = subprocess.run(["node", "-e", node_code, str(script),json.dumps(cases)],
                              check=True, text=True, capture_output=True)
    results = json.loads(response.stdout)
    for state, vals in zip(cases, results):
        prior = Prior.from_intent_success(state["prior_intent"],state["success_given_intent"])
        likely = Likelihoods(state["likelihood_honest"],state["likelihood_failed"],
                             state["likelihood_succeeded"])
        try:
            res = update(prior, likely)
            expected = [res.prior_backdoor, res.posterior_backdoor, res.delta_backdoor]
        except ValueError:
            expected = [prior.backdoor,None,None]
        st = planted_success(state["rarity_bits"],state["restricted_bits"],
                             state["compute_bits"],state["know_restricted"])
        su = planted_success(state["rarity_bits"],state["unrestricted_bits"],
                             state["compute_bits"],state["know_unrestricted"])
        method = method_observation_update(state["prior_restricted"],st,su,state["publish_failed"])
        expected += [method.before,method.after,method.delta]
        from seed_bayes_lab.restriction import restriction_update
        rr = restriction_update(
            state["restriction_intent"], state["restriction_before"],
            state["restriction_evidence_t"], state["restriction_evidence_u"],
            state["restriction_success_u"], state["restriction_success_t"],
        )
        expected += [rr.before,rr.after,rr.delta]
        for actual, want in zip(vals,expected):
            if want is None:
                assert actual is None
            else:
                assert actual == pytest.approx(want,rel=1e-10,abs=2e-13)
