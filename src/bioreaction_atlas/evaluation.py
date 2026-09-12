"""Discovery-event retrieval evaluation with explicit temporal and provenance gates.

Unknown candidates are unlabeled, never converted to failed enzyme reactions.
"""
from datetime import date
import hashlib
import math
import numpy as np
from .corpus import load_index, json_hash
from .encoders import pairwise_similarity

FEATURES = ('metal', 'activation', 'light', 'medium')


def iso(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError('Verified dates must be YYYY-MM-DD')
    date.fromisoformat(value)
    return value


def validate_protocol(protocol, info):
    if protocol.get('benchmark_version') != '1.0':
        raise ValueError('Unsupported benchmark version')
    cutoff = iso(protocol.get('cutoff_date'))
    if not protocol.get('candidate_pool_protocol') or not protocol.get('freeze_note'):
        raise ValueError('Describe candidate construction and protocol freeze before running evaluation')
    entries = {r['record_id']: r for r in info['entries']}
    seeds = protocol.get('seed_entry_ids', [])
    candidates = protocol.get('candidates', [])
    events = protocol.get('events', [])
    if not seeds or not candidates or not events:
        raise ValueError('Nonempty seeds, a fixed candidate pool and held-out discovery events are required')
    if len(seeds) != len(set(seeds)):
        raise ValueError('Duplicate seed IDs')
    selected, seen_candidates, assigned_entries = set(seeds), set(), set()
    for c in candidates:
        key = c.get('candidate_id')
        if not key or key in seen_candidates or not c.get('entry_ids'):
            raise ValueError('Candidate IDs must be unique and contain entries')
        seen_candidates.add(key)
        for entry in c['entry_ids']:
            if entry in assigned_entries:
                raise ValueError('An entry cannot be duplicated across candidate groups')
            assigned_entries.add(entry)
            selected.add(entry)
    if assigned_entries.intersection(seeds):
        raise ValueError('Seed entries and candidate entries must be separate')
    known_reactions = {entries[k]['reaction_smiles'] for k in seeds if k in entries}
    if any(entries[k]['reaction_smiles'] in known_reactions for k in assigned_entries if k in entries):
        raise ValueError('Candidate pool includes an exact transformation already present in enzyme seeds')
    for key in selected:
        if key not in entries:
            raise ValueError(f'Fixed evaluation entry missing from this index: {key}; do not silently shrink the pool')
        r = entries[key]
        expected = 'enzymatic' if key in seeds else 'nonenzymatic'
        if r['domain'] != expected:
            raise ValueError(f'{key}: expected manually curated {expected} evidence, got {r["domain"]}')
        if not r.get('evidence'):
            raise ValueError(f'{key}: missing evidence')
        for e in r['evidence']:
            if e.get('review_status') != 'checked' or not e.get('date_evidence') or not e.get('source_locator'):
                raise ValueError(f'{key}: source, date and record must be checked before historical evaluation')
            if iso(e.get('first_public_date')) >= cutoff:
                raise ValueError(f'{key}: evidence is not before the cutoff')
        if key in seeds and not any(e.get('outcome') == '检出' for e in r['evidence']):
            raise ValueError(f'{key}: seed lacks a reviewed detected-product result')
    event_ids = set()
    for event in events:
        if not event.get('event_id') or event['event_id'] in event_ids:
            raise ValueError('Discovery event IDs must be unique')
        event_ids.add(event['event_id'])
        if not event.get('paper_id') or not event.get('date_evidence') or not event.get('mapping_evidence'):
            raise ValueError('Each event needs a paper group, date source and evidence for candidate mapping or lack of coverage')
        if iso(event.get('first_public_date')) < cutoff:
            raise ValueError('Held-out event predates cutoff')
        if not isinstance(event.get('candidate_ids'), list) or set(event['candidate_ids']) - seen_candidates:
            raise ValueError('Event mapping contains an unknown candidate')
    for key, annotation in protocol.get('condition_annotations', {}).items():
        if key not in selected:
            raise ValueError('Condition annotation references an unused/unknown entry')
        for field, value in annotation.items():
            if field not in FEATURES:
                raise ValueError('Unknown condition feature: ' + field)
            if not isinstance(value, dict) or not value.get('value') or not value.get('source') or not value.get('source_locator'):
                raise ValueError('Condition features need a normalized value and source evidence')
            if value.get('evidence_type') not in ('experimental_support', 'author_proposal'):
                raise ValueError('Project hypotheses cannot enter the historical condition baseline')
            if iso(value.get('source_public_date')) >= cutoff:
                raise ValueError('Condition evidence leaks past the cutoff')
    if not protocol.get('allow_pretrained_exploration', False) and info['parameters']['backend'] == 'rxnfp':
        raise ValueError('RXNFP training chronology is unverified; explicitly allow and separately label exploratory pretrained results')
    return entries


def condition_agreement(a, b):
    agreements, comparable = [], []
    for key in FEATURES:
        av, bv = a.get(key, {}).get('value'), b.get(key, {}).get('value')
        if av is not None and bv is not None:
            comparable.append(key)
            if str(av).casefold() == str(bv).casefold():
                agreements.append(key)
    # Fixed denominator: missing information earns no agreement, not a negative label.
    return {'score': len(agreements)/len(FEATURES), 'matched_fields': agreements,
            'compared_fields': comparable, 'missing_fields': [f for f in FEATURES if f not in comparable]}


def rank_pool(protocol, info, matrix, condition_weight=0.15):
    if not math.isfinite(condition_weight) or not 0 <= condition_weight <= 1:
        raise ValueError('Condition weight must be finite and within [0,1]')
    validate_protocol(protocol, info)
    positions = {r['record_id']: i for i, r in enumerate(info['entries'])}
    seed_ids = protocol['seed_entry_ids']
    seed_matrix = matrix[[positions[k] for k in seed_ids]]
    selected_ids = [key for c in protocol['candidates'] for key in c['entry_ids']]
    scores = pairwise_similarity(matrix[[positions[k] for k in selected_ids]], seed_matrix, info['parameters']['metric'])
    scores_by_id = {key: scores[i] for i, key in enumerate(selected_ids)}
    annotations = protocol.get('condition_annotations', {})
    rows = []
    for c in protocol['candidates']:
        structural_best, conditioned_best = None, None
        sources = set()
        for key in c['entry_ids']:
            sources.update(e['source'] for e in info['entries'][positions[key]]['evidence'])
            for j, seed_id in enumerate(seed_ids):
                structural = float(scores_by_id[key][j])
                agreement = condition_agreement(annotations.get(key, {}), annotations.get(seed_id, {}))
                row = {'candidate_entry_id': key, 'seed_entry_id': seed_id, 'structure_score': structural,
                       'condition_agreement': agreement, 'combined_score': structural+condition_weight*agreement['score']}
                if structural_best is None or structural > structural_best['structure_score']:
                    structural_best = row
                if conditioned_best is None or row['combined_score'] > conditioned_best['combined_score']:
                    conditioned_best = row
        rows.append({'candidate_id': c['candidate_id'], 'structure_score': structural_best['structure_score'],
                     'combined_score': conditioned_best['combined_score'], 'source_frequency': len(sources),
                     'structure_best_pair': structural_best, 'condition_best_pair': conditioned_best})
    return rows


def _metrics(scores, events, ks):
    # Ties are expected, especially for frequency/random controls. Average hit probability
    # under uniform permutations within a tie; never let candidate IDs improve recall.
    per_event = []
    for e in events:
        targets = set(e['candidate_ids'])
        if not targets:
            per_event.append({'event_id': e['event_id'], 'paper_id': e['paper_id'], 'covered': False,
                              'hit_at_k': {str(k): 0.0 for k in ks}, 'expected_best_rank': None})
            continue
        highest = max(scores[t] for t in targets)
        above = sum(v > highest+1e-10 for v in scores.values())
        tied = {key for key, v in scores.items() if abs(v-highest) <= 1e-10}
        successful = len(tied.intersection(targets))
        hit = {}
        for k in ks:
            slots = min(max(k-above, 0), len(tied))
            miss = (math.comb(len(tied)-successful, slots)/math.comb(len(tied), slots)) if slots <= len(tied)-successful else 0
            hit[str(k)] = 1-float(miss)
        per_event.append({'event_id': e['event_id'], 'paper_id': e['paper_id'], 'covered': True,
                          'hit_at_k': hit, 'expected_best_rank': above+(len(tied)+1)/(successful+1)})
    covered = [e for e in per_event if e['covered']]
    return {'events': per_event,
            'overall_recall_at_k': {str(k): float(np.mean([e['hit_at_k'][str(k)] for e in per_event])) for k in ks},
            'covered_event_recall_at_k': {str(k): float(np.mean([e['hit_at_k'][str(k)] for e in covered])) if covered else None for k in ks}}


def evaluate(index_dir, protocol, ks=(1, 5, 10), condition_weight=0.15, seed=17, bootstrap=1000):
    if not ks or any(not isinstance(k, int) or k < 1 for k in ks):
        raise ValueError('k values must be positive integers')
    if bootstrap < 1:
        raise ValueError('bootstrap must be positive')
    info, matrix = load_index(index_dir)
    rows = rank_pool(protocol, info, matrix, condition_weight)
    methods = {'structure': {r['candidate_id']: r['structure_score'] for r in rows},
               'structure_plus_conditions': {r['candidate_id']: r['combined_score'] for r in rows},
               'source_frequency': {r['candidate_id']: r['source_frequency'] for r in rows},
               'uniform_random_expectation': {r['candidate_id']: 0 for r in rows}}
    metrics = {name: _metrics(scores, protocol['events'], ks) for name, scores in methods.items()}
    rng = np.random.default_rng(seed)
    # Bootstrap independent paper groups, preserving within-paper event dependence.
    papers = sorted({e['paper_id'] for e in protocol['events']})
    for method in metrics.values():
        method['paper_cluster_bootstrap_ci95'] = {}
        for k in ks:
            means = []
            if len(papers) >= 2:
                for _ in range(bootstrap):
                    selected = rng.choice(papers, len(papers), replace=True)
                    values = [e['hit_at_k'][str(k)] for p in selected for e in method['events'] if e['paper_id'] == p]
                    means.append(np.mean(values))
            method['paper_cluster_bootstrap_ci95'][str(k)] = np.quantile(means, [.025,.975]).tolist() if means else None
    return {'protocol_sha256': json_hash(protocol), 'corpus_sha256': info['corpus_sha256'],
            'parameters': info['parameters'], 'cutoff_date': protocol['cutoff_date'],
            'candidate_count': len(rows), 'event_count': len(protocol['events']), 'paper_groups': len(papers),
            'candidate_coverage': sum(bool(e['candidate_ids']) for e in protocol['events'])/len(protocol['events']),
            'condition_weight': condition_weight, 'random_seed': seed, 'bootstrap_resamples': bootstrap,
            'pretrained_exploratory': info['parameters']['backend'] == 'rxnfp',
            'tie_policy': 'Expected hit probability under uniform tie permutations',
            'interpretation': 'Recovery of published discoveries, not experimental success probability. Unmapped events remain in overall recall.',
            'rankings': rows, 'metrics': metrics}
