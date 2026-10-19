"""Definitions shown identically in both interactive interfaces."""

from pathlib import Path

from seed_bayes_lab.demo import render_html
from seed_bayes_lab.glossary import (
    BAYES_EVENTS, BAYES_PARAMETERS, BAYES_QUANTITIES,
    SEARCH_EVENTS, SEARCH_PARAMETERS, SEARCH_QUANTITIES,
    all_parameter_keys,
)
from seed_bayes_lab.sensitivity import SLIDER_SPECS
from seed_bayes_lab.ui_state import DEFAULT_ASSUMPTIONS


def test_every_slider_is_described_once():
    assert all_parameter_keys() == set(SLIDER_SPECS) == set(DEFAULT_ASSUMPTIONS)
    parameter_entries = [*BAYES_PARAMETERS, *SEARCH_PARAMETERS]
    assert len(parameter_entries) == len(SLIDER_SPECS) == 13
    assert len({e.key for e in parameter_entries}) == 13
    assert all(e.symbol and e.definition for e in parameter_entries)


def test_all_events_have_meanings_and_no_conflation():
    assert all(e.symbol and e.definition for e in
               (*BAYES_EVENTS, *SEARCH_EVENTS, *BAYES_QUANTITIES, *SEARCH_QUANTITIES))
    b = next(e for e in BAYES_EVENTS if e.symbol == 'B')
    assert 'deliberately planted' in b.definition
    assert 'accidental weakness' in b.qualification
    i = next(e for e in BAYES_EVENTS if e.symbol.startswith('I'))
    assert 'F ∪ B' in i.symbol
    e = next(e for e in BAYES_EVENTS if e.symbol == 'E')
    assert '1997' in e.definition and '1,842' in e.definition
    t = next(e for e in SEARCH_EVENTS if e.symbol == 'T')
    assert 'restricted timestamp' in t.definition
    assert 'stronger' in t.qualification
    assert any('CAN REVERSE' in e.qualification for e in
               (*BAYES_QUANTITIES, *SEARCH_QUANTITIES)) is False


def test_html_glossary_is_static_searchable_and_accessible(tmp_path: Path):
    dest = render_html(tmp_path / 'demo.html')
    html = dest.read_text(encoding='utf-8')
    assert 'id="tab-glossary"' in html
    assert 'id="panel-glossary"' in html
    assert 'role="tabpanel"' in html
    assert 'Notation and exact events' in html
    assert 'P(B | E)' in html
    assert '1997' in html
    assert 'scope="row"' in html
    assert 'Read the full observation, limitations and sources' in html
    assert 'Δendpoint' in html
