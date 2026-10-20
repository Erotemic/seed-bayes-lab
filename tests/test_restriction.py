"""Test alternative effective-restriction model assumptions and update signs."""
from __future__ import annotations

import pytest

from seed_bayes_lab.restriction import restriction_update, restriction_support_warning
from seed_bayes_lab.sensitivity import analyze_slider, break_even_regions, direction
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def test_neutral_default_and_direction():
    p = DEFAULT_ASSUMPTIONS
    result = restriction_update(p['restriction_intent'],p['restriction_baseline_success'],
                                p['restriction_before'],p['restriction_after'],p['restriction_ratio'])
    assert result.before == pytest.approx(result.after)
    assert result.delta == 0
    assert result.multiplier == pytest.approx(1)
    assert direction(result.delta) == 'unchanged'


def test_effective_restriction_increases_confidence_when_assumed_effective():
    res = restriction_update(.5,.3,.2,.8,.5)
    assert res.before == pytest.approx(.135)
    assert res.after == pytest.approx(.09)
    assert res.delta == pytest.approx(-.045)
    assert res.multiplier == pytest.approx(2/3)
    assert restriction_update(.5,.3,.8,.2,.5).delta == pytest.approx(+.045)
    assert restriction_update(1,.3,.2,.8,.5).delta < 0  # 100% intent


def test_break_even_factors_and_zero_prior_ratio():
    for p,s,t0,t1,r in [(.5,.3,.2,.8,1), (0,.3,.2,.8,.5),
                        (.5,0,.2,.8,.5), (.5,.3,.8,.8,.5)]:
        assert restriction_update(p,s,t0,t1,r).delta == 0
    assert restriction_update(0,.3,.2,.8,.5).multiplier is None
    assert restriction_update(.5,.3,1,1,0).multiplier is None
    for bad in (-0.01,1.01,float('nan'),float('inf')):
        with pytest.raises(ValueError):
            restriction_update(.5,.3,.2,.8,bad)


def test_restriction_slider_endpoint_semantics_and_break_even_ticks():
    state=dict(DEFAULT_ASSUMPTIONS)
    scan=analyze_slider(state,'restriction_after')
    assert direction(scan.left_delta)=='increase'
    assert direction(scan.right_delta)=='decrease'
    assert len(scan.break_evens)==1
    assert scan.break_evens[0].start == pytest.approx(.5)
    for x in (0,.3,.8,1):
        alt=analyze_slider({**state,'restriction_after':x},'restriction_after')
        assert alt.left_delta == scan.left_delta
        assert alt.right_delta == scan.right_delta
        assert alt.break_evens == scan.break_evens
    assert (analyze_slider({**state,'restriction_before':.2},'restriction_after')
            .break_evens[0].start == pytest.approx(.2))
    assert break_even_regions({**state,'restriction_ratio':1},'restriction_after')[0].is_interval


def test_monotonicity_away_from_degeneracies():
    for p in (0,.1,.5,1):
        for s in (0,.4,1):
            for r in (0,.25,1):
                for t0,t1 in ((0,1),(.1,.9),(.5,.5)):
                    assert restriction_update(p,s,t0,t1,r).delta <= 0


def test_impossible_conditional_boundary_is_explicitly_flagged():
    assert restriction_support_warning(.5, 0, .5)
    assert restriction_support_warning(.5, 1, .5)
    assert restriction_support_warning(0, .5, .5)
    assert restriction_support_warning(.5, 0, 0) is None
    assert restriction_support_warning(.5, 1, 1) is None
    assert restriction_support_warning(.5, .2, .8) is None
