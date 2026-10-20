"""Fixed-endpoint evidence-update badges (not movement from current posterior)."""

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from seed_bayes_lab.sensitivity import (
    SLIDER_SPECS, analyze_slider, bayes_delta, bayes_posterior,
    search_delta, search_posterior,
)
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS, EVIDENCE_PRESETS


def _equal(actual, expected):
    if expected is None:
        assert actual is None
    else:
        assert actual == pytest.approx(expected, abs=2e-13)


def test_endpoint_deltas_equal_evidence_update_at_endpoints():
    """The displayed values must be posterior MINUS prior at the endpoint."""
    values = dict(DEFAULT_ASSUMPTIONS)
    for key, spec in SLIDER_SPECS.items():
        scan = analyze_slider(values, key)
        delta = bayes_delta if spec.group == 'bayes' else search_delta
        posterior = bayes_posterior if spec.group == 'bayes' else search_posterior
        for extreme, reported_delta, reported_posterior in (
            (spec.minimum, scan.left_delta, scan.left_posterior),
            (spec.maximum, scan.right_delta, scan.right_posterior),
        ):
            candidate = {**values, key: extreme}
            _equal(reported_delta, delta(candidate))
            _equal(reported_posterior, posterior(candidate))


def test_moving_each_slider_cannot_change_its_own_endpoint_badges():
    """Changing only this dial does not affect its fixed endpoint evaluations."""
    state = dict(DEFAULT_ASSUMPTIONS)
    for key, spec in SLIDER_SPECS.items():
        baseline = analyze_slider(state, key)
        for alternative in (spec.minimum, spec.maximum):
            changed = analyze_slider({**state, key: alternative}, key)
            for field in ('left_delta', 'right_delta', 'left_posterior',
                          'right_posterior', 'minimum_delta', 'maximum_delta'):
                _equal(getattr(changed, field), getattr(baseline, field))
            assert changed.directions == baseline.directions
            assert changed.undefined_positions == baseline.undefined_positions


def test_moving_another_slider_changes_endpoint_badges():
    state = dict(DEFAULT_ASSUMPTIONS)
    original = analyze_slider(state, 'likelihood_succeeded')
    # Moving the intent prior must change the likelihood slider's endpoints.
    modified = analyze_slider({**state, 'prior_intent': 0.75}, 'likelihood_succeeded')
    assert modified.left_delta != pytest.approx(original.left_delta)
    assert modified.right_delta != pytest.approx(original.right_delta)

    original = analyze_slider(state, 'restricted_bits')
    # In the second model, method-U attack knowledge can change the T-bits badges.
    modified = analyze_slider({**state, 'know_unrestricted': 0.9}, 'restricted_bits')
    assert modified.left_delta != pytest.approx(original.left_delta)
    assert modified.right_delta != pytest.approx(original.right_delta)


def test_arrows_are_evidence_update_sign_not_posterior_movement():
    scan = analyze_slider({**DEFAULT_ASSUMPTIONS, **EVIDENCE_PRESETS['benign']}, 'prior_intent')
    assert scan.left_delta == 0
    assert scan.right_delta < 0
    assert scan.current_direction == 'decrease'
    assert not scan.can_reverse
    # Increasing P(I) from 0.5 to 1 increases the posterior but E still
    # decreases the probability of B at that endpoint.
    assert scan.right_posterior > scan.current_posterior


def test_undefined_endpoint_does_not_depend_on_current_position():
    values = {**DEFAULT_ASSUMPTIONS, 'prior_intent': 0.0,
              'likelihood_honest': 0.0}
    scan = analyze_slider(values, 'likelihood_honest')
    assert scan.left_delta is None
    assert scan.left_posterior is None
    altered = analyze_slider({**values, 'likelihood_honest': 0.8}, 'likelihood_honest')
    assert altered.left_delta is None
    assert altered.left_posterior is None
    _equal(altered.right_delta, scan.right_delta)
    _equal(altered.right_posterior, scan.right_posterior)


@pytest.mark.skipif(shutil.which('node') is None, reason='Node optional')
def test_js_and_python_endpoint_sensitivity_match_randomly():
    rng = random.Random(20261019)
    states = [dict(DEFAULT_ASSUMPTIONS)]
    for _ in range(10):
        state = dict(DEFAULT_ASSUMPTIONS)
        for spec in SLIDER_SPECS.values():
            state[spec.key] = rng.choice(spec.positions())
        states.append(state)
    script = Path(__file__).resolve().parents[1] / 'src/seed_bayes_lab/offline.js'
    payload = {'states': states, 'specs': [vars(v) for v in SLIDER_SPECS.values()]}
    code = '''
      require(process.argv[1]);
      const {states,specs} = JSON.parse(process.argv[2]);
      const out = globalThis.SeedBayesOffline;
      console.log(JSON.stringify(states.map(state => specs.map(spec => {
        const v = out.sweep(state, {...spec,min:spec.minimum,max:spec.maximum});
        return {key:spec.key, left:v.left,right:v.right,
                lp:v.leftPosterior,rp:v.rightPosterior,reverse:v.reverse};
      }))));
    '''
    result = subprocess.run(['node', '-e', code, str(script), json.dumps(payload)],
                            text=True, check=True, capture_output=True)
    for state, cases in zip(states, json.loads(result.stdout)):
        for actual in cases:
            scan = analyze_slider(state, actual['key'])
            _equal(actual['left'], scan.left_delta)
            _equal(actual['right'], scan.right_delta)
            _equal(actual['lp'], scan.left_posterior)
            _equal(actual['rp'], scan.right_posterior)
            assert actual['reverse'] == scan.can_reverse
