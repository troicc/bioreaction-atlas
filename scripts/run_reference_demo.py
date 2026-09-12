"""Reproducible real-data smoke run, explicitly not a discovery benchmark."""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
from bioreaction_atlas.corpus import import_references, encode_corpus, find_neighbors, load_index, json_hash
from bioreaction_atlas.curation import write_json
from bioreaction_atlas.maps import render_map
from bioreaction_atlas.cards import write_cards


def main():
    from rdkit import RDLogger
    RDLogger.DisableLog('rdApp.warning')  # Repeated isolated-hydrogen warnings; errors remain enabled.
    p = argparse.ArgumentParser()
    p.add_argument('--legacy', required=True)
    p.add_argument('--assets', default='data/local/public')
    p.add_argument('--reference-size', type=int, default=2000)
    p.add_argument('--backends', nargs='+', default=['morgan', 'substrate', 'drfp', 'rxnfp'])
    p.add_argument('--work', default='data/local/reference_demo')
    p.add_argument('--out', default='outputs/bioreaction_atlas_v02/reference_demo')
    a = p.parse_args()
    work, output = Path(a.work), Path(a.out)
    assets = Path(a.assets)
    corpus = import_references(a.legacy, assets/'schneider50k.tsv', a.reference_size)
    write_json(work/'corpus.json', corpus)
    reports = {}
    for backend in a.backends:
        started = time.monotonic()
        index_dir = work/backend
        # Reuse only the exact input, encoder configuration and saved matrix.
        existing = None
        if (index_dir/'index.json').exists():
            info, _ = load_index(index_dir)
            if info['corpus_sha256'] == json_hash(corpus):
                from bioreaction_atlas.encoders import Encoder
                if info['parameters'] == Encoder(backend, assets/'rxnfp').parameters:
                    existing = info
        info = existing or encode_corpus(corpus, index_dir, backend, assets/'rxnfp', allow_unreviewed=True, batch_size=16)
        # Deterministic illustrative enzyme query. It is a retrieved legacy record, not a prediction.
        seed = next(r for r in info['entries'] if r['domain'] == 'enzyme_reference')
        result = find_neighbors(index_dir, seed['reaction_smiles'], top_k=5, model_dir=assets/'rxnfp', domain='patent_reference')
        result['query_reference'] = seed
        write_json(output/backend/'neighbors.json', result)
        write_cards(result, output/backend/'cards')
        reports[backend] = {'unique_reactions': len(info['entries']),
                            'domains': dict(Counter(r['domain'] for r in info['entries'])),
                            'excluded_source_rows': len(info['excluded']),
                            'exclusion_reasons': dict(Counter(r['reason'] for r in info['excluded'])),
                            'wall_seconds': round(time.monotonic()-started, 2),
                            'parameters': info['parameters'], 'corpus_sha256': info['corpus_sha256'],
                            'top_neighbor_sources': [h['evidence'][0]['source'] for h in result['hits']]}
        print(f'Completed {backend}: {reports[backend]["unique_reactions"]} reactions', flush=True)
    map_backend = 'rxnfp' if 'rxnfp' in a.backends else a.backends[0]
    reports['map'] = render_map(work/map_backend, output/'map', method='tsne')
    write_json(output/'technical_run.json', reports)
    lines = ['# Public-reference technical run', '',
             'This run uses real public source structures. It is not a historical discovery benchmark or evidence that a new enzyme reaction is feasible.', '',
             f'EnzymeEngineeringDB V6 rows: 1,342. Independently hash-sampled patent reference rows: {a.reference_size:,}.', '',
             '| Encoder | Unique enzyme references | Unique patent references | Excluded source rows |', '|---|---:|---:|---:|']
    for backend in a.backends:
        r = reports[backend]
        lines.append(f"| {backend} | {r['domains'].get('enzyme_reference',0)} | {r['domains'].get('patent_reference',0)} | {r['excluded_source_rows']} |")
    lines += ['', 'Source rows are canonicalized and grouped within each domain, with all original evidence retained. Exclusions differ by encoder and are reported; this run does not compare discovery metrics on unequal pools.', '',
              '[Open the offline interactive RXNFP map](map/reaction_map.html)' if map_backend == 'rxnfp' else '[Open the offline map](map/reaction_map.html)', '',
              '![Reaction map](map/reaction_map.png)', '',
              'The map is a joint t-SNE projection, not the original TMAP layout. Nearest neighbors are computed in the original representation space. Projection trustworthiness is a geometry diagnostic, not a scientific success metric.', '',
              'Evidence cards show a deterministic legacy enzyme query against patent references. They preserve review state and missing conditions; they do not claim new-to-nature candidates.', '',
              'Strict historical evaluation remains gated on manually checked dates, experimental sources, candidate groups and held-out discoveries. The public reference importer intentionally cannot pass those gates.']
    (output/'README.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    main()
