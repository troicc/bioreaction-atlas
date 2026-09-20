"""Seed the coverage registry from the calibration intake, resolving nothing.

Every state stays at its intake value. This script only reshapes existing
metadata into the annotable protocol-v0.2 record; it never invents chemistry,
dates or precedents.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.coverage import PROTOCOL_VERSION, validate_registry  # noqa: E402

INTAKE = Path('research/coverage_pilot_intake.json')
REGISTRY = Path('research/coverage_registry.json')


def main():
    intake = json.loads(INTAKE.read_text())
    if intake.get('protocol_version') != PROTOCOL_VERSION:
        raise SystemExit(f'Intake declares {intake.get("protocol_version")}, expected {PROTOCOL_VERSION}')
    if REGISTRY.exists():
        raise SystemExit(f'{REGISTRY} already exists; edit it directly rather than reseeding over annotations')

    events = []
    for paper in intake['papers']:
        events.append({
            'event_id': paper['pilot_id'],
            'cohort': 'calibration',
            'paper_id': paper['paper_id'],
            'provisional_transformation': paper['provisional_transformation'],
            'source_url': paper['source_url'],
            'related_source_url': paper.get('related_source_url'),
            'reported_publication_date': paper.get('reported_publication_date'),
            'event_earliest_public_date': paper.get('event_earliest_public_date'),
            'event_date_evidence': paper.get('event_date_evidence'),
            'reaction_smiles': paper.get('reaction_smiles'),
            'event_experiment_locator': paper.get('event_experiment_locator'),
            'strata': paper['provisional_strata'],
            'literature_precedent': paper['literature_precedent'],
            'corpus_coverage': paper['corpus_coverage'],
            'structure_eligibility': paper['structure_eligibility'],
            'search_outcome': paper['search_outcome'],
            'precedents': paper['precedents'],
            'corpus_check_procedure': None,
            'corpus_absence_rationale': None,
            'reviewers': [],
            'search_minutes': None,
            'review_state': paper['review_state'],
            'notes': paper['notes'],
            'remaining_checks': paper['remaining_checks'],
        })

    registry = {
        'protocol_version': PROTOCOL_VERSION,
        'status': 'calibration_in_progress_no_frozen_cohort',
        'selection': intake['selection'],
        'seeded_from': str(INTAKE),
        'accounting_rule': (
            'Unresolved events stay in the denominator. A top-k miss is not a corpus absence. '
            'Calibration outcomes are reported separately from any later frozen cohort.'),
        'events': events,
    }
    validate_registry(registry)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n')
    print(f'Seeded {REGISTRY} with {len(events)} calibration events, all unresolved.')


if __name__ == '__main__':
    main()
