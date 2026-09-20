"""Discovery-event precedent coverage accounting under protocol v0.2.

Three observations stay independent: whether an earlier nonenzymatic literature
precedent exists, whether the frozen corpus contains a corresponding record, and
whether retrieval found it. Unresolved annotations stay in the denominator, and a
top-k miss is never promoted to a demonstrated corpus absence.

This is deliberately separate from `evaluation.py`, which implements the v1
single-cutoff ranking design. The two must not be fed into each other.
"""
from datetime import date

from .chemistry import canonical_reaction

PROTOCOL_VERSION = 'coverage-0.2'

COVERAGE_STATES = ('confirmed_present', 'confirmed_absent_under_protocol', 'unresolved')
PRECEDENT_STATES = ('confirmed_earlier', 'unresolved')
ELIGIBILITY_STATES = ('usable', 'unusable')
SEARCH_STATES = ('verified_hit', 'no_verified_hit_within_budget', 'not_completed')
COHORTS = ('calibration', 'frozen')
MATCH_LEVELS = ('transformation', 'exact_substrate')
STRATA_AXES = ('transformation', 'activation', 'platform')

# Every accepted precedent must carry each of these; a review citation or a
# database class label is a search lead, not experimental evidence.
PRECEDENT_FIELDS = ('source_id', 'experiment_locator', 'reaction_smiles', 'catalyst',
                    'nonenzymatic_evidence', 'first_public_date', 'date_evidence',
                    'corpus_record_id', 'match_rationale', 'match_level')


def iso(value, field):
    """Protocol dates are calendar-verified, never free text."""
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError(f'{field} must be a YYYY-MM-DD string')
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'{field} is not a real calendar date: {value}') from exc


def _check_precedent(event_id, n, precedent, event_date):
    where = f'{event_id} precedent {n}'
    if not isinstance(precedent, dict):
        raise ValueError(f'{where}: each precedent must be an object')
    missing = [f for f in PRECEDENT_FIELDS if not precedent.get(f)]
    if missing:
        raise ValueError(f'{where}: missing required evidence {", ".join(missing)}')
    if precedent['match_level'] not in MATCH_LEVELS:
        raise ValueError(f'{where}: match_level must be one of {MATCH_LEVELS}')
    try:
        canonical_reaction(precedent['reaction_smiles'])
    except ValueError as exc:
        raise ValueError(f'{where}: reaction_smiles does not parse: {exc}') from exc
    precedent_date = iso(precedent['first_public_date'], f'{where} first_public_date')
    # The event-specific cutoff: a precedent must predate the discovery's own
    # earliest verified disclosure, not some shared corpus-wide date.
    if event_date is None:
        raise ValueError(f'{where}: event_earliest_public_date is required before a precedent can be accepted')
    if precedent_date >= event_date:
        raise ValueError(f'{where}: precedent date {precedent_date} does not predate the event date {event_date}')


def validate_event(event):
    """Reject any annotation that would overstate what has actually been checked."""
    event_id = event.get('event_id')
    if not isinstance(event_id, str) or not event_id:
        raise ValueError('Each event needs a non-empty event_id')
    if event.get('cohort') not in COHORTS:
        raise ValueError(f'{event_id}: cohort must be one of {COHORTS}')
    for field, allowed in (('literature_precedent', PRECEDENT_STATES), ('corpus_coverage', COVERAGE_STATES),
                           ('structure_eligibility', ELIGIBILITY_STATES), ('search_outcome', SEARCH_STATES)):
        if event.get(field) not in allowed:
            raise ValueError(f'{event_id}: {field} must be one of {allowed}')
    strata = event.get('strata')
    if not isinstance(strata, dict) or set(strata) != set(STRATA_AXES):
        raise ValueError(f'{event_id}: strata must carry exactly the axes {STRATA_AXES}')
    for axis, labels in strata.items():
        if not isinstance(labels, list) or not labels or not all(isinstance(v, str) and v for v in labels):
            raise ValueError(f'{event_id}: strata.{axis} must be a non-empty list of labels')

    event_date = iso(event['event_earliest_public_date'], f'{event_id} event_earliest_public_date') \
        if event.get('event_earliest_public_date') else None

    eligibility = event['structure_eligibility']
    if eligibility == 'usable':
        if not event.get('reaction_smiles'):
            raise ValueError(f'{event_id}: structure_eligibility "usable" requires a reaction_smiles')
        try:
            canonical_reaction(event['reaction_smiles'])
        except ValueError as exc:
            raise ValueError(f'{event_id}: reaction_smiles does not parse: {exc}') from exc
        if not event.get('event_experiment_locator'):
            raise ValueError(f'{event_id}: a usable structure needs event_experiment_locator')
    elif event.get('reaction_smiles'):
        raise ValueError(f'{event_id}: reaction_smiles present but structure_eligibility is "unusable"')

    precedents = event.get('precedents') or []
    if not isinstance(precedents, list):
        raise ValueError(f'{event_id}: precedents must be a list')
    for n, precedent in enumerate(precedents, 1):
        _check_precedent(event_id, n, precedent, event_date)

    coverage = event['corpus_coverage']
    if coverage == 'confirmed_present':
        if not precedents:
            raise ValueError(f'{event_id}: "confirmed_present" requires at least one fully evidenced precedent')
        if event['literature_precedent'] != 'confirmed_earlier':
            raise ValueError(f'{event_id}: a record cannot be confirmed in the corpus while the literature '
                             'precedent is unresolved')
    if coverage == 'confirmed_absent_under_protocol':
        # A top-k miss does not qualify: the protocol demands a completed
        # corpus-level check with its own written rationale.
        if not event.get('corpus_check_procedure') or not event.get('corpus_absence_rationale'):
            raise ValueError(f'{event_id}: "confirmed_absent_under_protocol" requires both corpus_check_procedure '
                             'and corpus_absence_rationale; a top-k miss is not sufficient')
        if event['search_outcome'] == 'not_completed':
            raise ValueError(f'{event_id}: cannot declare corpus absence while the search is not completed')
        if precedents:
            raise ValueError(f'{event_id}: corpus absence contradicts the recorded precedents')
    if event['search_outcome'] == 'verified_hit' and not any(p.get('corpus_record_id') for p in precedents):
        raise ValueError(f'{event_id}: a verified hit must name the corpus record it matched')
    # A reviewer is required only once the event makes a positive claim. A wholly
    # unresolved intake row is honest without one.
    claims = (event['literature_precedent'] == 'confirmed_earlier'
              or coverage != 'unresolved'
              or event['search_outcome'] == 'verified_hit')
    if claims and not event.get('reviewers'):
        raise ValueError(f'{event_id}: a resolved decision must name who adjudicated it')
    return event


