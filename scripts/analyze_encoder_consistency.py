"""Reuse saved indices to produce agreement tables, figures and local evidence cards."""
import argparse
import csv
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy

from bioreaction_atlas.cards import draw_reaction
from bioreaction_atlas.consistency import BACKENDS, analyze, load_common_pool, source_ids
from bioreaction_atlas.corpus import json_hash, sha
from bioreaction_atlas.curation import write_json

LABELS = {'morgan': 'Morgan difference', 'substrate': 'Substrate Morgan', 'drfp': 'DRFP', 'rxnfp': 'RXNFP'}
COLORS = ['#176B87', '#B55B32', '#578443', '#9366A2', '#A08228', '#C45470']


def write_rows(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in row.items()})


def save_figure(fig, folder, name):
    for ext in ('png', 'svg'):
        fig.savefig(folder / f'{name}.{ext}', dpi=180, bbox_inches='tight')
    plt.close(fig)


def figures(result, rows, output, prefix):
    fig, ax = plt.subplots(figsize=(9, 5.6), layout='constrained')
    for p, color in zip(result['pairs'], COLORS):
        ax.plot(result['ks'], [p['metrics'][f'expected_overlap_at_{k}']['mean'] for k in result['ks']],
                marker='o', color=color, label=f"{LABELS[p['encoder_a']]} / {LABELS[p['encoder_b']]}")
    random = [result['pairs'][0]['metrics'][f'random_overlap_at_{k}']['mean'] for k in result['ks']]
    ax.plot(result['ks'], random, '--', color='#777777', label='Independent uniform lists')
    ax.set(xlabel='Retrieved candidates (k)', ylabel='Mean expected shared fraction', ylim=(0, 1),
           title=f"Retrieval agreement: {prefix.replace('_', ' ')}\n{result['query_count']} common enzyme queries; independent boundary-tie permutations")
    ax.legend(fontsize=8, ncols=2, loc='upper left')
    ax.grid(alpha=.15)
    save_figure(fig, output, f'{prefix}_overlap')

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9), layout='constrained')
    for ax, metric, title, limits in zip(axes, ['expected_overlap_at_10', 'spearman'],
            ['Mean expected top-10 overlap', 'Mean full-pool Spearman'], [(0, 1), (-1, 1)]):
        matrix = np.full((4, 4), np.nan)
        for p in result['pairs']:
            i, j = BACKENDS.index(p['encoder_a']), BACKENDS.index(p['encoder_b'])
            matrix[i, j] = matrix[j, i] = p['metrics'][metric]['mean']
        im = ax.imshow(np.ma.masked_invalid(matrix), vmin=limits[0], vmax=limits[1], cmap='viridis')
        for i in range(4):
            for j in range(4):
                ax.text(j, i, '—' if i == j else f'{matrix[i,j]:.3f}', ha='center', va='center',
                        color='black' if i == j or matrix[i,j] > (limits[0] + .65 * (limits[1]-limits[0])) else 'white')
        ax.set(xticks=range(4), yticks=range(4), xticklabels=BACKENDS, yticklabels=BACKENDS, title=title)
        fig.colorbar(im, ax=ax, shrink=.7)
    fig.suptitle(f"{prefix.replace('_', ' ')}: same queries and candidate eligibility across encoders")
    save_figure(fig, output, f'{prefix}_heatmaps')

    fig, ax = plt.subplots(figsize=(8.5, 5.1), layout='constrained')
    for p, color in zip(result['pairs'], COLORS):
        values = sorted(r['expected_overlap_at_10'] for r in rows
                        if (r['encoder_a'], r['encoder_b']) == (p['encoder_a'], p['encoder_b']))
        ax.step(values, np.arange(1, len(values)+1) / len(values), where='post', color=color,
                label=f"{p['encoder_a']} / {p['encoder_b']}")
    ax.set(xlabel='Expected top-10 shared fraction per query', ylabel='Cumulative fraction of queries',
           xlim=(0, 1), ylim=(0, 1), title='Query-level disagreement distribution')
    ax.legend(fontsize=8, loc='lower right')
    ax.grid(alpha=.15)
    save_figure(fig, output, f'{prefix}_distribution')


