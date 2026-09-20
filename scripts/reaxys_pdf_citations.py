"""Extract the citation and condition layer from a Reaxys PDF export.

A PDF export renders structures as images, so it cannot build a candidate pool on
its own. Use it to recover per-reference conditions, yields and full citations, and
join them onto an RD File export by Reaxys reaction ID.

Output goes under data/local/ by default: the export is licensed data.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from bioreaction_atlas.reaxys_pdf import parse_export, summarize  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pdf_path')
    parser.add_argument('--out', default='data/local/pools/reaxys_citations.json')
    args = parser.parse_args()

    try:
        from pypdf import PdfReader
    except ImportError:
        raise SystemExit("pypdf is required: pip install -e '.[pdf]'")

    reader = PdfReader(args.pdf_path)
    text = '\n'.join((page.extract_text() or '') for page in reader.pages)
    records = parse_export(text)
    if not records:
        raise SystemExit('No "Rx-ID:" entries found. Confirm this is a Reaxys reaction export.')

    report = summarize(records)
    print(f"{report['reactions']} reactions, {report['condition_rows']} condition rows, "
          f"{report['rows_with_a_citation']} with a parsed citation")
    print(f"{report['distinct_journals']} distinct journals; years {report['year_range'][0]}-{report['year_range'][1]}")
    for journal, count in report['top_journals'].items():
        print(f'  {count:5d}  {journal}')

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'summary': report, 'records': records}, ensure_ascii=False, indent=2) + '\n')
    print(f'\nWrote {out}.')
    print('Structures are images in this format; export the same query as RD File to get reaction SMILES,')
    print('then join these rows on reaxys_reaction_id.')


if __name__ == '__main__':
    main()
