"""Bayes-derived effective-restriction update and its UI semantics."""
from __future__ import annotations

import pytest

from seed_bayes_lab.restriction import (
    restriction_update, restriction_support_warning, restriction_delta_numerator,
)
from seed_bayes_lab.sensitivity import analyze_slider, break_even_regions, direction
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def model(state):
    return restriction_update(
        state['restriction_intent'], state['restriction_before'],
        state['restriction_evidence_t'], state['restriction_evidence_u'],
        state['restriction_success_u'], state['restriction_success_t'],
    )


def test_neutral_default_and_derived_belief():
    result = model(DEFAULT_ASSUMPTIONS)
    assert result.before == pytest.approx(.15)
    assert result.after == pytest.approx(result.before)
    assert result.belief_after == pytest.approx(.5)
    assert result.delta == 0
    assert result.multiplier == pytest.approx(1)
    assert direction(result.delta) == 'unchanged'


def test_real_bayesian_evidence_update_and_both_directions():
    # p=1/2, t=1/5, eT=4/5, eU=1/5 => P(T|I,E)=1/2.
    res = restriction_update(.5, .2, .8, .2, .3, .15)
    assert res.evidence_mass == pytest.approx(.32)
    assert res.belief_after == pytest.approx(.5)
    assert res.before == pytest.approx(.135)
    assert res.after == pytest.approx(.1125)
    assert res.delta == pytest.approx(-.0225)
    assert res.multiplier == pytest.approx(5/6)
    # Both ways of reversing the hypothesis reverse the evidence update.
    assert restriction_update(.5,.2,.2,.8,.3,.15).delta > 0
    assert restriction_update(.5,.2,.8,.2,.15,.3).delta > 0
    assert restriction_update(1,.2,.8,.2,.3,.15).delta < 0


def test_derived_posterior_obeys_bayesian_boundaries():
    assert restriction_update(.5,0,.8,.2,.3,.15).belief_after == 0
    assert restriction_update(.5,1,.8,.2,.3,.15).belief_after == 1
    assert restriction_update(.5,.2,0,.8,.3,.15).belief_after == 0
    assert restriction_update(.5,.2,.8,0,.3,.15).belief_after == 1
    assert restriction_update(.5,.2,0,0,.3,.15).after is None
    assert restriction_update(.5,.2,0,0,.3,.15).delta is None
    assert restriction_delta_numerator(.5,.2,0,0,.3,.15) is None
    for value in (-0.01,1.01,float('nan'),float('inf')):
        with pytest.raises(ValueError):
            restriction_update(.5,.2,.8,.2,.3,value)


def test_break_even_factors():
    for params in [
        (0,.2,.8,.2,.3,.15),
        (.5,0,.8,.2,.3,.15),
        (.5,1,.8,.2,.3,.15),
        (.5,.2,.5,.5,.3,.15),
        (.5,.2,.8,.2,.3,.3),
    ]:
        assert restriction_update(*params).delta == pytest.approx(0,abs=1e-16)
    assert restriction_update(0,.2,.8,.2,.3,.15).multiplier is None
    assert restriction_update(.5,.2,0,0,.3,.15).multiplier is None


def test_endpoint_invariance_and_bayes_break_even_tick():
    state=dict(DEFAULT_ASSUMPTIONS)
    scan=analyze_slider(state,'restriction_evidence_t')
    assert direction(scan.left_delta)=='increase'
    assert direction(scan.right_delta)=='decrease'
    assert len(scan.break_evens)==1
    assert scan.break_evens[0].start == pytest.approx(.5)
    for x in (0,.3,.8,1):
        alt=analyze_slider({**state,'restriction_evidence_t':x},'restriction_evidence_t')
        assert alt.left_delta == scan.left_delta
        assert alt.right_delta == scan.right_delta
        assert alt.break_evens == scan.break_evens
    shifted=analyze_slider({**state,'restriction_evidence_u':.2},'restriction_evidence_t')
    assert shifted.break_evens[0].start == pytest.approx(.2)
    assert break_even_regions({**state,'restriction_success_t':.4},
                              'restriction_evidence_t')[0].is_interval


def test_nonincrease_theorem_empirical_sweep():
    for p in (0,.1,.5,1):
        for t in (0,.1,.5,1):
            for et,eu in ((.5,.5),(.8,.2),(1,0)):
                for st,su in ((0,.4),(.25,.8),(.5,.5)):
                    res=restriction_update(p,t,et,eu,su,st)
                    if res.evidence_mass == 0:
                        assert res.delta is None
                    else:
                        assert res.delta is not None and res.delta <= 1e-15


def test_conditional_intent_assumption_and_warning():
    assert restriction_support_warning(0,.5,.5,.5)
    assert restriction_support_warning(.5,.5,0,0)
    assert restriction_support_warning(.5,0,.8,.2) is None
    assert restriction_support_warning(.5,1,.8,.2) is None
