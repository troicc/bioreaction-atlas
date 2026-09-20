"""Bulk intake of non-enzymatic methodology reactions as a candidate pool.

Records are `imported`: they carry a literature identifier but have not passed
primary-source review. Two things are deliberately never inferred here — a
mechanism, and a verified earliest public date from a publication year.
"""
from .activation import FAMILIES, catalytic_context, family_screen
from .chemistry import canonical_reaction
from .corpus import CORPUS_VERSION, sha

REQUIRED = ('reaction_smiles', 'family', 'source_doi')
OPTIONAL = ('catalyst', 'reagents', 'solvent', 'temperature_c', 'time_h', 'loading',
            'yield_percent', 'source_year', 'source_locator', 'external_id',
            'reaction_name', 'first_public_date', 'date_evidence', 'notes')
CONDITION_COLUMNS = ('catalyst', 'reagents', 'solvent', 'temperature_c', 'time_h', 'loading')


def build_records(rows, prefix='METH', screen=True):
    """Return (records, skipped). Every rejected row is reported, never dropped silently.

    With `screen`, rows that carry neither the family's diagnostic reactant group nor a
    diagnostic catalyst are rejected. A methodology paper's substrate-preparation steps
    are exactly the routine chemistry the pool is meant to exclude.
    """
    records, skipped, seen = [], [], {}
    for n, row in enumerate(rows, 2):
        missing = [c for c in REQUIRED if not (row.get(c) or '').strip()]
        if missing:
            skipped.append({'row': n, 'reason': 'missing ' + ', '.join(missing)})
            continue
        family = row['family'].strip()
        if family not in FAMILIES:
            skipped.append({'row': n, 'reason': f'unknown family {family}'})
            continue
        raw = row['reaction_smiles'].strip()
        try:
            canonical = canonical_reaction(raw)
        except ValueError as exc:
            skipped.append({'row': n, 'reason': f'unparseable reaction: {exc}'})
            continue

        context = catalytic_context(raw, family)
        explicit = [f for f in CONDITION_COLUMNS if (row.get(f) or '').strip()]
        for field in explicit:
            # An exported condition column outranks the lexical agents guess.
            context[field] = row[field].strip()
        if explicit:
            context['context_source'] = 'explicit_export_columns_plus_agents_segment'

        if screen:
            verdict, reason = family_screen(raw, family, context.get('catalyst'))
            if verdict is False:
                skipped.append({'row': n, 'reason': f'off-family: {reason}'})
                continue
            context['family_screen'] = reason if verdict else 'unscreened: ' + reason

        record_id = f"{prefix}_{sha((family + '|' + canonical + '|' + row['source_doi'].strip()).encode())[:16]}"
        if record_id in seen:
            skipped.append({'row': n, 'reason': f'duplicate of row {seen[record_id]}'})
            continue
        seen[record_id] = n
        records.append({
            'record_id': record_id,
            'reaction_smiles': raw,
            'domain': 'nonenzymatic',
            'source': row['source_doi'].strip(),
            'source_locator': (row.get('source_locator') or '').strip()
                              or 'export row; original procedure not checked',
            'review_status': 'imported',
            # A publication year is not a verified earliest public date.
            'first_public_date': (row.get('first_public_date') or '').strip() or None,
            'date_evidence': (row.get('date_evidence') or '').strip() or None,
            'source_year': (row.get('source_year') or '').strip() or None,
            'external_id': (row.get('external_id') or '').strip() or None,
            'label': (row.get('reaction_name') or '').strip() or FAMILIES[family],
            'activation_family': family,
            'context': context,
            'reported_results_raw': {'yield_percent': (row.get('yield_percent') or '').strip() or None},
            'notes': (row.get('notes') or '').strip() or None,
            'outcome': 'not_reviewed',
        })
    return records, skipped


def build_corpus(records, source_name, source_sha, source_rows):
    families = {}
    for record in records:
        families[record['activation_family']] = families.get(record['activation_family'], 0) + 1
    return {
        'corpus_version': CORPUS_VERSION,
        'purpose': 'nonenzymatic_methodology_candidate_pool_not_a_reviewed_benchmark',
        'sources': [{'name': source_name, 'sha256': source_sha, 'rows': source_rows}],
        'family_counts': families,
        'records': records,
    }
