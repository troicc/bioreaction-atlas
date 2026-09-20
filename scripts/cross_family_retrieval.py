"""Does retrieval rank a seed's own activation family above another family?

Both families sit in one candidate pool. For each enzyme seed the top-k is scored
for how much of it comes from the seed's own family, against that family's share of
the pool as the no-skill reference. This asks whether a representation carries any
notion of activation mode, using labels assigned by a structural rule the encoders
have never seen.

It is not accuracy. A same-family candidate is not a verified precedent, and the
comparison is between two specific families in one fixed pool.
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
from bioreaction_atlas.intermediates import canonicalize, normalize_reactants  # noqa: E402

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def seed_sets(index_dir, cofactors, by_screen=()):
    """Select seeds per family, by cofactor or by the family's structural screen.

    Carbene seeds share the diazo precursor with the abiotic pool, so the screen picks
    exactly the carbene chemistry and excludes the nitrene and C-H amination reactions
    that also carry a haem cofactor. PLP seeds cannot be selected that way: the enzyme
    consumes serine and forms the acceptor in the active site, so cofactor is the only
    available handle.
    """
    info, _ = load_index(Path(index_dir) / 'morgan')
    enzymes = [e for e in info['entries'] if e['domain'] == 'enzyme_reference']
    sets, how = {}, {}
    for family, cofactor in cofactors.items():
        by_cofactor = [e for e in enzymes
                       if any((ev.get('context') or {}).get('metal_cofactor') == cofactor
                              for ev in e['evidence'])]
        if family in by_screen:
            sets[family] = [e for e in by_cofactor if family_screen(e['reaction_smiles'], family)[0]]
            how[family] = f'cofactor {cofactor} and the {family} structural screen'
        else:
            sets[family] = by_cofactor
            how[family] = f'cofactor {cofactor}'
    return sets, how


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pool', default='data/local/pools/combined')
    parser.add_argument('--seeds', default='data/local/reference_demo')
    parser.add_argument('--model-dir', default='data/local/public/rxnfp')
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--out', default='outputs/candidate_pool/cross_family.json')
    # Which enzyme cofactor maps to which candidate family.
    parser.add_argument('--map', nargs='+', default=['heme=metal_carbene', 'PLP=aminoacrylate_addition'])
    parser.add_argument('--normalize', action='store_true',
                        help='rewrite seed reactants into the intermediate their platform forms, '
                             'so both sides are expressed at the same level')
    parser.add_argument('--canonical', action='store_true',
                        help='also reduce the acceptor to its unprotected core on the seed side; '
                             'pair with a pool encoded the same way')
    parser.add_argument('--seed-screen', nargs='*', default=['metal_carbene'],
                        help='families whose seeds are additionally filtered by the structural screen')
    args = parser.parse_args()

    pairs = dict(m.split('=', 1) for m in args.map)
    seeds, how = seed_sets(args.seeds, {family: cofactor for cofactor, family in pairs.items()},
                           by_screen=set(args.seed_screen))
    for family, entries in seeds.items():
        print(f'{len(entries):5d} enzyme seeds for {family}  (selected by {how[family]})')
    report_how = how

    queries, normalized = {}, {}
    for family, entries in seeds.items():
        texts, hits = [], 0
        for entry in entries:
            smiles = entry['reaction_smiles']
            if args.normalize:
                smiles, rule = normalize_reactants(smiles, family)
                hits += bool(rule)
            if args.canonical:
                smiles, _ = canonicalize(smiles, family)
            texts.append(smiles)
        queries[family] = texts
        normalized[family] = hits
    if args.normalize:
        for family, hits in normalized.items():
            print(f'  normalized {hits}/{len(seeds[family])} {family} seeds to their intermediate')

    report = {'top_k': args.top_k, 'seed_counts': {f: len(e) for f, e in seeds.items()},
              'seed_selection': report_how, 'normalized': args.normalize,
              'seeds_normalized': normalized, 'backends': {}}
    for backend in BACKENDS:
        index, matrix = load_index(Path(args.pool) / backend)
        families = np.asarray([e['evidence'][0].get('activation_family') for e in index['entries']])
        shares = {f: float((families == f).mean()) for f in seeds}
        report['pool_share'] = shares
        encoder = Encoder(backend, args.model_dir if backend == 'rxnfp' else None)
        report['backends'][backend] = {}
        for family, entries in seeds.items():
            if not entries:
                continue
            vectors = encoder.encode(queries[family], batch_size=32)
            scores = pairwise_similarity(vectors, matrix, index['parameters']['metric'])
            top = np.argsort(-np.round(scores, 6), axis=1, kind='stable')[:, :args.top_k]
            own = (families[top] == family)
            report['backends'][backend][family] = {
                'pool_share': round(shares[family], 4),
                'mean_own_family_share_at_k': round(float(own.mean()), 4),
                'seeds_with_no_own_family_hit': int((~own.any(axis=1)).sum()),
                'lift_over_pool_share': round(float(own.mean()) / shares[family], 2) if shares[family] else None,
            }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    print(f"\npool composition: " + ', '.join(f'{f} {s:.1%}' for f, s in report['pool_share'].items()))
    print(f"\n{'backend':10s} {'seed family':26s} {'own-family @k':>13s} {'lift':>6s} {'zero-hit seeds':>15s}")
    for backend, families in report['backends'].items():
        for family, row in families.items():
            print(f"{backend:10s} {family:26s} {row['mean_own_family_share_at_k']:12.1%} "
                  f"{row['lift_over_pool_share']:6.2f} {row['seeds_with_no_own_family_hit']:15d}")
    print(f'\nWrote {args.out}')
    print('A same-family candidate is not a verified precedent. Lift is measured against '
          'this pool\'s composition, not against chance in any wider sense.')


if __name__ == '__main__':
    main()
