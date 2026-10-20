"""Exact cases proved by Lean and evaluated by the production UI engines.

`SeedBayes/Fixtures.lean` proves all expected rational outputs with norm_num.
The source-sync test checks that it matches this fixture set. Once `lake
build` passes, these regression expectations have both a Lean proof and a
Python/JS runtime comparison. Tests never infer historical probabilities.
"""

from __future__ import annotations

import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import magnet_theory as theory

from seed_bayes_lab.model import Likelihoods, Prior, update
from seed_bayes_lab.restriction import restriction_update
from seed_bayes_lab.search import independent_search_success, method_observation_update
from seed_bayes_lab.sensitivity import _zero_numerator

ROOT = Path(__file__).resolve().parents[1]


def _load_fixture_generator():
    spec = importlib.util.spec_from_file_location(
        'generate_formal_fixtures', ROOT / 'scripts/generate_formal_fixtures.py'
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _cases():
    return _load_fixture_generator().compute_cases()


def _close(actual, exact):
    assert actual is not None
    assert actual == pytest.approx(float(Fraction(exact)), abs=1e-13)


def test_fixture_proofs_are_synchronized():
    generator = _load_fixture_generator()
    assert generator.OUTPUT.read_text() == generator.render(), (
        'SeedBayes/Fixtures.lean is stale; run '
        'python scripts/generate_formal_fixtures.py'
    )


@theory.tests(
    "SeedBayes.Bayes.UpdateDelta",
    note="Exact Lean fixture values compared against production Python floats",
)
def test_lean_proved_bayesian_cases_against_python():
    for c in _cases()['bayes']:
        i, s, lh, lf, lb = (float(Fraction(c[x])) for x in
                              ('intent', 'success', 'lh', 'lf', 'lb'))
        res = update(Prior.from_intent_success(i, s), Likelihoods(lh, lf, lb))
        expected = c['expected']
        for actual, field in (
            (res.evidence_probability, 'evidence'),
            (res.prior_backdoor, 'before'),
            (res.posterior_backdoor, 'after'),
            (res.posterior_intent, 'intent_after'),
            (res.delta_backdoor, 'delta'),
        ):
            _close(actual, expected[field])
        state = {
            'prior_intent': i, 'success_given_intent': s,
            'likelihood_honest': lh, 'likelihood_failed': lf,
            'likelihood_succeeded': lb,
        }
        _close(_zero_numerator(state, 'bayes'), expected['numerator'])


@theory.tests(
    "SeedBayes.Publication.Delta",
    note="Rational proof fixtures compared with publication-conditioned Python output",
)
def test_lean_proved_publication_cases_against_python():
    for c in _cases()['publication']:
        a, st, su, rho = (float(Fraction(c[x])) for x in
                          ('alpha', 'st', 'su', 'rho'))
        res = method_observation_update(a, st, su, rho)
        expected = c['expected']
        for actual, field in (
            (res.probability_published, 'published'),
            (res.before, 'before'),
            (res.after, 'after'),
            (res.delta, 'delta'),
        ):
            _close(actual, expected[field])
        _close(rho * (1 - a) * (st - su), expected['numerator'])


@theory.tests(
    "SeedBayes.Search.Independent",
    note="Natural trial count instances proved in Lean, then evaluated in Python",
)
def test_lean_proved_independent_search_cases_against_python():
    for c in _cases()['search']:
        actual = independent_search_success(c['k'], min(c['freedom'], c['budget']))
        _close(actual, c['expected']['success'])


@theory.tests(
    "SeedBayes.Restriction.Posterior",
    note="Bayes-derived restricted-method posterior tested against exact rational examples",
)
@theory.tests(
    "SeedBayes.Restriction.Delta",
    note="Exact rational Lean fixtures compared with production restriction model",
)
def test_lean_proved_effective_restriction_cases_against_python():
    for c in _cases()['restriction']:
        p, t, et, eu, su, st = (float(Fraction(c[x])) for x in
                             ('p', 't', 'et', 'eu', 'su', 'st'))
        result = restriction_update(p, t, et, eu, su, st)
        expected = c['expected']
        for actual, field in (
            (result.evidence_mass, 'evidence'),
            (result.belief_after, 'belief_after'),
            (result.before, 'before'),
            (result.after, 'after'),
            (result.delta, 'delta'),
        ):
            _close(actual, expected[field])
        state = {'restriction_intent':p,'restriction_before':t,
                 'restriction_evidence_t':et,'restriction_evidence_u':eu,
                 'restriction_success_u':su,'restriction_success_t':st}
        _close(_zero_numerator(state,'restriction'),expected['numerator'])
        if expected['multiplier'] is None:
            assert result.multiplier is None
        else:
            _close(result.multiplier, expected['multiplier'])


@pytest.mark.skipif(shutil.which('node') is None, reason='Node is optional')
@theory.tests(
    "SeedBayes.Bayes.Posterior",
    note="Offline browser kernel compared against exact Lean fixtures",
)
@theory.tests(
    "SeedBayes.Publication.Delta",
    note="Offline publication kernel compared against exact Lean fixtures",
)
@theory.tests(
    "SeedBayes.Search.Independent",
    note="Offline search kernel compared against exact Lean fixtures",
)
@theory.tests(
    "SeedBayes.Restriction.Delta",
    note="Offline restriction kernel compared against exact Lean fixtures",
)
def test_lean_proved_cases_against_offline_javascript():
    cases = _cases()
    js = ROOT / 'src/seed_bayes_lab/offline.js'
    # The JS functions called here are the SAME kernels used by the HTML UI,
    # not independent reimplementations written for the test.
    runner = r'''
      require(process.argv[1]);
      const all = JSON.parse(process.argv[2]);
      const api = globalThis.SeedBayesOffline;
      function num(v) { return Number(v.includes('/') ?
        v.split('/')[0] / v.split('/')[1] : v); }
      const bayes = all.bayes.map(c => api.finiteBayes({
        prior_intent:num(c.intent), success_given_intent:num(c.success),
        likelihood_honest:num(c.lh), likelihood_failed:num(c.lf),
        likelihood_succeeded:num(c.lb)
      }));
      const publication = all.publication.map(c =>
        api.publishedMethodUpdate(num(c.alpha), num(c.st), num(c.su), num(c.rho)));
      const search = all.search.map(c =>
        api.independentSearch(c.k, c.freedom, c.budget));
      const restriction = all.restriction.map(c => api.restrictionUpdate({
        restriction_intent:num(c.p), restriction_before:num(c.t),
        restriction_evidence_t:num(c.et), restriction_evidence_u:num(c.eu),
        restriction_success_u:num(c.su), restriction_success_t:num(c.st)
      }));
      console.log(JSON.stringify({bayes, publication, search, restriction}));
    '''
    payload = {k: [{kk: vv for kk, vv in c.items() if kk != 'expected'}
                    for c in cases[k]] for k in cases}
    proc = subprocess.run(
        ['node', '-e', runner, str(js), json.dumps(payload)],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    output = json.loads(proc.stdout)
    for c, result in zip(cases['bayes'], output['bayes'], strict=True):
        for field, js_key in [
            ('evidence', 'evidence'), ('before', 'before'),
            ('after', 'after'), ('intent_after', 'intentAfter'),
            ('delta', 'delta')
        ]:
            _close(result[js_key], c['expected'][field])
    for c, result in zip(cases['publication'], output['publication'], strict=True):
        for field in ('before', 'after', 'delta'):
            _close(result[field], c['expected'][field])
    for c, result in zip(cases['search'], output['search'], strict=True):
        _close(result, c['expected']['success'])

    for c, result in zip(cases['restriction'], output['restriction'], strict=True):
        for field, key in (
            ('evidence', 'evidence'), ('belief_after', 'beliefAfter'),
            ('before', 'before'), ('after', 'after'), ('delta', 'delta'),
        ):
            _close(result[key], c['expected'][field])
        if c['expected']['multiplier'] is None:
            assert result['multiplier'] is None
        else:
            _close(result['multiplier'], c['expected']['multiplier'])
