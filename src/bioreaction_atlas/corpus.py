"""Reference corpora and reusable, hash-verified matrix indices."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from .chemistry import canonical_reaction
from .curation import validate, write_json
from .encoders import Encoder, structure_view, pairwise_similarity

CORPUS_VERSION = '1.0'
LEGACY_SHA = 'abe6bd9f0c1dcc3487b6a2a595d427b70c6714b9a2bfd1c195e50b702ffe9245'
SCHNEIDER_BLOB = '5d7faad69a75f539a50e5d254feee7c69bac3e8f'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_hash(data):
    return sha(json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False).encode())


def import_references(legacy_path, patent_path, limit=2000, seed=17):
    if limit < 1:
        raise ValueError('Reference sample limit must be positive')
    raw = Path(legacy_path).read_bytes()
    if sha(raw) != LEGACY_SHA:
        raise ValueError('Legacy input differs from the pinned file')
    legacy = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    patent_raw = Path(patent_path).read_bytes()
    if hashlib.sha1(f'blob {len(patent_raw)}\0'.encode()+patent_raw).hexdigest() != SCHNEIDER_BLOB:
        raise ValueError('Patent input differs from the pinned file')
    patents = list(csv.DictReader(patent_raw.decode().splitlines(), delimiter='\t'))
    # Sample across the entire table by a fixed hash, without consulting enzyme reactions.
    chosen = sorted(enumerate(patents, 2), key=lambda x: sha(f'{seed}:{x[0]}'.encode()))[:limit]
    records = []
    for i, r in enumerate(legacy, 2):
        records.append({'record_id': f'ENZV6_ROW_{i}', 'reaction_smiles': r.get('cannonical_reactions') or r.get('reaction_smiles'),
                        'domain': 'enzyme_reference', 'source': r.get('doi') or 'EnzymeEngineeringDB V6',
                        'source_locator': f'EnzymeEngineeringDB V6 CSV row {i}; original SI not checked',
                        'review_status': 'imported', 'first_public_date': None, 'date_evidence': None,
                        'reported_date_raw': r.get('date published '), 'label': r.get('named_reactions') or 'unclassified',
                        'context': {'metal_cofactor': r.get('cofactor'), 'scaffold': r.get('enzyme_name_from_paper'),
                                    'enzyme_form': r.get('enzyme_form'), 'source': r.get('doi')},
                        'reported_results_raw': {k: r.get(k) for k in ('TTN (if applicable)', 'activity_for_reaction_% (if applicable)',
                         'selectivity(ee%),diastereo or chemo should be a separate smiles entry')},
                        'outcome': 'not_reviewed'})
    for i, r in chosen:
        records.append({'record_id': f'SCH50K_ROW_{i}', 'reaction_smiles': r['original_rxn'],
                        'domain': 'patent_reference', 'source': r['source'],
                        'source_locator': f'Schneider50k TSV row {i}; patent procedure not checked',
                        'review_status': 'imported', 'first_public_date': None, 'date_evidence': None,
                        'label': r['rxn_class'], 'context': {}, 'outcome': 'not_reviewed'})
    return {'corpus_version': CORPUS_VERSION, 'purpose': 'reference_exploration_not_historical_benchmark',
            'sources': [{'name': 'EnzymeEngineeringDB V6', 'sha256': sha(raw), 'rows': len(legacy)},
                        {'name': 'Schneider50k', 'sha256': sha(patent_raw), 'rows': len(patents),
                         'sample_size': len(chosen), 'sample_seed': seed, 'sampling': 'SHA256(seed:row), independent of targets'}],
            'records': records}


def curated_corpus(data):
    report = validate(data)
    if report['errors']:
        raise ValueError('; '.join(report['errors'][:10]))
    contexts = {r['context_id']: r for r in data['contexts']}
    records = []
    for r in data['experiments']:
        c = contexts[r['context_id']]
        status = 'checked' if c['record_status'] == '已核对' and r.get('structure_status') == '已核对' else 'draft'
        if c['record_status'] == '示例':
            status = 'example'
        records.append({'record_id': r['measurement_id'], 'reaction_smiles': r.get('reaction_smiles'),
                        'domain': {'酶催化': 'enzymatic', '非酶催化': 'nonenzymatic', '无催化剂对照': 'control'}[c['catalysis_mode']],
                        'source': c['source'], 'source_locator': r['source_locator'], 'review_status': status,
                        'first_public_date': c.get('first_public_date'), 'date_evidence': c.get('date_evidence'),
                        'discovery_id': c['discovery_id'], 'label': c['reaction_name'], 'context': c,
                        'measurement': r, 'outcome': r['outcome']})
    return {'corpus_version': CORPUS_VERSION, 'purpose': 'curated_intake', 'records': records}


def encode_corpus(corpus, out_dir, backend='morgan', model_dir=None, allow_unreviewed=False, batch_size=32):
    if batch_size < 1:
        raise ValueError('batch_size must be positive')
    if corpus.get('corpus_version') != CORPUS_VERSION or not isinstance(corpus.get('records'), list):
        raise ValueError('Invalid corpus format/version')
    encoder = Encoder(backend, model_dir)
    grouped, excluded, ids = {}, [], set()
    for row in corpus['records']:
        if not isinstance(row, dict):
            raise ValueError('Each corpus record must be an object')
        if not isinstance(row.get('record_id'), str) or not row['record_id'] or row['record_id'] in ids:
            raise ValueError('Missing or duplicate corpus record ID')
        if row.get('domain') not in ('enzymatic','nonenzymatic','control','enzyme_reference','patent_reference','unknown'):
            raise ValueError('Unknown corpus domain')
        if row.get('review_status') not in ('checked','imported','draft','example'):
            raise ValueError('Unknown corpus review status')
        if row.get('reaction_smiles') is not None and not isinstance(row['reaction_smiles'],str):
            raise ValueError('reaction_smiles must be text or null')
        ids.add(row['record_id'])
        reason = None
        if row.get('review_status') == 'example':
            reason = 'example'
        elif row.get('review_status') != 'checked' and not allow_unreviewed:
            reason = 'unreviewed'
        elif not row.get('source') or not row.get('source_locator'):
            reason = 'missing_provenance'
        if reason is None:
            try:
                canonical = canonical_reaction(row.get('reaction_smiles') or '')
                prepared = encoder.prepare(canonical)
            except ValueError as e:
                reason = str(e)
        if reason:
            excluded.append({'record_id': row['record_id'], 'reason': reason})
            continue
        # Do not merge biological and patent evidence into a single scientific label.
        key = (row.get('domain', 'unknown'), prepared)
        if key not in grouped:
            grouped[key] = {'record_id': 'R_'+sha((key[0]+'|'+prepared).encode())[:20],
                            'reaction_smiles': prepared, 'domain': key[0], 'evidence': []}
        grouped[key]['evidence'].append(row)
    entries = list(grouped.values())
    matrices, keep = [], []
    for start in range(0, len(entries), batch_size):
        batch = entries[start:start+batch_size]
        vectors = encoder.encode([r['reaction_smiles'] for r in batch], batch_size=batch_size)
        for row, vector in zip(batch, vectors, strict=True):
            if not np.isfinite(vector).all() or np.linalg.norm(vector) == 0:
                excluded.extend({'record_id': e['record_id'], 'reason': 'zero_or_nonfinite_fingerprint'} for e in row['evidence'])
                continue
            keep.append(row)
            matrices.append(vector)
        if start % (batch_size*10) == 0:
            print(f'{backend}: {min(start+batch_size,len(entries))}/{len(entries)} unique reactions encoded', flush=True)
    matrix = np.asarray(matrices, dtype=np.float32).reshape((-1, encoder.parameters['dimension']))
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(folder/'vectors.npz', vectors=matrix)
    manifest = {'index_version': '2.0', 'parameters': encoder.parameters, 'corpus_sha256': json_hash(corpus),
                'vectors_sha256': sha((folder/'vectors.npz').read_bytes()), 'allow_unreviewed': allow_unreviewed,
                'purpose': corpus.get('purpose'), 'sources': corpus.get('sources', []),
                'input_records': len(corpus['records']), 'entries': keep, 'excluded': excluded}
    write_json(folder/'index.json', manifest)
    return manifest


def load_index(folder):
    folder = Path(folder)
    info = json.loads((folder/'index.json').read_text())
    raw = (folder/'vectors.npz').read_bytes()
    if info.get('index_version') != '2.0' or sha(raw) != info.get('vectors_sha256'):
        raise ValueError('Index version or matrix checksum mismatch')
    with np.load(folder/'vectors.npz', allow_pickle=False) as archive:
        matrix = archive['vectors']
    if matrix.shape != (len(info['entries']), info['parameters']['dimension']) or not np.isfinite(matrix).all():
        raise ValueError('Invalid index matrix')
    if len({r['record_id'] for r in info['entries']}) != len(info['entries']):
        raise ValueError('Duplicate index entry IDs')
    return info, matrix


def find_neighbors(folder, reaction, top_k=10, model_dir=None, domain=None, exclude_source=None):
    if top_k < 1:
        raise ValueError('top_k must be positive')
    info, matrix = load_index(folder)
    encoder = Encoder(info['parameters']['backend'], model_dir)
    if encoder.parameters != info['parameters']:
        raise ValueError('Encoder/model parameters differ from index; rebuild or use the matching model')
    query = encoder.encode([reaction])
    if np.linalg.norm(query) == 0:
        raise ValueError('Zero query fingerprint')
    allowed = [i for i, row in enumerate(info['entries']) if (not domain or row['domain'] == domain)
               and (not exclude_source or all(e['source'] != exclude_source for e in row['evidence']))]
    scores = pairwise_similarity(query, matrix[allowed], info['parameters']['metric'])[0]
    ranked = sorted(zip(allowed, scores), key=lambda x: (-float(x[1]), info['entries'][x[0]]['record_id']))[:top_k]
    return {'query': structure_view(reaction), 'parameters': info['parameters'], 'eligible': len(allowed),
            'interpretation': 'Structural similarity, not enzymatic feasibility. Source review status is retained.',
            'hits': [{'similarity': float(score), **info['entries'][i]} for i, score in ranked]}
