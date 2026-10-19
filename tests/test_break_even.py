"""Break-even ticks show the mathematical evidence update, not slider motion."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from seed_bayes_lab.sensitivity import (
    SLIDER_SPECS, _zero_numerator, analyze_slider, break_even_regions,
    bayes_delta, search_delta,
)
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def test_bayes_interior_zero_has_expected_likelihood_ratio():
    state = dict(DEFAULT_ASSUMPTIONS)
    regions = break_even_regions(state, 'likelihood_succeeded')
    assert len(regions) == 1
    point = regions[0]
    assert point.interpolated and not point.is_interval
    # When P(B) is strictly between 0 and 1, evidence is neutral iff
    # P(E | B) equals the weighted P(E | not B).
    expected = ((1 - .5) * .8 + (.5 * (1 - .3)) * .6) / (1 - .5 * .3)
    assert point.start == pytest.approx(expected, abs=2e-12)
    assert bayes_delta({**state,'likelihood_succeeded':point.start}) == pytest.approx(0,abs=1e-13)


def test_endpoint_zero_and_search_interval():
    state = dict(DEFAULT_ASSUMPTIONS)
    at_zero = break_even_regions(state,'prior_intent')
    assert len(at_zero) == 1 and at_zero[0].start == at_zero[0].end == 0
    compute_limited = break_even_regions(state,'restricted_bits')
    assert len(compute_limited) == 1
    assert compute_limited[0].start == state['compute_bits']
    assert compute_limited[0].end == SLIDER_SPECS['restricted_bits'].maximum
    assert compute_limited[0].is_interval
    assert search_delta({**state,'restricted_bits':40}) == pytest.approx(0,abs=1e-13)


def test_saturation_is_not_a_mathematical_equality():
    state = dict(DEFAULT_ASSUMPTIONS)
    # In floating point both attack probabilities round to 1 for k=5, but
    # the true search probabilities strictly differ if N_T < N_U.
    assert search_delta({**state,'rarity_bits':5}) == 0.0
    assert _zero_numerator({**state,'rarity_bits':5}, 'search') < 0
    assert break_even_regions(state,'rarity_bits') == ()
    assert not analyze_slider(state,'rarity_bits').can_reach_equality


def test_full_range_equality_and_impossible_conditioning():
    state = {**DEFAULT_ASSUMPTIONS,'prior_intent':0.0}
    entire = break_even_regions(state,'likelihood_failed')
    spec = SLIDER_SPECS['likelihood_failed']
    assert len(entire) == 1
    assert entire[0].start == spec.minimum and entire[0].end == spec.maximum
    # P(E)=0 at the left endpoint. Undefined conditioning is never equality.
    state['likelihood_honest'] = 0.0
    assert break_even_regions(state,'likelihood_failed') == ()
    assert break_even_regions(state,'likelihood_honest')[0].start > 0


def test_self_invariant_other_dial_changes_break_even():
    base = dict(DEFAULT_ASSUMPTIONS)
    for key, spec in SLIDER_SPECS.items():
        reference = break_even_regions(base,key)
        assert reference == break_even_regions({**base,key:spec.minimum},key)
        assert reference == break_even_regions({**base,key:spec.maximum},key)
    root = break_even_regions(base,'likelihood_succeeded')[0].start
    modified = break_even_regions({**base,'likelihood_honest':0.4},'likelihood_succeeded')[0].start
    assert modified < root
    assert modified != pytest.approx(root)
    # A dial can lack an equality point entirely for the current settings.
    assert break_even_regions(base,'likelihood_honest') == ()


@pytest.mark.skipif(shutil.which('node') is None, reason='Node is optional')
def test_js_python_break_even_consistency():
    rng = random.Random(314159)
    states = [dict(DEFAULT_ASSUMPTIONS)]
    for _ in range(24):
        state = dict(DEFAULT_ASSUMPTIONS)
        for key, spec in SLIDER_SPECS.items():
            state[key] = rng.choice(spec.positions())
        states.append(state)
    specs = [{"key":sp.key,"group":sp.group,"min":sp.minimum,
              "max":sp.maximum,"step":sp.step} for sp in SLIDER_SPECS.values()]
    js = Path(__file__).resolve().parents[1] / 'src/seed_bayes_lab/offline.js'
    code = '''
      require(process.argv[1]);
      const {states,specs} = JSON.parse(process.argv[2]);
      const api=globalThis.SeedBayesOffline;
      console.log(JSON.stringify(states.map(s=> specs.map(sp=>api.breakEvens(s,sp)))));
    '''
    run = subprocess.run(['node','-e',code,str(js),json.dumps({'states':states,'specs':specs})],
                         capture_output=True,text=True,check=True)
    for state, regions_per_spec in zip(states,json.loads(run.stdout)):
        for spec, theirs in zip(SLIDER_SPECS.values(),regions_per_spec):
            ours = break_even_regions(state,spec.key)
            assert len(ours) == len(theirs), (spec.key, ours, theirs)
            for x,y in zip(ours,theirs):
                assert x.start == pytest.approx(y['start'],abs=2e-8)
                assert x.end == pytest.approx(y['end'],abs=2e-8)
                assert x.interpolated == y['interpolated']
