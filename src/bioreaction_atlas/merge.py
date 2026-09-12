"""Merge collaborators' intakes without overwriting conflicts or losing provenance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from .curation import read_dataset, validate
from .schema import VERSION, TABLES


def merge_datasets(paths, prefixes=None):
    if prefixes is not None and (len(prefixes) != len(paths) or len(set(prefixes)) != len(prefixes)):
        raise ValueError('Provide one distinct prefix per input')
    merged = {'schema_version': VERSION, 'contexts': [], 'experiments': [], 'imports': []}
    seen = {name: {} for name in TABLES}
    for i, path in enumerate(paths):
        data = read_dataset(path)
        report = validate(data)
        if report['errors']:
            raise ValueError(f'{path}: ' + '; '.join(report['errors'][:5]))
        original_hash = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        data = deepcopy(data)
        prefix = prefixes[i] if prefixes else ''
        if prefix:
            for name in TABLES:
                for row in data[name]:
                    for key in ('context_id', 'discovery_id', 'assay_id', 'measurement_id'):
                        if row.get(key):
                            row[key] = prefix + '_' + row[key]
        duplicates = 0
        for name, spec in TABLES.items():
            id_key = spec['fields'][0]['key']
            for row in data[name]:
                key = row[id_key]
                if key in seen[name]:
                    if row != seen[name][key]:
                        raise ValueError(f'Conflicting {id_key}={key}; assign curator prefixes or resolve explicitly')
                    duplicates += 1
                    continue
                seen[name][key] = row
                merged[name].append(row)
        merged['imports'].append({'input_name': Path(path).name, 'normalized_sha256': original_hash,
                                  'prefix': prefix, 'identical_rows_deduplicated': duplicates})
    report = validate(merged)
    if report['errors']:
        raise ValueError('Merged data invalid: ' + '; '.join(report['errors'][:5]))
    # A shared source is a review hint, never an automatic scientific deduplication.
    sources = {}
    for row in merged['contexts']:
        sources.setdefault(row['source'], []).append(row['context_id'])
    merged['merge_notes'] = {'shared_sources': {s: ids for s, ids in sources.items() if len(ids) > 1},
                             'discovery_events_reconciled': False}
    return merged
