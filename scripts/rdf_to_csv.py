"""Convert an RD File reaction export into the methodology import CSV.

Run with --list-fields first. Vendor data-field names differ between databases
and subscriptions, so the mapping is decided by looking at the actual export
rather than assumed.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.activation import FAMILIES  # noqa: E402
from bioreaction_atlas.methodology import OPTIONAL, REQUIRED  # noqa: E402
from bioreaction_atlas.rdf import (  # noqa: E402
    REAXYS_COLUMNS, explode_variations, field_summary, guess_mapping, read_rdf,
)

COLUMNS = list(REQUIRED) + [c for c in OPTIONAL if c != 'loading']


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('rdf_path')
    parser.add_argument('--family', help=f'activation family for every row; one of: {", ".join(FAMILIES)}')
    parser.add_argument('--out', help='write the import CSV here')
    parser.add_argument('--list-fields', action='store_true',
                        help='print the data fields this file actually carries, then exit')
    parser.add_argument('--map', action='append', default=[], metavar='COLUMN=FIELD',
                        help='override a mapping, e.g. --map source_doi="Citation DOI"')
    parser.add_argument('--no-variations', action='store_true',
                        help='keep one row per reaction instead of one per literature variation')
    parser.add_argument('--exclude-reviews', action='store_true',
                        help='drop variations whose citation is a review rather than primary literature')
    args = parser.parse_args()

    text = Path(args.rdf_path).read_text(errors='replace')
    rows, failures = read_rdf(text)
    print(f'Read {len(rows)} reactions; {len(failures)} records failed to parse.')
    for failure in failures[:5]:
        print(f"  record {failure['record']}: {failure['reason']}")

    if not args.no_variations:
        rows = explode_variations(rows)
        print(f'Exploded to {len(rows)} literature variations.')
        if args.exclude_reviews:
            before = len(rows)
            rows = [r for r in rows if (r.get('document_type') or '').lower() != 'review']
            print(f'Dropped {before - len(rows)} review citations; {len(rows)} remain.')

    if not rows:
        raise SystemExit('No parseable reactions. Confirm the export came from the Reactions tab, not Documents.')

    summary = field_summary(rows)
    mapping = guess_mapping(rows)
    if not args.no_variations:
        mapping.update({c: f for c, f in REAXYS_COLUMNS.items() if any(f in r for r in rows)})
    if args.list_fields:
        print(f'\n{len(summary)} data fields present:\n')
        for name, (count, example) in summary.items():
            print(f'  {count:5d}/{len(rows)}  {name}')
            print(f'         e.g. {example[:90]}')
        print('\nMapping that will be used (verify before trusting it):')
        for column, field in mapping.items():
            print(f'  {column:18s} <- {field}')
        print('\nOverride anything wrong with --map column="Field Name".')
        return

    if not args.family:
        raise SystemExit('--family is required when writing a CSV')
    if args.family not in FAMILIES:
        raise SystemExit(f'Unknown family. Choose one of: {", ".join(FAMILIES)}')
    if not args.out:
        raise SystemExit('--out is required when writing a CSV')

    for override in args.map:
        if '=' not in override:
            raise SystemExit(f'Bad --map value: {override}')
        column, field = override.split('=', 1)
        column = column.strip()
        if column not in COLUMNS:
            raise SystemExit(f'Unknown column {column}; valid: {", ".join(COLUMNS)}')
        mapping[column] = field.strip()

    print('\nMapping used:')
    for column in COLUMNS:
        if column in mapping:
            print(f'  {column:18s} <- {mapping[column]}')
    unmapped = [c for c in COLUMNS if c not in mapping and c not in ('reaction_smiles', 'family')]
    if unmapped:
        print(f'  (left empty: {", ".join(unmapped)})')
    if 'source_doi' not in mapping:
        print('\nWARNING: no DOI field was mapped. Every row will be skipped at import, '
              'because a literature identifier is required. Use --list-fields and --map.')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            record = {'reaction_smiles': row['reaction_smiles'], 'family': args.family}
            for column, field in mapping.items():
                value = row.get(field, '')
                # Keep it on one line; the importer stores text, not formatted blocks.
                record[column] = ' '.join(str(value).split()) if value not in (None, '') else ''
            writer.writerow({c: record.get(c, '') for c in COLUMNS})
            written += 1
    print(f'\nWrote {written} rows to {out}.')
    print('A publication year here is a year, never a verified public date. Import with:')
    print(f'  PYTHONPATH=src .venv/bin/python scripts/import_methodology.py {out} '
          f'--out data/local/pools/{args.family}.json --prefix {args.family[:4].upper()}')


if __name__ == '__main__':
    main()
