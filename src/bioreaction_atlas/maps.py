"""Standalone scientific plots; retrieval always uses the original feature space."""
import os
from pathlib import Path
import numpy as np
from .corpus import load_index, sha
from .curation import write_json
from .map_view import attach_diagrams, write_interactive_map


def render_map(index_dir, out_dir, method='tsne', seed=17):
    if method not in ('pca', 'tsne'):
        raise ValueError('Map method must be pca or tsne')
    info, matrix = load_index(index_dir)
    n = len(matrix)
    if not 3 <= n <= 10000:
        raise ValueError('Map expects 3–10,000 unique reactions; use a declared sample for larger corpora')
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE, trustworthiness
    from sklearn.neighbors import NearestNeighbors
    # Normalize cosine vectors before Euclidean embedding. Binary DRFP uses Jaccard distances.
    metric = info['parameters']['metric']
    x = matrix / np.linalg.norm(matrix, axis=1, keepdims=True) if metric == 'cosine' else matrix
    if method == 'pca':
        reducer = PCA(n_components=2, random_state=seed, svd_solver='randomized')
        coords = reducer.fit_transform(x)
        projection_details = {'explained_variance_ratio': reducer.explained_variance_ratio_.tolist()}
    else:
        perplexity = min(30, max(2, (n-1)/3))
        # Jaccard on bit vectors agrees with the DRFP retrieval metric.
        distance = 'cosine' if metric == 'cosine' else 'jaccard'
        reducer = TSNE(n_components=2, perplexity=perplexity, init='pca', random_state=seed,
                       learning_rate='auto', metric=distance, max_iter=1000, n_jobs=4)
        coords = reducer.fit_transform(x if distance != 'jaccard' else x.astype(bool))
        projection_details = {'perplexity': perplexity, 'iterations': 1000, 'distance': distance,
                              'kl_divergence': float(reducer.kl_divergence_)}
    k = min(5, n-1)
    nn_metric = 'cosine' if metric == 'cosine' else 'jaccard'
    features = matrix if metric == 'cosine' else matrix.astype(bool)
    neighbors = NearestNeighbors(n_neighbors=k+1, metric=nn_metric, algorithm='brute', n_jobs=4).fit(features)
    distances, ids = neighbors.kneighbors(features)
    edges, seen_edges = [], set()
    for i in range(n):
        for j, d in zip(ids[i], distances[i]):
            pair = tuple(sorted((i, int(j))))
            if i != j and pair not in seen_edges:
                seen_edges.add(pair)
                edges.append({'source': info['entries'][pair[0]]['record_id'], 'target': info['entries'][pair[1]]['record_id'],
                              'distance_in_original_space': float(d)})
    trust = None
    # This diagnoses projection fidelity, not reaction feasibility or model utility.
    if n <= 4000 and n > 12:
        trust = float(trustworthiness(features, coords, n_neighbors=5, metric=nn_metric))
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for row, xy in zip(info['entries'], coords, strict=True):
        first = row['evidence'][0]
        records.append({'record_id': row['record_id'], 'x': float(xy[0]), 'y': float(xy[1]),
                        'domain': row['domain'], 'source': first['source'],
                        'source_label': first.get('label', ''), 'cofactor': first.get('context', {}).get('metal_cofactor') or 'not specified',
                        'evidence_rows': len(row['evidence']), 'reaction_smiles': row['reaction_smiles'],
                        'evidence': row['evidence']})
    attach_diagrams(records, folder)
    mapdata = {'backend': info['parameters']['backend'], 'projection': method, 'seed': seed,
               'index_sha256': sha((Path(index_dir)/'index.json').read_bytes()),
               'projection_details': projection_details, 'trustworthiness_at_5': trust,
               'interpretation': '2D visualization of the selected corpus, not a fixed chemical coordinate system or feasibility map. kNN edges use original-space distances.',
               'records': records, 'knn_edges': edges}
    write_json(folder/'map_data.json', mapdata)
    colors = {'enzyme_reference': '#167D8D', 'patent_reference': '#C58835',
              'enzymatic': '#00796B', 'nonenzymatic': '#8056B3', 'control': '#888888'}
    import plotly.graph_objects as go
    figure = go.Figure()
    for domain in sorted({r['domain'] for r in records}):
        rows = [r for r in records if r['domain'] == domain]
        figure.add_trace(go.Scatter(x=[r['x'] for r in rows], y=[r['y'] for r in rows], mode='markers', name=domain,
                         marker={'size': 6 if 'enzyme' in domain or domain == 'enzymatic' else 4,
                                 'color': colors.get(domain, '#666666'), 'opacity': .65},
                         customdata=[r['record_id'] for r in rows], hoverinfo='none'))
    figure.update_layout(template='plotly_white', autosize=True, height=620,
                         title=f"{info['parameters']['backend'].upper()} reaction map — {n:,} unique reactions<br><sup>{method.upper()} projection; imported references are not manually reviewed. Click legend to filter.</sup>",
                         xaxis_title=f'{method.upper()} 1', yaxis_title=f'{method.upper()} 2',
                         legend={'orientation': 'h', 'y': -.13}, margin={'b': 95})
    write_interactive_map(figure, records, folder/'reaction_map.html')
    os.environ.setdefault('MPLCONFIGDIR', str(folder.resolve()/'.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)
    for domain in sorted({r['domain'] for r in records}):
        indices = [i for i, r in enumerate(records) if r['domain'] == domain]
        ax.scatter(coords[indices, 0], coords[indices, 1], s=9, alpha=.65, label=f'{domain} (n={len(indices)})',
                   c=colors.get(domain, '#666666'), linewidths=0)
    ax.set(title=f"{info['parameters']['backend'].upper()} | {method.upper()} | {n:,} unique reactions",
           xlabel=f'{method.upper()} 1', ylabel=f'{method.upper()} 2')
    ax.legend(frameon=False, loc='best')
    fig.suptitle('Imported reference data. Spatial proximity does not establish enzyme feasibility.', fontsize=10)
    fig.savefig(folder/'reaction_map.png', dpi=180)
    plt.close(fig)
    return {'reactions': n, 'projection': method, 'trustworthiness_at_5': trust, 'output': str(folder)}
