# Reproduce the encoder-agreement study

The aggregate tables describe the pinned 639-query/1,988-candidate analysis. Full regeneration requires the original input file and four encoded indices. Third-party records and weights are not bundled with the Git snapshot.

## Existing workspace

From the project root:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/ai4c-matplotlib .venv/bin/python scripts/analyze_encoder_consistency.py
.venv/bin/python scripts/write_consistency_report.py
.venv/bin/python -m pytest -q
```

The first command verifies vector hashes, corpus identity, structural view and common entry provenance before scoring. It overwrites aggregate results under `outputs/encoder_consistency/` and detailed generated artifacts under `data/local/encoder_consistency/`. It does not edit original source records or require a model/network call.

## Fresh environment and source acquisition

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,research,rxnfp]'
.venv/bin/python scripts/fetch_public_assets.py
```

The downloader uses pinned RXNFP commit `6fd48f4927c2178555cc5d71dbfb225fb178f43c`, verifies size and Git blob hashes, and writes a SHA256 manifest. It downloads official weights, vocabulary, configuration, Schneider50k and class names. `requirements.lock.txt` records the original workspace dependency snapshot; summary metadata records numerical-library versions. Investigate cross-version numerical differences rather than silently treating them as identical.

Obtain `protein-evolution-database_V6.csv` from the [EnzymeEngineeringDB repository at commit bae30c9b45cb8a4eab1d6facd9314994f086cf9b](https://github.com/fhalab/EnzymeEngineeringDB/tree/bae30c9b45cb8a4eab1d6facd9314994f086cf9b), following applicable access and data terms. Its expected SHA256 is:

```text
abe6bd9f0c1dcc3487b6a2a595d427b70c6714b9a2bfd1c195e50b702ffe9245
```

Save the obtained file as `data/local/protein-evolution-database_V6.csv`, then run:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_reference_demo.py \
  --legacy data/local/protein-evolution-database_V6.csv
PYTHONPATH=src MPLCONFIGDIR=/tmp/ai4c-matplotlib .venv/bin/python scripts/analyze_encoder_consistency.py
.venv/bin/python scripts/write_consistency_report.py
```

The reference runner also regenerates a local map and illustrative cards. Its patent sample uses seed 17 and 2,000 rows. Do not substitute another corpus and report results under the original label. Common-pool exclusions and configuration are part of the result.

## Artifact map

| Artifact | Contents |
|---|---|
| `outputs/encoder_consistency/summary.json` | Aggregate metrics, exclusions, source/vector/code hashes, environment and rounding sensitivity |
| `outputs/encoder_consistency/pair_summary.csv` | Six-pair comparisons in each of three settings |
| `outputs/encoder_consistency/*_overlap.*` | Top-k overlap curves |
| `outputs/encoder_consistency/*_heatmaps.*` | Top-10 agreement and full-pool Spearman |
| `outputs/encoder_consistency/*_distribution.*` | Query-level cumulative distributions |
| `data/local/encoder_consistency/*_scores.npz` | Rounded score matrices keyed by encoder |
| `data/local/encoder_consistency/*_pool.json` | Matrix row/column ID ordering |
| `data/local/encoder_consistency/*_per_query.csv` | Query-pair metrics, sources and eligibility counts |
| `data/local/encoder_consistency/cases/` | Selected reactions, full evidence and SVG cards |

Score matrices contain the full domain pool. Apply self/shared-source exclusions with `allowed_candidates` and original common entries before reproducing within-enzyme statistics. All formal comparisons use identical eligibility across encoders.

## Checks and practical limits

Synthetic tests verify tie expectations, undefined correlations, common-pool alignment, source normalization and exclusions. Existing tests cover imports, fingerprints, matrix corruption, bilingual intake and historical-date gates. The RXNFP integration test is skipped until local official assets exist; a skipped integration test is not a verified model reproduction.

Source-macro summaries reduce domination by large publication groups but are not independence-adjusted confidence intervals. This analysis uses no discovery-event labels, prospective outcomes or verified nonenzymatic correspondence set. Numerical reproduction establishes this descriptive result only.
