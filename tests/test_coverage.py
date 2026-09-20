from copy import deepcopy
import json
from pathlib import Path

import pytest

from bioreaction_atlas.coverage import (
    PRECEDENT_FIELDS, accounting, blocking_checks, validate_event, validate_registry,
)

PRECEDENT = {f: 'recorded' for f in PRECEDENT_FIELDS} | {
    'reaction_smiles': 'CCBr.NCC>>CCNCC',
    'first_public_date': '2010-05-04',
    'match_level': 'transformation',
}

EVENT = {
    'event_id': 'E1', 'cohort': 'calibration', 'paper_id': '10.0000/a',
    'provisional_transformation': 'test',
    'event_earliest_public_date': '2016-11-25',
    'reaction_smiles': 'CCBr.NCC>>CCNCC',
    'event_experiment_locator': 'Scheme 2, compound 4b, SI page 12',
    'strata': {'transformation': ['carbene_transfer'], 'activation': ['thermal'], 'platform': ['heme_protein']},
    'literature_precedent': 'unresolved', 'corpus_coverage': 'unresolved',
    'structure_eligibility': 'usable', 'search_outcome': 'not_completed',
    'precedents': [], 'reviewers': [],
}


def event(**overrides):
    return deepcopy(EVENT) | overrides


def registry(*events):
    return {'protocol_version': 'coverage-0.2', 'events': [deepcopy(e) for e in events]}


def test_wholly_unresolved_event_needs_no_reviewer():
    validate_event(event())


def test_confirmed_present_requires_evidenced_precedents():
    with pytest.raises(ValueError, match='at least one fully evidenced precedent'):
        validate_event(event(corpus_coverage='confirmed_present',
                             literature_precedent='confirmed_earlier', reviewers=['AB']))


def test_corpus_presence_cannot_outrun_the_literature_check():
    with pytest.raises(ValueError, match='literature precedent is unresolved'):
        validate_event(event(corpus_coverage='confirmed_present', precedents=[PRECEDENT], reviewers=['AB']))


def test_precedent_must_predate_the_event():
    late = PRECEDENT | {'first_public_date': '2016-11-25'}
    with pytest.raises(ValueError, match='does not predate the event date'):
        validate_event(event(corpus_coverage='confirmed_present', literature_precedent='confirmed_earlier',
                             precedents=[late], reviewers=['AB']))


def test_precedent_requires_every_evidence_field():
    for field in PRECEDENT_FIELDS:
        stripped = {k: v for k, v in PRECEDENT.items() if k != field}
        with pytest.raises(ValueError, match='missing required evidence'):
            validate_event(event(corpus_coverage='confirmed_present', literature_precedent='confirmed_earlier',
                                 precedents=[stripped], reviewers=['AB']))


def test_precedent_needs_a_verified_event_date_first():
    with pytest.raises(ValueError, match='event_earliest_public_date is required'):
        validate_event(event(event_earliest_public_date=None, corpus_coverage='confirmed_present',
                             literature_precedent='confirmed_earlier', precedents=[PRECEDENT], reviewers=['AB']))


def test_topk_miss_alone_cannot_become_a_corpus_absence():
    with pytest.raises(ValueError, match='a top-k miss is not sufficient'):
        validate_event(event(corpus_coverage='confirmed_absent_under_protocol',
                             search_outcome='no_verified_hit_within_budget', reviewers=['AB']))


def test_absence_cannot_be_declared_before_the_search_completes():
    with pytest.raises(ValueError, match='search is not completed'):
        validate_event(event(corpus_coverage='confirmed_absent_under_protocol',
                             corpus_check_procedure='documented', corpus_absence_rationale='documented',
                             search_outcome='not_completed', reviewers=['AB']))


def test_verified_hit_must_name_the_matched_corpus_record():
    with pytest.raises(ValueError, match='must name the corpus record'):
        validate_event(event(search_outcome='verified_hit', reviewers=['AB']))


def test_resolved_decision_requires_a_reviewer():
    with pytest.raises(ValueError, match='must name who adjudicated'):
        validate_event(event(corpus_coverage='confirmed_present', literature_precedent='confirmed_earlier',
                             precedents=[PRECEDENT]))


def test_structure_states_and_smiles_stay_consistent():
    with pytest.raises(ValueError, match='requires a reaction_smiles'):
        validate_event(event(structure_eligibility='usable', reaction_smiles=None))
    with pytest.raises(ValueError, match='structure_eligibility is "unusable"'):
        validate_event(event(structure_eligibility='unusable'))


def test_unparseable_structures_are_rejected():
    with pytest.raises(ValueError, match='does not parse'):
        validate_event(event(reaction_smiles='not a reaction'))


def test_strata_axes_are_mandatory_and_nonempty():
    with pytest.raises(ValueError, match='exactly the axes'):
        validate_event(event(strata={'transformation': ['x']}))
    with pytest.raises(ValueError, match='non-empty list'):
        validate_event(event(strata={'transformation': [], 'activation': ['a'], 'platform': ['p']}))


def test_duplicate_event_ids_are_rejected():
    with pytest.raises(ValueError, match='Duplicate event_id'):
        validate_registry(registry(event(), event()))


def test_unresolved_events_stay_in_the_denominator():
    report = accounting(registry(event(), event(event_id='E2', paper_id='10.0000/b')), cohort='calibration')
    assert report['events_N'] == 2 and report['unresolved_U'] == 2
    assert report['coverage_fraction_C_over_N'] == 0.0
    # The upper bound admits that every unresolved event could still turn out covered.
    assert report['completion_bounds'] == [0.0, 1.0]
    assert report['conditional_recall_denominator'] == 0
    assert report['conditional_recall_at_budget'] is None


def test_accounting_counts_a_resolved_event():
    covered = event(event_id='E2', paper_id='10.0000/b', corpus_coverage='confirmed_present',
                    literature_precedent='confirmed_earlier', search_outcome='verified_hit',
                    precedents=[PRECEDENT], reviewers=['AB'])
    report = accounting(registry(event(), covered), cohort='calibration')
    assert report['events_N'] == 2 and report['papers'] == 2
    assert report['confirmed_candidate_coverage_C'] == 1 and report['unresolved_U'] == 1
    assert report['coverage_fraction_C_over_N'] == 0.5
    assert report['completion_bounds'] == [0.5, 1.0]
    assert report['conditional_recall_denominator'] == 1
    assert report['conditional_recall_at_budget'] == 1.0
    assert report['strata']['platform']['heme_protein'] == {'events': 2, 'confirmed_present': 1}


def test_cohorts_are_accounted_separately():
    frozen = event(event_id='E2', paper_id='10.0000/b', cohort='frozen')
    assert accounting(registry(event(), frozen), cohort='calibration')['events_N'] == 1
    assert accounting(registry(event(), frozen), cohort='frozen')['events_N'] == 1


def test_blocking_checks_list_open_work():
    assert 'trace an earlier nonenzymatic experimental source' in blocking_checks(event())
    resolved = event(corpus_coverage='confirmed_present', literature_precedent='confirmed_earlier',
                     search_outcome='verified_hit', precedents=[PRECEDENT], reviewers=['AB'])
    assert blocking_checks(resolved) == []


def test_seeded_registry_validates_and_claims_no_coverage():
    data = json.loads(Path('research/coverage_registry.json').read_text())
    validate_registry(data)
    report = accounting(data, cohort='calibration')
    assert report['events_N'] == 5
    assert report['confirmed_candidate_coverage_C'] == 0
    assert report['unresolved_U'] == 5
    assert report['structurally_unqueryable'] == 5
