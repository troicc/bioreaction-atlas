"""Label-free retrieval agreement on an explicitly shared, provenance-checked pool.

Agreement is not retrieval accuracy. Scores are rounded before ranking so numerical
noise is not interpreted as evidence that a tied candidate is preferable.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

from .corpus import json_hash, load_index, sha
from .encoders import pairwise_similarity

BACKENDS = ('morgan', 'substrate', 'drfp', 'rxnfp')


def topk_membership(scores, k):
    """Selection probabilities under a uniform permutation of the boundary tie."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError('Scores must be a finite one-dimensional array')
    if not isinstance(k, (int, np.integer)) or not 1 <= k <= len(scores):
        raise ValueError('k must be an integer between 1 and candidate count')
    threshold = np.partition(scores, len(scores) - k)[len(scores) - k]
    better, tied = scores > threshold, scores == threshold
    probability = better.astype(float)
    remaining = k - int(better.sum())
    probability[tied] = remaining / int(tied.sum())
    return probability, bool(remaining < int(tied.sum()))


def rank_correlation(left, right):
    """Spearman over the entire aligned pool, with average ranks for ties."""
    left, right = np.asarray(left), np.asarray(right)
    if left.ndim != 1 or left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError('Rank correlation requires aligned finite score arrays')
    a, b = rankdata(left), rankdata(right)
    a, b = a - a.mean(), b - b.mean()
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.clip(a @ b / denominator, -1, 1)) if denominator else None


def source_ids(entry):
    result = set()
    for evidence in entry['evidence']:
        if not evidence.get('source'):
            continue
        source = evidence['source'].strip().lower()
        for prefix in ('https://', 'http://', 'dx.doi.org/', 'doi.org/', 'doi:'):
            source = source.removeprefix(prefix)
        result.add(source.strip())
    return result


def allowed_candidates(query, candidates, exclude_shared_source=False):
    sources = source_ids(query)
    return np.asarray([c['record_id'] != query['record_id'] and
                       (not exclude_shared_source or not sources.intersection(source_ids(c)))
                       for c in candidates], dtype=bool)


def load_common_pool(root, backends=BACKENDS):
    """Reject different corpora/views and align by stable IDs, never row position."""
    indices = {b: load_index(Path(root) / b) for b in backends}
    if len({i['corpus_sha256'] for i, _ in indices.values()}) != 1:
        raise ValueError('Encoders must use the same input corpus')
    if len({i['parameters']['structure_view'] for i, _ in indices.values()}) != 1:
        raise ValueError('Encoders must use the same structural view')
    maps = {b: {e['record_id']: (n, e) for n, e in enumerate(i['entries'])} for b, (i, _) in indices.items()}
    common = sorted(set.intersection(*(set(m) for m in maps.values())))
    if not common:
        raise ValueError('No common entries')
    for ident in common:
        if len({json_hash(m[ident][1]) for m in maps.values()}) != 1:
            raise ValueError('Common entry identity/provenance differs between encoders')
    entries = [maps[backends[0]][ident][1] for ident in common]
    vectors = {b: matrix[[maps[b][ident][0] for ident in common]] for b, (_, matrix) in indices.items()}
    provenance = {}
    for b, (info, _) in indices.items():
        if info['parameters']['backend'] != b:
            raise ValueError('Backend does not match index folder')
        provenance[b] = {
            'parameters': info['parameters'], 'corpus_sha256': info['corpus_sha256'],
            'vectors_sha256': info['vectors_sha256'],
            'index_sha256': sha((Path(root) / b / 'index.json').read_bytes()),
            'available_domains': dict(Counter(e['domain'] for e in info['entries'])),
            'excluded_source_rows': len(info['excluded']),
            'outside_common_pool_ids': sorted(set(maps[b]) - set(common)),
        }
    return entries, vectors, provenance


def source_macro_mean(rows, key):
    """Mean within each source, then mean across sources (descriptive sensitivity)."""
    groups = {}
    for r in rows:
        if r[key] is not None:
            for source in r['query_sources']:
                groups.setdefault(source, []).append(r[key])
    return float(np.mean([np.mean(values) for values in groups.values()])) if groups else None