def cases(result, scores, queries, candidates, local, count=3):
    folder = local / 'cases'
    folder.mkdir(parents=True, exist_ok=True)
    used_sources, selected = set(), []
    positions = {q['record_id']: n for n, q in enumerate(queries)}
    for q in result['query_disagreement']:
        if used_sources.intersection(q['query_sources']):
            continue
        used_sources.update(q['query_sources'])
        selected.append(q)
        if len(selected) == count:
            break
    lines = ['# Disagreement evidence cards', '',
             'Selection: ascending mean expected top-10 overlap across all six encoder pairs; ID breaks ties. '
             'After each selection, skip queries sharing any source with an earlier case. '
             'These are structural observations from imported records, not reviewed precedent matches.', '']
    records = []
    for i, selected_query in enumerate(selected, 1):
        pos = positions[selected_query['query_id']]
        q = queries[pos]
        draw_reaction(q['reaction_smiles'], folder / f'case_{i}_query.svg')
        lines += [f'## Case {i}: {q["record_id"]}', '', f'![Query](case_{i}_query.svg)', '',
                  f'Mean expected top-10 overlap: {selected_query["mean_expected_overlap"]:.4f}.', '',
                  'Sources: ' + '; '.join(sorted(source_ids(q))), '', '```text', q['reaction_smiles'], '```', '']
        record = {'selection': selected_query, 'query': q, 'neighbors': {}}
        for b, matrix in scores.items():
            order = np.argsort(-matrix[pos], kind='stable')[:10]
            record['neighbors'][b] = [{'similarity': float(matrix[pos, n]), **candidates[n]} for n in order]
            top = candidates[order[0]]
            name = f'case_{i}_{b}.svg'
            draw_reaction(top['reaction_smiles'], folder / name)
            lines += [f'### {LABELS[b]}: first neighbor', '', f'![{b}]({name})', '',
                      f'Score: {matrix[pos, order[0]]:.6f}; entry: {top["record_id"]}.', '',
                      'Sources: ' + '; '.join(sorted(source_ids(top))), '', '```text', top['reaction_smiles'], '```', '']
        records.append(record)
    write_json(folder / 'cases.json', records)
    (folder / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return [r['selection'] for r in records]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--indices', default='data/local/reference_demo')
    parser.add_argument('--out', default='outputs/encoder_consistency')
    parser.add_argument('--local', default='data/local/encoder_consistency')
    args = parser.parse_args()
    output, local = Path(args.out), Path(args.local)
    output.mkdir(parents=True, exist_ok=True)
    local.mkdir(parents=True, exist_ok=True)
    entries, vectors, provenance = load_common_pool(args.indices)
    configuration = {
        'analysis_version': '1.0', 'ks': [5, 10, 20, 50], 'score_decimals': 6,
        'ranking': 'descending rounded score; stable ascending entry ID for deterministic overlap',
        'expected_overlap': 'sum(p_a * p_b) / k; independent uniform permutations of boundary ties',
        'spearman': 'average ranks on all eligible candidates; constant ranks are undefined',
        'case_selection': 'lowest mean expected overlap@10; ID tie-break; exclude previously represented sources',
        'purpose': 'descriptive representation agreement; no labeled accuracy or historical coverage',
    }
    # Written before scores are computed; this is a reproducible run configuration, not preregistration.
    write_json(output / 'configuration.json', configuration)
    report = {'configuration': configuration, 'provenance': provenance,
              'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
                              'matplotlib': matplotlib.__version__},
              'code_sha256': {p: sha(Path(p).read_bytes()) for p in
                              ['src/bioreaction_atlas/consistency.py', 'scripts/analyze_encoder_consistency.py']},
              'analyses': {}}
    for name, domain, exclude in [('enzyme_to_patent', 'patent_reference', False),
                                  ('enzyme_to_enzyme', 'enzyme_reference', False),
                                  ('enzyme_cross_source', 'enzyme_reference', True)]:
        result, rows, scores, queries, candidates = analyze(entries, vectors, provenance,
                                                          candidate_domain=domain, exclude_shared_source=exclude)
        write_rows(local / f'{name}_per_query.csv', rows)
        np.savez_compressed(local / f'{name}_scores.npz', **scores)
        write_json(local / f'{name}_pool.json', {'queries': [q['record_id'] for q in queries],
                                                'candidates': [c['record_id'] for c in candidates]})
        write_json(local / f'{name}_full.json', result)
        if name == 'enzyme_to_patent':
            report['case_selection'] = cases(result, scores, queries, candidates, local)
        figures(result, rows, output, name)
        report['analyses'][name] = {k: v for k, v in result.items() if k != 'query_disagreement'}
        print(f'{name}: {result["query_count"]} queries; {result["eligible_candidate_range"]} eligible candidates', flush=True)
    report['rounding_sensitivity'] = {}
    for decimals in (5, 7):
        result, *_ = analyze(entries, vectors, provenance, decimals=decimals)
        report['rounding_sensitivity'][str(decimals)] = result['pairs']
    report['local_artifacts_sha256'] = {str(p.relative_to(local)): sha(p.read_bytes())
                                       for p in sorted(local.rglob('*')) if p.is_file()}
    write_json(output / 'summary.json', report)
    with (output / 'pair_summary.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['analysis', 'encoder_a', 'encoder_b', 'queries', 'top10_expected_overlap',
                         'top10_deterministic_overlap', 'spearman', 'source_macro_top10', 'source_macro_spearman'])
        for name, result in report['analyses'].items():
            for p in result['pairs']:
                m = p['metrics']
                writer.writerow([name, p['encoder_a'], p['encoder_b'], p['queries'],
                                 m['expected_overlap_at_10']['mean'], m['overlap_at_10']['mean'], m['spearman']['mean'],
                                 m['expected_overlap_at_10']['source_macro_mean'], m['spearman']['source_macro_mean']])
    print(f'Aggregate results: {output}; detailed local evidence: {local}', flush=True)


if __name__ == '__main__':
    main()
