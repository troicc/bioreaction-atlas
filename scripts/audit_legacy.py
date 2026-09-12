"""Read an existing public legacy CSV locally; emit aggregate diagnostics only.

Not a scientific benchmark. Does not promote legacy records to checked curation.
"""
import argparse
import csv
import hashlib
from collections import Counter
from pathlib import Path
from bioreaction_atlas.chemistry import canonical_reaction, fingerprint, PARAMETERS
from bioreaction_atlas.curation import write_json

p = argparse.ArgumentParser()
p.add_argument('csv')
p.add_argument('--out', required=True)
a = p.parse_args()
raw = Path(a.csv).read_bytes()
expected_sha256 = 'abe6bd9f0c1dcc3487b6a2a595d427b70c6714b9a2bfd1c195e50b702ffe9245'
if hashlib.sha256(raw).hexdigest() != expected_sha256:
    p.error('输入散列不匹配已核查的固定V6文件；先核查来源与版本，不自动沿用旧提交信息。')
rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
unique, failures = set(), []
for i, row in enumerate(rows, 2):
    reaction = row.get('cannonical_reactions') or row.get('reaction_smiles') or ''
    try:
        canonical = canonical_reaction(reaction)
        if not fingerprint(canonical):
            raise ValueError('zero net fingerprint')
        unique.add(canonical)
    except ValueError as e:
        failures.append({'csv_row': i, 'reason': str(e)})
write_json(a.out, {
    'source': 'EnzymeEngineeringDB protein-evolution-database_V6.csv',
    'commit': 'bae30c9b45cb8a4eab1d6facd9314994f086cf9b',
    'sha256': hashlib.sha256(raw).hexdigest(), 'raw_rows': len(rows),
    'distinct_nonempty_dois': len({r['doi'] for r in rows if r.get('doi')}),
    'fingerprintable_rows': len(rows)-len(failures), 'unique_canonical_reactions': len(unique),
    'cofactor_counts': dict(Counter(r.get('cofactor', '') for r in rows)),
    'failures': failures, 'parameters': PARAMETERS,
    'interpretation': '技术可解析性检查，不是论文级人工核查、领域覆盖率或模型效果。未复制原始数据到发行目录。',
})
print(f'{len(rows)} rows; {len(unique)} unique parseable nonzero reactions; {len(failures)} failures')
