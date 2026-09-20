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
            'reaction_name', 'document_type', 'first_public_date', 'date_evidence', 'notes')

# A retracted paper is not evidence. Reviews and conference abstracts are search
# leads: the protocol requires a primary experimental source, so they are kept out
# of the pool by default and can be re-admitted deliberately.
REJECTED_DOCUMENT_TYPES = {'retracted article', 'review', 'conference paper'}
CONDITION_COLUMNS = ('catalyst', 'reagents', 'solvent', 'temperature_c', 'time_h', 'loading')


def build_records(rows, prefix='METH', screen=True, reject_document_types=REJECTED_DOCUMENT_TYPES):
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

        document_type = (row.get('document_type') or '').strip()
        if reject_document_types and document_type.lower() in reject_document_types:
            skipped.append({'row': n, 'reason': f'document type not primary evidence: {document_type}'})
            continue

        # The label is always recorded. Screening only decides whether an off-family
        # row is dropped: an evaluation pool needs the mixture, and a pool filtered to
        # 100% in-family makes any later retrieval measurement degenerate.
        verdict, reason = family_screen(raw, family, context.get('catalyst'))
        context['family_screen'] = reason if verdict else ('unscreened: ' + reason if verdict is None else reason)
        context['in_family'] = verdict
        if screen and verdict is False:
            skipped.append({'row': n, 'reason': f'off-family: {reason}'})
            continue

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
            'document_type': document_type or None,
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
