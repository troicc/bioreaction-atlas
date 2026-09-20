"""Build the four-encoder union worksheet for one coverage event.

The protocol's pilot search budget inspects the union of each encoder's top-20
against the frozen corpus. This script produces exactly that candidate set with
structures and provenance, plus blank adjudication fields. It decides nothing:
every match verdict is left for the reviewer, and no candidate is scored for
"feasibility".

Output lands under data/local/, because the candidate rows carry source-derived
patent structures and identifiers.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.cards import draw_reaction, markdown  # noqa: E402
from bioreaction_atlas.corpus import find_neighbors, load_index  # noqa: E402
from bioreaction_atlas.coverage import PRECEDENT_FIELDS, validate_registry  # noqa: E402

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('event_id')
    parser.add_argument('--registry', default='research/coverage_registry.json')
    parser.add_argument('--indices', default='data/local/reference_demo')
    parser.add_argument('--model-dir', default='data/local/public/rxnfp')
    parser.add_argument('--domain', default='patent_reference')
    parser.add_argument('--top-k', type=int, default=20)
    parser.add_argument('--out', default='data/local/coverage')
    args = parser.parse_args()

    registry = json.loads(Path(args.registry).read_text())
    validate_registry(registry)
    events = {e['event_id']: e for e in registry['events']}
    if args.event_id not in events:
        raise SystemExit(f'Unknown event {args.event_id}; have {", ".join(sorted(events))}')
    event = events[args.event_id]
    if event['structure_eligibility'] != 'usable' or not event.get('reaction_smiles'):
        raise SystemExit(
            f"{args.event_id} has no usable reaction_smiles yet. Extract the transformation and its experiment "
            f"locator from the primary source first, set structure_eligibility to 'usable', then rerun.\n"
            f"Blocking: {event.get('review_state')}")

    corpora = set()
    per_backend, ranks = {}, defaultdict(dict)
    for backend in BACKENDS:
        index_dir = Path(args.indices) / backend
        info, _ = load_index(index_dir)
        corpora.add(info['corpus_sha256'])
        result = find_neighbors(index_dir, event['reaction_smiles'], top_k=args.top_k,
                                model_dir=args.model_dir, domain=args.domain)
        per_backend[backend] = result
        for position, hit in enumerate(result['hits'], 1):
            ranks[hit['record_id']][backend] = (position, hit['similarity'])
        print(f'{backend}: {len(result["hits"])} of {result["eligible"]} eligible candidates', flush=True)
    if len(corpora) != 1:
        raise SystemExit('Encoders were built on different corpora; the union would not be a shared candidate set')

    records = {h['record_id']: h for r in per_backend.values() for h in r['hits']}
    # Order by how many encoders surfaced the record, then best rank: a reviewer's
    # reading order, not a ranking of chemical relevance.
    union = sorted(records, key=lambda k: (-len(ranks[k]), min(p for p, _ in ranks[k].values()), k))

    folder = Path(args.out) / args.event_id
    (folder / 'structures').mkdir(parents=True, exist_ok=True)
    draw_reaction(per_backend['morgan']['query'], folder / 'structures' / 'query.svg')

    lines = [f"# Coverage worksheet: {args.event_id}", '',
             f"**{event['provisional_transformation']}** · paper `{event['paper_id']}` · "
             f"event date: {event['event_earliest_public_date'] or 'NOT YET VERIFIED'}", '',
             'Union of each encoder\'s top-%d against the frozen `%s` pool (corpus `%s`).' % (
                 args.top_k, args.domain, sorted(corpora)[0][:12]), '',
             'Retrieval order is not chemical relevance. A high similarity score is not a verified '
             'correspondence, and a candidate absent here is **not** a demonstrated corpus absence: '
             'that decision needs the protocol\'s separate corpus-level check.', '',
             '![Event reaction](structures/query.svg)', '',
             f'## Candidate union ({len(union)} records)', '',
             '| # | Record | Encoders | Best rank | Similarity range | Class label | Source |',
             '|---:|---|---|---:|---|---|---|']
    for n, record_id in enumerate(union, 1):
        hit = records[record_id]
        found = ranks[record_id]
        sims = [s for _, s in found.values()]
        best = min(p for p, _ in found.values())
        lines.append(
            f"| {n} | `{record_id}` | {'/'.join(sorted(found))} ({len(found)}/4) | {best} | "
            f"{min(sims):.3f}-{max(sims):.3f} | {markdown(hit.get('label'))} | "
            f"{markdown(hit['evidence'][0]['source'])} |")

    lines += ['', '## Adjudication', '',
              'Fill one block per **accepted** precedent, then copy it into the event\'s `precedents` list in '
              'the registry. Leave the block out entirely if nothing qualifies; an empty list keeps the event '
              'unresolved, which is the honest default.', '',
              '```json', json.dumps({f: '' for f in PRECEDENT_FIELDS}, indent=2), '```', '',
              f'`match_level` is `transformation` (primary) or `exact_substrate` (stricter secondary). '
              f'`first_public_date` must strictly predate {event["event_earliest_public_date"] or "the event date"}.', '',
              '## Per-candidate structures', '']
    for n, record_id in enumerate(union, 1):
        hit = records[record_id]
        diagram = f'structures/cand_{n:02d}.svg'
        draw_reaction(hit['reaction_smiles'], folder / diagram)
        found = ranks[record_id]
        lines += [f'### {n}. `{record_id}`', '',
                  f'![Candidate]({diagram})', '',
                  f"Retrieved by: {', '.join(f'{b} (rank {p}, sim {s:.3f})' for b, (p, s) in sorted(found.items()))}", '',
                  f"Class label: {markdown(hit.get('label'))}. Source: {markdown(hit['evidence'][0]['source'])}. "
                  f"Locator: {markdown(hit['evidence'][0]['source_locator'])}.", '',
                  '- [ ] transformation corresponds (reaction-centre bond changes and reaction mode)',
                  '- [ ] demonstrably nonenzymatic',
                  '- [ ] earliest public date verified and earlier than the event',
                  '- [ ] primary experiment locator captured from the original procedure', '']

    (folder / 'worksheet.md').write_text('\n'.join(lines) + '\n')
    (folder / 'candidates.json').write_text(json.dumps(
        {'event_id': args.event_id, 'domain': args.domain, 'top_k': args.top_k,
         'corpus_sha256': sorted(corpora)[0],
         'parameters': {b: r['parameters'] for b, r in per_backend.items()},
         'eligible_candidates': {b: r['eligible'] for b, r in per_backend.items()},
         'union': [{'record_id': r, 'retrieved_by': {b: {'rank': p, 'similarity': s}
                                                     for b, (p, s) in ranks[r].items()},
                    'reaction_smiles': records[r]['reaction_smiles'],
                    'label': records[r].get('label'),
                    'evidence': records[r]['evidence']} for r in union]},
        ensure_ascii=False, indent=2) + '\n')
    print(f'\nUnion: {len(union)} unique candidates from {4 * args.top_k} retrieved slots.')
    print(f'Worksheet: {folder / "worksheet.md"}')


if __name__ == '__main__':
    main()