def validate_registry(registry):
    if registry.get('protocol_version') != PROTOCOL_VERSION:
        raise ValueError(f'Registry must declare protocol_version {PROTOCOL_VERSION}')
    events = registry.get('events')
    if not isinstance(events, list) or not events:
        raise ValueError('Registry needs a non-empty events list')
    seen = set()
    for event in events:
        validate_event(event)
        if event['event_id'] in seen:
            raise ValueError(f'Duplicate event_id {event["event_id"]}')
        seen.add(event['event_id'])
    # Events from one paper are not independent; the protocol clusters them.
    for event in events:
        if not event.get('paper_id'):
            raise ValueError(f'{event["event_id"]}: paper_id is required for paper-level clustering')
    return registry


def _fraction(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None


def accounting(registry, cohort='frozen'):
    """Counts and denominators first. Bounds describe unresolved annotations only."""
    validate_registry(registry)
    if cohort not in COHORTS:
        raise ValueError(f'cohort must be one of {COHORTS}')
    events = [e for e in registry['events'] if e['cohort'] == cohort]
    n = len(events)
    confirmed = [e for e in events if e['corpus_coverage'] == 'confirmed_present']
    unresolved = [e for e in events if e['corpus_coverage'] == 'unresolved']
    absent = [e for e in events if e['corpus_coverage'] == 'confirmed_absent_under_protocol']
    queryable = [e for e in confirmed if e['structure_eligibility'] == 'usable']
    strata = {axis: {} for axis in STRATA_AXES}
    for event in events:
        for axis in STRATA_AXES:
            for label in event['strata'][axis]:
                bucket = strata[axis].setdefault(label, {'events': 0, 'confirmed_present': 0})
                bucket['events'] += 1
                bucket['confirmed_present'] += event['corpus_coverage'] == 'confirmed_present'
    return {
        'protocol_version': PROTOCOL_VERSION,
        'cohort': cohort,
        'events_N': n,
        'papers': len({e['paper_id'] for e in events}),
        'confirmed_candidate_coverage_C': len(confirmed),
        'unresolved_U': len(unresolved),
        'confirmed_absent_under_protocol': len(absent),
        'coverage_fraction_C_over_N': _fraction(len(confirmed), n),
        'completion_bounds': [_fraction(len(confirmed), n), _fraction(len(confirmed) + len(unresolved), n)],
        'verified_literature_precedents_over_N': _fraction(
            sum(e['literature_precedent'] == 'confirmed_earlier' for e in events), n),
        'search_verified_hits_over_N': _fraction(sum(e['search_outcome'] == 'verified_hit' for e in events), n),
        'structurally_unqueryable': sum(e['structure_eligibility'] == 'unusable' for e in events),
        'conditional_recall_denominator': len(queryable),
        'conditional_recall_at_budget': _fraction(
            sum(e['search_outcome'] == 'verified_hit' for e in queryable), len(queryable)),
        'strata': strata,
        'interpretation': (
            'Counts describe this cohort only. Completion bounds express unresolved annotations, '
            'not a statistical confidence interval. Unreported reactions are not negative experiments, '
            'and no number here is an experimental success probability.'),
    }


def blocking_checks(event):
    """What still stands between this event and a resolved coverage decision."""
    blocked = []
    if not event.get('event_earliest_public_date'):
        blocked.append('verify the earliest public disclosure date and its evidence')
    if event['structure_eligibility'] != 'usable':
        blocked.append('extract the reaction SMILES and experiment locator from the primary source')
    if event['literature_precedent'] == 'unresolved':
        blocked.append('trace an earlier nonenzymatic experimental source')
    if event['corpus_coverage'] == 'unresolved':
        blocked.append('decide corpus inclusion against the frozen manifest')
    if event['search_outcome'] == 'not_completed':
        blocked.append('run the four-encoder union search within the frozen budget')
    if not event.get('reviewers'):
        blocked.append('record an adjudicating reviewer')
    return blocked
