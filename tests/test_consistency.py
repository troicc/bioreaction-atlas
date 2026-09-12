from itertools import permutations

import numpy as np
import pytest

from bioreaction_atlas.consistency import (
    allowed_candidates, analyze, load_common_pool, rank_correlation, topk_membership,
)


def test_boundary_ties_match_exhaustive_independent_permutations():
    left, right = [3, 2, 2, 0], [1, 2, 2, 0]
    p, tied = topk_membership(left, 2)
    q, _ = topk_membership(right, 2)
    assert tied and p.sum() == pytest.approx(2)
    a = [{0, i} for i in (1, 2)]
    b = [{1, 2}]
    expected = np.mean([len(x & y) / 2 for x in a for y in b])
    assert p @ q / 2 == pytest.approx(expected)
    assert np.allclose(topk_membership([1, 1, 1, 1], 2)[0], .5)
    assert not topk_membership([1, 1, 0, 0], 2)[1]


@pytest.mark.parametrize('k', [0, 5, 1.5])
def test_topk_rejects_invalid_budget(k):
    with pytest.raises(ValueError):
        topk_membership([1, 2, 3, 4], k)


def test_spearman_full_pool_ties_and_undefined():
    assert rank_correlation([1, 2, 2, 4], [4, 2, 2, 1]) == pytest.approx(-1)
    assert rank_correlation([1, 1], [1, 2]) is None
    for order in permutations(range(3)):
        assert rank_correlation(np.array([1, 2, 4])[list(order)], np.array([1, 3, 2])[list(order)]) == pytest.approx(.5)


def entry(ident, source, domain='enzyme_reference'):
    return {'record_id': ident, 'domain': domain, 'reaction_smiles': 'CCO>>CC=O',
            'evidence': [{'source': source}]}


def test_self_and_shared_source_exclusion():
    query = entry('Q', 'https://doi.org/10.1/ABC')
    candidates = [query, entry('A', 'doi.org/10.1/abc'), entry('B', '10.1/def')]
    assert allowed_candidates(query, candidates).tolist() == [False, True, True]
    assert allowed_candidates(query, candidates, True).tolist() == [False, False, True]


def test_analyze_common_pool_and_no_accuracy_claim():
    entries = [entry('Q', 'P1'), entry('A', 'P2', 'patent_reference'),
               entry('B', 'P3', 'patent_reference'), entry('C', 'P4', 'patent_reference')]
    vectors = {'a': np.array([[1, 0], [1, 0], [1, 1], [0, 1]]),
               'b': np.array([[1, 0], [0, 1], [1, 1], [1, 0]])}
    provenance = {b: {'parameters': {'metric': 'cosine'}} for b in vectors}
    result, rows, *_ = analyze(entries, vectors, provenance, ks=(1, 2))
    assert result['query_count'] == 1
    assert rows[0]['spearman'] == pytest.approx(-1)
    assert rows[0]['expected_overlap_at_1'] == 0
    assert rows[0]['overlap_at_2'] == .5
    assert rows[0]['random_overlap_at_2'] == pytest.approx(2 / 3)
    assert 'accuracy' not in result and 'candidate_coverage' not in result
    with pytest.raises(ValueError, match='No queries'):
        analyze(entries, vectors, provenance, ks=(4,))


def test_common_pool_aligns_ids_and_rejects_different_corpora(monkeypatch, tmp_path):
    for b in ('a', 'b'):
        (tmp_path / b).mkdir()
        (tmp_path / b / 'index.json').write_text('{}')
    a, b, extra = entry('A', 'P1'), entry('B', 'P2'), entry('Z', 'P3')
    def info(backend, rows):
        return {'corpus_sha256': 'same', 'parameters': {'structure_view': 'same', 'backend': backend},
                'vectors_sha256': 'fixture', 'entries': rows, 'excluded': []}
    indices = {'a': (info('a', [b, a]), np.array([[2, 0], [1, 0]])),
               'b': (info('b', [a, extra, b]), np.array([[10, 0], [30, 0], [20, 0]]))}
    monkeypatch.setattr('bioreaction_atlas.consistency.load_index', lambda path: indices[path.name])
    entries, vectors, provenance = load_common_pool(tmp_path, ('a', 'b'))
    assert [e['record_id'] for e in entries] == ['A', 'B']
    assert vectors['a'][:, 0].tolist() == [1, 2]
    assert vectors['b'][:, 0].tolist() == [10, 20]
    assert provenance['b']['outside_common_pool_ids'] == ['Z']
    indices['b'][0]['corpus_sha256'] = 'different'
    with pytest.raises(ValueError, match='same input corpus'):
        load_common_pool(tmp_path, ('a', 'b'))
