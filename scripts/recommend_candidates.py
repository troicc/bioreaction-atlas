"""Rank non-enzymatic reactions worth attempting on a given enzyme platform.

Given a set of enzyme seeds that define a platform's current chemistry, rank the
candidate pool for reactions that are close to that chemistry but that the platform
has not already performed. Output is an evidence card per candidate.

Three deliberate refusals:
  - No feasibility score. Candidates are ranked by structural proximity in a space
    that was measured to work for this family, and the evidence is shown. Multiplying
    hand-chosen factors into a "probability" would invent precision that does not exist.
  - No single encoder's word. All four ranks are shown, because disagreement between
    them is information about how firm a candidate is.
  - Nothing already done. A candidate whose transformation the platform's own seeds
    already cover is dropped, with the seed that covers it named.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.activation import family_screen  # noqa: E402
from bioreaction_atlas.cards import draw_reaction, markdown  # noqa: E402
from bioreaction_atlas.corpus import load_index  # noqa: E402
from bioreaction_atlas.encoders import Encoder, pairwise_similarity  # noqa: E402
from bioreaction_atlas.intermediates import canonicalize, normalize_reactants  # noqa: E402

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def prepare(smiles, family, normalize, canonical):
    if normalize:
        smiles, _ = normalize_reactants(smiles, family)
    if canonical:
        smiles, _ = canonicalize(smiles, family)
    return smiles


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--family', required=True)
    parser.add_argument('--cofactor', required=True, help='enzyme cofactor that defines the platform')
    parser.add_argument('--pool', default='data/local/pools/combined_canonical')
    parser.add_argument('--seeds', default='data/local/reference_demo')
    parser.add_argument('--model-dir', default='data/local/public/rxnfp')
    parser.add_argument('--rank-by', default='fused',
                        choices=list(BACKENDS) + ['fused'],
                        help='"fused" combines --fuse encoders by reciprocal rank fusion')
    parser.add_argument('--fuse', nargs='+', default=['morgan', 'substrate', 'drfp'],
                        help='encoders to fuse. RXNFP is excluded by default because it was '
                             'measured at 0.53x the pool composition on this family while the '
                             'other three reach 3.58x-4.30x; see outputs/candidate_pool/CROSS_FAMILY.md')
    parser.add_argument('--rrf-k', type=int, default=60, help='reciprocal rank fusion constant')
    parser.add_argument('--firm-percentile', type=float, default=10.0,
                        help='a candidate is firm when every fused encoder ranks it within this '
                             'top percentile of the pool')
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--max-per-paper', type=int, default=1)
    parser.add_argument('--already-done', type=float, default=0.95,
                        help='drop a candidate this similar to one of the platform\'s own reactions')
    parser.add_argument('--no-normalize', action='store_true')
    parser.add_argument('--out', default='data/local/candidates')
    args = parser.parse_args()

    normalize = not args.no_normalize
    # "fused" is not an index; the primary encoder supplies similarity values and the
    # eligibility view, while fusion decides only the order.
    primary = args.rank_by if args.rank_by != 'fused' else args.fuse[0]
    info, _ = load_index(Path(args.seeds) / 'morgan')
    seeds = [e for e in info['entries'] if e['domain'] == 'enzyme_reference'
             and any((ev.get('context') or {}).get('metal_cofactor') == args.cofactor
                     for ev in e['evidence'])]
    if not seeds:
        raise SystemExit(f'No enzyme seeds with cofactor {args.cofactor}')
    print(f'{len(seeds)} enzyme seeds define the {args.cofactor} platform')

    index, _ = load_index(Path(args.pool) / primary)
    entries = index['entries']
    eligible = [i for i, e in enumerate(entries)
                if e['evidence'][0].get('activation_family') == args.family]
    print(f'{len(eligible)} candidates in family {args.family}')

    queries = [prepare(s['reaction_smiles'], args.family, normalize, normalize) for s in seeds]
    scores, ranks = {}, {}
    for backend in BACKENDS:
        idx, matrix = load_index(Path(args.pool) / backend)
        order = {e['record_id']: n for n, e in enumerate(idx['entries'])}
        columns = [order[entries[i]['record_id']] for i in eligible]
        encoder = Encoder(backend, args.model_dir if backend == 'rxnfp' else None)
        vectors = encoder.encode(queries, batch_size=32)
        sim = pairwise_similarity(vectors, matrix[columns], idx['parameters']['metric'])
        # A candidate's score is its best match to any seed: the platform is a set of
        # capabilities, and proximity to one of them is what matters.
        best = sim.max(axis=0)
        scores[backend] = best
        ranks[backend] = (-np.round(best, 6)).argsort(kind='stable').argsort() + 1
        # Similarity of each candidate to the platform's own chemistry, unnormalised,
        # is what decides whether it has already been done.
        if backend == primary:
            scores['_seed_argmax'] = sim.argmax(axis=0)

    if args.rank_by == 'fused':
        # Reciprocal rank fusion: robust, parameter-light, and it does not require the
        # encoders' similarity scales to be comparable - which they are not.
        fused = sum(1.0 / (args.rrf_k + ranks[b]) for b in args.fuse)
        order_key = fused
        stacked = np.stack([ranks[b] for b in args.fuse])
    else:
        order_key = scores[args.rank_by]
        stacked = np.stack([ranks[b] for b in BACKENDS])
    spread = np.ptp(stacked, axis=0)
    # The worst rank any fused encoder gives a candidate is what decides how firm it is:
    # a candidate one encoder buries is not one to spend an experiment on first.
    worst = stacked.max(axis=0)
    cutoff = max(1, int(len(eligible) * args.firm_percentile / 100))

    chosen, per_paper, skipped = [], {}, []
    for position in np.argsort(-np.round(order_key, 6), kind='stable'):
        entry = entries[eligible[position]]
        best_seed = seeds[int(scores['_seed_argmax'][position])]
        if scores[primary][position] >= args.already_done:
            skipped.append({'record_id': entry['record_id'], 'reason': 'already_performed',
                            'detail': 'the platform already performs this transformation',
                            'closest_seed': best_seed['record_id']})
            continue
        paper = entry['evidence'][0]['source']
        if per_paper.get(paper, 0) >= args.max_per_paper:
            skipped.append({'record_id': entry['record_id'], 'reason': 'source_repeated',
                            'detail': 'this source is already represented'})
            continue
        per_paper[paper] = per_paper.get(paper, 0) + 1
        chosen.append((position, entry, best_seed))
        if len(chosen) >= args.top_k:
            break

    folder = Path(args.out) / f'{args.cofactor}_{args.family}'
    (folder / 'structures').mkdir(parents=True, exist_ok=True)
    lines = [f'# Candidate non-enzymatic reactions for the {args.cofactor} platform', '',
             f'Ranked by **{args.rank_by}** ({"+".join(args.fuse)}) proximity to {len(seeds)} enzyme seeds, over '
             if args.rank_by == 'fused' else
             f'Ranked by **{args.rank_by}** proximity to {len(seeds)} enzyme seeds, over '
             f'{len(eligible)} candidates in family `{args.family}`'
             + (', with both sides expressed at the shared reactive core.' if normalize else '.'), '',
             'These are **retrieved precedents, not predictions**. Nothing here is a feasibility '
             'estimate, a success probability, or a verified transferable reaction. Each card ends '
             'with what a reviewer still has to decide.', '']
    for n, (position, entry, best_seed) in enumerate(chosen, 1):
        diagram = f'structures/cand_{n:02d}.svg'
        seed_diagram = f'structures/seed_{n:02d}.svg'
        draw_reaction(entry['reaction_smiles'], folder / diagram)
        draw_reaction(best_seed['reaction_smiles'], folder / seed_diagram)
        evidence = entry['evidence'][0]
        context = evidence.get('context') or {}
        agreement = ', '.join(f'{b} #{ranks[b][position]}' for b in BACKENDS)
        share = worst[position] / len(eligible)
        firmness = (f'**firm** - every fused encoder ranks it in the top {share:.0%}'
                    if worst[position] <= cutoff else
                    f'contested - one encoder ranks it only #{int(worst[position])} of {len(eligible)} '
                    f'(top {share:.0%})')
        lines += [
            f'## {n}. `{entry["record_id"]}`', '',
            f'![Candidate]({diagram})', '',
            f'**Closest enzyme capability** — `{best_seed["record_id"]}`, similarity '
            f'{scores[primary][position]:.3f}', '',
            f'![Enzyme seed]({seed_diagram})', '',
            '| | |', '|---|---|',
            f'| Rank by each encoder | {agreement} |',
            f'| Agreement | {firmness} |',
            f'| Catalyst / reagent | {markdown(context.get("catalyst"))} |',
            f'| Solvent, T, time | {markdown(context.get("solvent"))}, '
            f'{markdown(context.get("temperature_c"))} °C, {markdown(context.get("time_h"))} h |',
            f'| Reported yield | {markdown((entry["evidence"][0].get("reported_results_raw") or {}).get("yield_percent"))}% |',
            f'| Source | {markdown(evidence["source"])[:150]} |',
            f'| Document type | {markdown(evidence.get("document_type"))} |',
            f'| Locator | {markdown(evidence["source_locator"])} |',
            f'| Acceptor consumed | {context.get("acceptor_consumed")} |',
            f'| Family evidence | {markdown(context.get("family_screen"))} |', '',
            '**Still to decide:** does the enzyme platform supply the same activation, what does the '
            'recorded catalyst or medium provide that a protein cannot, and what would a first '
            'experiment need to distinguish? Mechanism is not recorded here and must be read from '
            'the primary source.', '']

    (folder / 'candidates.md').write_text('\n'.join(lines) + '\n')
    (folder / 'candidates.json').write_text(json.dumps({
        'platform': {'cofactor': args.cofactor, 'seeds': len(seeds)},
        'family': args.family, 'ranked_by': args.rank_by, 'normalized': normalize,
        'pool_candidates': len(eligible), 'already_done_threshold': args.already_done,
        'candidates': [{'record_id': e['record_id'], 'reaction_smiles': e['reaction_smiles'],
                        'closest_seed': s['record_id'],
                        'similarity': float(scores[primary][p]),
                        'rank_spread_across_fused': int(spread[p]),
                        'worst_rank_across_fused': int(worst[p]),
                        'firm': bool(worst[p] <= cutoff),
                        'ranks': {b: int(ranks[b][p]) for b in BACKENDS},
                        'evidence': e['evidence'][0]} for p, e, s in chosen],
        'skipped': skipped[:50],
    }, ensure_ascii=False, indent=2) + '\n')
    print(f'\n{len(chosen)} candidates written to {folder / "candidates.md"}')
    done = sum(1 for s in skipped if s['reason'] == 'already_performed')
    repeat = sum(1 for s in skipped if s['reason'] == 'source_repeated')
    contested = sum(1 for p, _, _ in chosen if worst[p] > cutoff)
    print(f'{done} dropped as already performed by the platform; {repeat} dropped to keep sources distinct.')
    print(f'{len(chosen) - contested} of {len(chosen)} are firm: every fused encoder ranks them in '
          f'the top {args.firm_percentile:g}% of the pool. The rest are contested, which is '
          'information about the candidate rather than a defect to hide.')


if __name__ == '__main__':
    main()
