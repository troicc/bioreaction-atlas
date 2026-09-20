"""Does retrieval surface the chemically corresponding family, or routine background?

For every enzyme seed in a family, retrieve top-k from each pool with each encoder
and measure what fraction of the retrieved candidates carry that family's diagnostic
feature. This is a purity measurement of the candidate pool and the retrieval
together. It is not accuracy: a family match is not a verified precedent, and a
non-match is not proof that the candidate is useless.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.activation import family_screen  # noqa: E402
from bioreaction_atlas.corpus import load_index  # noqa: E402
from bioreaction_atlas.encoders import Encoder, pairwise_similarity  # noqa: E402

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def pool_flags(entries, family):
    """Which candidates carry the family's diagnostic feature."""
    flags = []
    for entry in entries:
        catalyst = None
        for evidence in entry['evidence']:
            catalyst = (evidence.get('context') or {}).get('catalyst')
            if catalyst:
                break
        verdict, _ = family_screen(entry['reaction_smiles'], family, catalyst)
        flags.append(bool(verdict))
    return np.asarray(flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--family', default='metal_carbene')
    parser.add_argument('--seeds', default='data/local/reference_demo')
    parser.add_argument('--pools', nargs='+', required=True, metavar='NAME=DIR')
    parser.add_argument('--seed-domain', default='enzyme_reference')
    parser.add_argument('--seed-cofactor',
                        help='select seeds by recorded cofactor (e.g. PLP) instead of by the '
                             'family structural screen. Needed when the enzyme and abiotic routes '
                             'share an intermediate but not a precursor.')
    parser.add_argument('--pool-domain', help='restrict a pool to one domain, e.g. patent_reference')
    parser.add_argument('--model-dir', default='data/local/public/rxnfp')
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--out', default='data/local/pools/family_match_rate.json')
    args = parser.parse_args()

    info, _ = load_index(Path(args.seeds) / 'morgan')
    pool = [e for e in info['entries'] if e['domain'] == args.seed_domain]
    if args.seed_cofactor:
        def chosen(entry):
            return any((ev.get('context') or {}).get('metal_cofactor') == args.seed_cofactor
                       for ev in entry['evidence'])
        seeds, how = [e for e in pool if chosen(e)], f'cofactor {args.seed_cofactor}'
    else:
        seeds = [e for e in pool if family_screen(e['reaction_smiles'], args.family)[0]]
        how = 'the family structural screen'
    if not seeds:
        raise SystemExit(f'No {args.seed_domain} seeds selected by {how}')
    print(f'{len(seeds)} enzyme seeds selected by {how}; family {args.family}\n')

    report = {'family': args.family, 'seeds': len(seeds), 'top_k': args.top_k, 'pools': {}}
    for spec in args.pools:
        name, directory = spec.split('=', 1)
        report['pools'][name] = {}
        for backend in BACKENDS:
            index, matrix = load_index(Path(directory) / backend)
            entries = index['entries']
            keep = np.asarray([e['domain'] == args.pool_domain for e in entries]) if args.pool_domain \
                else np.ones(len(entries), dtype=bool)
            if not keep.any():
                raise SystemExit(f'{name}/{backend}: no candidates in domain {args.pool_domain}')
            candidates = [e for e, k in zip(entries, keep) if k]
            flags = pool_flags(candidates, args.family)
            encoder = Encoder(backend, args.model_dir if backend == 'rxnfp' else None)
            vectors = encoder.encode([s['reaction_smiles'] for s in seeds], batch_size=32)
            scores = pairwise_similarity(vectors, matrix[keep], index['parameters']['metric'])
            # Deterministic ranking; ties broken by candidate order, as elsewhere.
            top = np.argsort(-np.round(scores, 6), axis=1, kind='stable')[:, :args.top_k]
            matched = flags[top]
            report['pools'][name][backend] = {
                'candidates': int(keep.sum()),
                'pool_family_share': round(float(flags.mean()), 4),
                'mean_family_share_at_k': round(float(matched.mean()), 4),
                'seeds_with_no_family_hit': int((~matched.any(axis=1)).sum()),
            }
            print(f"{name:14s} {backend:9s} pool {int(keep.sum()):5d} cand, "
                  f"{flags.mean():6.1%} in-family | top-{args.top_k} in-family "
                  f"{matched.mean():6.1%} | seeds with zero family hit "
                  f"{int((~matched.any(axis=1)).sum()):4d}/{len(seeds)}")
        print()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Wrote {args.out}')
    print('A family match is not a verified precedent; this measures pool composition and '
          'retrieval together, not correctness.')


if __name__ == '__main__':
    main()
