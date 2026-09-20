"""Extract the citation and condition layer from a Reaxys PDF export.

A PDF export renders structures as images, so it cannot supply reaction SMILES and
cannot build a pool on its own. What it does carry, and carry well, is one row per
literature condition: the yield, the full condition sentence, and a complete
citation with journal, volume, year and pages.

That is the provenance layer the coverage protocol needs, so this reader exists to
be joined onto an RD File export by Reaxys reaction ID. Extracted records stay
local: the export is licensed data, and only aggregates are shareable.
"""
import re

RX_ID = re.compile(r'Rx-ID:\s*(\d+)')
# A condition row opens with its yield, or with "With ..." when no yield is given.
YIELD_ROW = re.compile(r'^\s*(\d+(?:\.\d+)?)\s*%\s+(.*)$')
CITATION = re.compile(r';\s*(?P<journal>[A-Z][A-Za-z&.\-\' ]{4,70});\s*vol\.\s*(?P<volume>[^;]+);'
                      r'(?:\s*nb\.\s*(?P<issue>[^;]+);)?\s*\((?P<year>\d{4})\);\s*p\.\s*(?P<pages>[\d\s\-]+)')
NOISE = re.compile(r'^(Copyright ©|Disclaimer:|View in Reaxys|Yield Conditions|\d+/\d+\s+\d{4}-)')
# The author list that ends a condition blob and opens its citation. Anchored to the
# end of the slice, because the final author is followed by the journal separator
# rather than by another semicolon.
AUTHOR = r"[A-ZÀ-Ý][\w'\-]+,\s*[A-ZÀ-Ý][\w.'\- ]*"
AUTHORS_TAIL = re.compile(rf"(?:{AUTHOR};\s*)*{AUTHOR}\s*$")


def _citation_start(blob, journal_at):
    """Back up from the journal to where the author list begins, when there is one."""
    match = AUTHORS_TAIL.search(blob[:journal_at])
    return match.start() if match else journal_at


def _clean(lines):
    return [ln for ln in lines if ln.strip() and not NOISE.match(ln.strip())]


def parse_export(text):
    """Return one record per reaction, each carrying its literature condition rows."""
    parts = RX_ID.split(text)
    records = []
    for rx_id, body in zip(parts[1::2], parts[2::2]):
        conditions, current = [], None
        for line in _clean(body.splitlines()):
            stripped = line.strip()
            match = YIELD_ROW.match(stripped)
            if match:
                if current:
                    conditions.append(current)
                current = {'yield_percent': match.group(1), 'text': [match.group(2)]}
            elif current is not None:
                current['text'].append(stripped)
        if current:
            conditions.append(current)
        parsed = []
        for condition in conditions:
            blob = ' '.join(condition['text'])
            citation = CITATION.search(blob)
            cut = _citation_start(blob, citation.start()) if citation else None
            entry = {'yield_percent': condition['yield_percent'],
                     'conditions_raw': blob[:cut].strip(' ;,') if citation else blob.strip(),
                     'citation': blob[cut:].strip(' ;,') if citation else None,
                     'journal': None, 'year': None, 'pages': None, 'volume': None}
            if citation:
                entry.update(journal=citation.group('journal').strip(),
                             year=citation.group('year'),
                             volume=citation.group('volume').strip(),
                             pages=re.sub(r'\s+', ' ', citation.group('pages')).strip())
            parsed.append(entry)
        records.append({'reaxys_reaction_id': rx_id, 'conditions': parsed,
                        # Structures are rendered images in this format.
                        'reaction_smiles': None})
    return records


def summarize(records):
    conditions = [c for r in records for c in r['conditions']]
    years = sorted(c['year'] for c in conditions if c['year'])
    journals = {}
    for condition in conditions:
        if condition['journal']:
            journals[condition['journal']] = journals.get(condition['journal'], 0) + 1
    return {
        'reactions': len(records),
        'condition_rows': len(conditions),
        'rows_with_a_citation': sum(1 for c in conditions if c['citation']),
        'distinct_journals': len(journals),
        'year_range': [years[0], years[-1]] if years else None,
        'top_journals': dict(sorted(journals.items(), key=lambda kv: -kv[1])[:10]),
        'note': 'A PDF export carries no machine-readable structures; join to an RD File by reaxys_reaction_id.',
    }
