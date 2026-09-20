"""Report current coverage accounting and what still blocks each event.

Runs at any completeness. It prints denominators before fractions and never
fills an unresolved decision with a guess.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.coverage import accounting, blocking_checks, validate_registry  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', nargs='?', default='research/coverage_registry.json')
    parser.add_argument('--cohort', choices=['calibration', 'frozen'], default='calibration')
    parser.add_argument('--out', help='Also write the accounting JSON here')
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text())
    validate_registry(registry)
    report = accounting(registry, cohort=args.cohort)

    n = report['events_N']
    print(f"Protocol {report['protocol_version']} | cohort: {report['cohort']} | "
          f"N = {n} events across {report['papers']} papers\n")
    if not n:
        print('No events in this cohort.')
        return
    print(f"  confirmed candidate coverage C : {report['confirmed_candidate_coverage_C']}")
    print(f"  unresolved U                   : {report['unresolved_U']}")
    print(f"  confirmed absent under protocol: {report['confirmed_absent_under_protocol']}")
    print(f"  C/N                            : {report['coverage_fraction_C_over_N']}")
    print(f"  completion bounds C/N-(C+U)/N  : {report['completion_bounds']}")
    print(f"  verified literature precedents : {report['verified_literature_precedents_over_N']}")
    print(f"  search verified hits / N       : {report['search_verified_hits_over_N']}")
    print(f"  structurally unqueryable       : {report['structurally_unqueryable']}")
    print(f"  conditional recall denominator : {report['conditional_recall_denominator']}")

    print('\nBlocking checks per event:')
    for event in registry['events']:
        if event['cohort'] != args.cohort:
            continue
        blocked = blocking_checks(event)
        mark = 'RESOLVED' if not blocked else f'{len(blocked)} open'
        print(f"\n  {event['event_id']}  [{mark}]  {event['provisional_transformation']}")
        for item in blocked:
            print(f'    - {item}')

    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(f'\nWrote {args.out}')
    print('\nNo number above is an experimental success probability. Unreported reactions '
          'are not negative experiments.')


if __name__ == '__main__':
    main()
