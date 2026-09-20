"""Bulk-import non-enzymatic methodology reactions into a candidate corpus.

Takes a CSV exported from Reaxys, SciFinder, ORD or assembled by hand, and writes a
corpus JSON that the existing encoders consume. Records are marked `imported`: they
carry a literature identifier but have not passed primary-source review, exactly like
the pinned patent references.

What this deliberately does NOT do:
  - infer a mechanism. `mechanism` stays empty; the family label records why the
    reaction was imported, not how it works.
  - promote a publication year to a verified earliest public date. A year is kept in
    `source_year`; `first_public_date` stays null unless an explicit, evidenced
    YYYY-MM-DD is supplied.
"""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.corpus import sha  # noqa: E402
from bioreaction_atlas.curation import write_json  # noqa: E402
from bioreaction_atlas.methodology import OPTIONAL, REQUIRED, build_corpus, build_records  # noqa: E402

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('csv_path')
    parser.add_argument('--out', required=True)
    parser.add_argument('--prefix', default='METH', help='record ID prefix, e.g. CARB for carbene')
    parser.add_argument('--report', help='write the skipped-row report here')
    args = parser.parse_args()

    raw = Path(args.csv_path).read_bytes()
    rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    if not rows:
        raise SystemExit('Export is empty')
    unknown = set(rows[0]) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        print(f'Note: ignoring unrecognized columns: {", ".join(sorted(unknown))}')

    records, skipped = build_records(rows, args.prefix)
    if not records:
        raise SystemExit('No importable rows; see the skipped report')

    corpus = build_corpus(records, Path(args.csv_path).name, sha(raw), len(rows))
    families = corpus['family_counts']
    write_json(args.out, corpus)
    print(f'Imported {len(records)} reactions, skipped {len(skipped)}.')
    for family, count in sorted(families.items(), key=lambda x: -x[1]):
        print(f'  {count:5d}  {family}')
    if skipped:
        print('\nFirst skipped rows:')
        for item in skipped[:5]:
            print(f"  row {item['row']}: {item['reason']}")
    if args.report:
        write_json(args.report, {'skipped': skipped, 'imported': len(records)})
    print(f'\nWrote {args.out}. Records are "imported": a literature identifier, not a reviewed procedure.')


if __name__ == '__main__':
    main()