def analyze(entries, vectors, provenance, candidate_domain='patent_reference',
            exclude_shared_source=False, ks=(5, 10, 20, 50), decimals=6):
    ks = tuple(sorted(set(ks)))
    if not ks or any(not isinstance(k, int) or k < 1 for k in ks):
        raise ValueError('ks must contain positive integers')
    if not isinstance(decimals, int) or not 0 <= decimals <= 12:
        raise ValueError('decimals must be an integer in [0, 12]')
    query_pos = [i for i, e in enumerate(entries) if e['domain'] == 'enzyme_reference']
    candidate_pos = [i for i, e in enumerate(entries) if e['domain'] == candidate_domain]
    queries, candidates = [entries[i] for i in query_pos], [entries[i] for i in candidate_pos]
    if not queries or not candidates:
        raise ValueError('Empty query or candidate pool')
    scores = {b: np.round(pairwise_similarity(v[query_pos], v[candidate_pos],
                                             provenance[b]['parameters']['metric']).astype(float), decimals)
              for b, v in vectors.items()}
    pairs = list(combinations(vectors, 2))
    rows, query_summaries, exclusions = [], [], []
    for n, query in enumerate(queries):
        allowed = allowed_candidates(query, candidates, exclude_shared_source)
        count = int(allowed.sum())
        if count < max(ks):
            exclusions.append({'query_id': query['record_id'], 'eligible': count, 'reason': 'fewer_than_max_k'})
            continue
        # Use an explicit ID tie-break even if this API is called with unsorted entries.
        s = {b: matrix[n, allowed] for b, matrix in scores.items()}
        candidate_ids = np.asarray([c['record_id'] for c, keep in zip(candidates, allowed) if keep])
        orders = {b: np.lexsort((candidate_ids, -values)) for b, values in s.items()}
        memberships = {b: {k: topk_membership(values, k) for k in ks} for b, values in s.items()}
        query_rows = []
        for a, b in pairs:
            row = {'query_id': query['record_id'], 'query_sources': sorted(source_ids(query)),
                   'encoder_a': a, 'encoder_b': b, 'eligible_candidates': count,
                   'spearman': rank_correlation(s[a], s[b])}
            for k in ks:
                pa, ta = memberships[a][k]
                pb, tb = memberships[b][k]
                row[f'overlap_at_{k}'] = len(set(orders[a][:k]) & set(orders[b][:k])) / k
                # Independent tie randomization in the two lists: E[intersection size]/k.
                row[f'expected_overlap_at_{k}'] = float(pa @ pb / k)
                row[f'boundary_tie_a_at_{k}'] = ta
                row[f'boundary_tie_b_at_{k}'] = tb
                row[f'random_overlap_at_{k}'] = k / count
            query_rows.append(row)
        rows.extend(query_rows)
        selection_k = 10 if 10 in ks else ks[0]
        query_summaries.append({'query_id': query['record_id'], 'query_sources': sorted(source_ids(query)),
                                'mean_expected_overlap': float(np.mean([r[f'expected_overlap_at_{selection_k}'] for r in query_rows])),
                                'selection_k': selection_k})
    if not rows:
        raise ValueError('No queries have enough eligible candidates')
    summaries = []
    metric_keys = ['spearman'] + [f'{prefix}_at_{k}' for k in ks for prefix in
                                  ('overlap', 'expected_overlap', 'boundary_tie_a', 'boundary_tie_b', 'random_overlap')]
    for a, b in pairs:
        subset = [r for r in rows if r['encoder_a'] == a and r['encoder_b'] == b]
        result = {'encoder_a': a, 'encoder_b': b, 'queries': len(subset), 'metrics': {}}
        for key in metric_keys:
            values = [float(r[key]) for r in subset if r[key] is not None]
            result['metrics'][key] = {
                'mean': float(np.mean(values)) if values else None,
                'median': float(np.median(values)) if values else None,
                'q10': float(np.quantile(values, .1)) if values else None,
                'q90': float(np.quantile(values, .9)) if values else None,
                'source_macro_mean': source_macro_mean(subset, key), 'defined_queries': len(values),
            }
        summaries.append(result)
    result = {'candidate_domain': candidate_domain, 'exclude_shared_source': exclude_shared_source,
              'self_excluded': True, 'query_count': len(query_summaries), 'candidate_pool_size': len(candidates),
              'query_source_count': len(set().union(*(source_ids(q) for q in queries))),
              'eligible_candidate_range': [min(r['eligible_candidates'] for r in rows), max(r['eligible_candidates'] for r in rows)],
              'ks': list(ks), 'score_decimals': decimals, 'query_exclusions': exclusions,
              'pairs': summaries, 'query_disagreement': sorted(query_summaries, key=lambda q: (q['mean_expected_overlap'], q['query_id']))}
    return result, rows, scores, queries, candidates
