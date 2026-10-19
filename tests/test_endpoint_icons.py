"""Posterior movement badges are not confused with sign of evidence updates."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from seed_bayes_lab.sensitivity import (
    SLIDER_SPECS, analyze_slider, bayes_posterior, search_posterior,
)
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def test_endpoints_change_posterior_relative_to_current():
    values = dict(DEFAULT_ASSUMPTIONS)
    for key, spec in SLIDER_SPECS.items():
        scan = analyze_slider(values, key)
        posterior = bayes_posterior if spec.group == 'bayes' else search_posterior
        assert scan.current_posterior == pytest.approx(posterior(values), abs=1e-14)
        for edge_value, endpoint, movement in [
            (spec.minimum, scan.left_posterior, scan.left_posterior_change),
            (spec.maximum, scan.right_posterior, scan.right_posterior_change),
        ]:
            candidate = {**values, key: edge_value}
            expected = posterior(candidate)
            assert endpoint == pytest.approx(expected, abs=1e-14)
            if expected is None or scan.current_posterior is None:
                assert movement is None
            else:
                assert movement == pytest.approx(expected-scan.current_posterior, abs=1e-14)


def test_posterior_movement_differs_from_update_sign():
    scan = analyze_slider(DEFAULT_ASSUMPTIONS, 'prior_intent')
    assert scan.left_posterior_change < 0
    assert scan.right_posterior_change > 0
    assert scan.current_direction == 'decrease'
    assert scan.can_reverse is False
    assert scan.right_delta < 0
    # Moving prior_intent to the maximum increases the posterior but still
    # leaves the evidence update P(B | E) - P(B) negative.


def test_undefined_conditioning_is_not_displayed_as_zero_movement():
    values = dict(DEFAULT_ASSUMPTIONS)
    values['prior_intent'] = 0.0
    values['likelihood_honest'] = 0.0
    s = analyze_slider(values, 'likelihood_honest')
    assert s.current_posterior is None
    assert s.left_posterior is None
    assert s.left_posterior_change is None
    assert s.right_posterior_change is None


@pytest.mark.skipif(shutil.which('node') is None, reason='Node optional')
def test_js_and_python_endpoint_sensitivity_match():
    script = Path(__file__).resolve().parents[1] / 'src/seed_bayes_lab/offline.js'
    payload = {'state': DEFAULT_ASSUMPTIONS, 'specs': [vars(v) for v in SLIDER_SPECS.values()]}
    code = '''
      require(process.argv[1]);
      const {state,specs} = JSON.parse(process.argv[2]);
      const out = globalThis.SeedBayesOffline;
      console.log(JSON.stringify(specs.map(spec => {
        const v = out.sweep(state, {...spec,min:spec.minimum,max:spec.maximum});
        return {key:spec.key,cp:v.currentPosterior,lp:v.leftPosterior,rp:v.rightPosterior,
                lc:v.leftChange,rc:v.rightChange,reverse:v.reverse};
      })));
    '''
    result = subprocess.run(['node','-e',code,str(script),json.dumps(payload)],
                            text=True,check=True,capture_output=True)
    for actual in json.loads(result.stdout):
        scan = analyze_slider(DEFAULT_ASSUMPTIONS, actual['key'])
        assert actual['cp'] == pytest.approx(scan.current_posterior, abs=2e-13)
        assert actual['lp'] == pytest.approx(scan.left_posterior, abs=2e-13)
        assert actual['rp'] == pytest.approx(scan.right_posterior, abs=2e-13)
        assert actual['lc'] == pytest.approx(scan.left_posterior_change, abs=2e-13)
        assert actual['rc'] == pytest.approx(scan.right_posterior_change, abs=2e-13)
        assert actual['reverse'] == scan.can_reverse
