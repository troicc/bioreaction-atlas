"""Is an activation family a region in a representation's space at all?

Retrieval can only rank a family highly if that family is a neighbourhood in the
space being searched. This compares mean pairwise similarity within each family
against mean similarity across families, in each encoder's own metric.

Run it before trusting a representation for a family. It needs no seeds, no labels
beyond family membership, and no retrieval - only the encoded pool.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.corpus import load_index  # noqa: E402
from bioreaction_atlas.encoders import pairwise_similarity  # noqa: E402

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def mean_similarity(left, right, metric):
    """Mean off-diagonal similarity within a set, or mean similarity between two."""
    if right is None:
        scores = pairwise_similarity(left, left, metric)
        n = len(left)
        return float((scores.sum() - np.trace(scores)) / (n * n - n)) if n > 1 else float('nan')
    return float(pairwise_similarity(left, right, metric).mean())


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pool', default='data/local/pools/combined_full')
    parser.add_argument('--out', default='outputs/candidate_pool/family_cohesion.json')
    args = parser.parse_args()

    report = {}
    for backend in BACKENDS:
        index, matrix = load_index(Path(args.pool) / backend)
        families = np.asarray([e['evidence'][0].get('activation_family') for e in index['entries']])
        metric = index['parameters']['metric']
        names = sorted({f for f in families if f})
        report[backend] = {'metric': metric, 'families': {}}
        for family in names:
            inside = matrix[families == family]
            outside = matrix[(families != family) & (families != None)]  # noqa: E711
            within = mean_similarity(inside, None, metric)
            across = mean_similarity(inside, outside, metric)
            report[backend]['families'][family] = {
                'members': int((families == family).sum()),
                'mean_within': round(within, 4),
                'mean_across': round(across, 4),
                # Positive means the family occupies its own neighbourhood. Near zero
                # means members are no more alike than they are like everything else,
                # and no amount of query normalisation can rank such a family.
                'separation': round(within - across, 4),
            }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    names = sorted(report['morgan']['families'])
    print(f"{'encoder':10s} " + ' '.join(f'{n[:22]:>24s}' for n in names))
    print(f"{'':10s} " + ' '.join(f'{"within/across/sep":>24s}' for _ in names))
    for backend in BACKENDS:
        cells = []
        for name in names:
            row = report[backend]['families'][name]
            cells.append(f"{row['mean_within']:.3f}/{row['mean_across']:.3f}/{row['separation']:+.3f}".rjust(24))
        print(f'{backend:10s} ' + ' '.join(cells))
    print(f'\nWrote {args.out}')
    print('Separation near zero means the representation does not encode that family as a '
          'region. Normalising a query cannot create a neighbourhood that is not there.')


if __name__ == '__main__':
    main()
