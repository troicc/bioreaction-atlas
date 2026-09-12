"""Report classification-label coverage, without calling it chemistry coverage."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--assets', default='data/local/public')
p.add_argument('--index', default='data/local/reference_demo/rxnfp/index.json')
p.add_argument('--out', default='research/reference_coverage_audit.json')
a = p.parse_args()
assets = Path(a.assets)
raw = (assets / 'schneider50k.tsv').read_bytes()
counts = Counter(r['rxn_class'] for r in csv.DictReader(raw.decode().splitlines(), delimiter='\t'))
names = json.loads((assets / 'rxnclass2name.json').read_text())
index = json.loads(Path(a.index).read_text())
patents = [e for e in index['entries'] if e['domain'] == 'patent_reference']
sample_counts = Counter(e['label'] for row in patents for e in row['evidence'])
result = {
    'audited_on': '2026-09-10',
    'source_file': str(assets / 'schneider50k.tsv'),
    'source_sha256': hashlib.sha256(raw).hexdigest(),
    'source_rows': sum(counts.values()),
    'source_distinct_class_labels': len(counts),
    'source_rows_per_class_min': min(counts.values()),
    'source_rows_per_class_max': max(counts.values()),
    'indexed_patent_source_rows': sum(sample_counts.values()),
    'indexed_unique_patent_structures': len(patents),
    'indexed_distinct_class_labels': len(sample_counts),
    'classes': [{'label': label, 'name': names.get(label), 'full_rows': count,
                 'sample_rows': sample_counts[label]} for label, count in sorted(counts.items())],
    'interpretation': 'Counts describe a selected classification benchmark and our local sample. '
                      'All 50 benchmark labels being present does not establish coverage of organic chemistry, '
                      'catalytic mechanisms, journal methods, or transferable enzyme reactions. '
                      'Reference imports are not manually checked nonenzymatic precedents.'
}
Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k: v for k, v in result.items() if k != 'classes'}, ensure_ascii=False))
