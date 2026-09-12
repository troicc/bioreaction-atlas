# BioReaction Atlas

**How reliably can public reaction corpora provide verifiable abiotic precedents for new-to-nature biocatalysis?**

BioReaction Atlas studies corpus coverage and the dependence of reaction retrieval on representation choice. The current result is a completed encoder-agreement analysis; discovery-event precedent coverage is the next measurement.

[English technical report](outputs/encoder_consistency/REPORT.md) · [Coverage protocol](research/coverage_protocol_v02.md) · [Reproduce](docs/REPRODUCIBILITY.md) · [中文使用说明](README.zh-CN.md)

## Measured result

On **639 common enzyme-reference reactions** queried against **1,988 common patent-reference reactions**, the six pairs of four representations have mean expected **top-10 overlap of 0.70%-11.07%** and mean full-pool **Spearman correlation of 0.042-0.217**.

| Retrieval setting | Mean expected top-10 overlap across six encoder pairs |
|---|---:|
| Enzyme queries to patent references | 0.70%-11.07% |
| Within the enzyme corpus, self excluded | 42.82%-62.45% |
| Within the enzyme corpus, self and shared publication sources excluded | 16.64%-37.71% |

![Encoder agreement](outputs/encoder_consistency/enzyme_to_patent_heatmaps.png)

Neighborhood selection depends strongly on representation and candidate-pool composition in this fixed collection. This does **not** identify the most accurate encoder or establish the absence of small-molecule precedents. Three selected disagreement cases include a structure/source discrepancy requiring original-SI review. Methods, source-macro sensitivity, boundary ties and limitations are in the [report](outputs/encoder_consistency/REPORT.md); exact values are in [summary.json](outputs/encoder_consistency/summary.json).

## Research scope

The main study separates three questions: does an earlier nonenzymatic literature precedent exist, is a corresponding record present in the frozen corpus, and does retrieval find it? The unit is an independently reviewed discovery event, rather than each mutant or substrate record.

The [v0.2 protocol](research/coverage_protocol_v02.md) defines matching, event-specific date cutoffs, search budgets, unresolved cases and overlapping activation/platform strata. A [five-paper calibration intake](research/coverage_pilot_intake.json) records starting sources and remaining checks. It is not a reviewed benchmark. No discovery-event candidate coverage rate has yet been measured.

The [English research proposal](research/research_proposal_EN.md) explains the contribution. Condition reranking and prospective reaction recommendations remain follow-up questions. Map and collection interfaces support the research workflow.

## Run locally

Python 3.11 or newer. For a fresh environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test,research,rxnfp]'
```

If the four saved indices are already present:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/ai4c-matplotlib .venv/bin/python scripts/analyze_encoder_consistency.py
.venv/bin/python scripts/write_consistency_report.py
.venv/bin/python -m pytest -q
```

A fresh clone needs the pinned input files and index construction first. Follow [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md). Missing data must not be replaced with fabricated examples or a different corpus under the same result label.

Outputs cover three retrieval settings, overlap at k = 5/10/20/50, full-pool rank correlations, deterministic and expected tie handling, source-macro means and rounding sensitivity. Figures are PNG/SVG. Full scores, per-query tables and structural cards are generated into ignored `data/local/encoder_consistency/`.

## Data and methods

- Pinned EnzymeEngineeringDB V6: 1,342 rows, 36 DOI sources; [audit](research/data_source_audit.json). This legacy file is not the entire current EnzEngDB service.
- Patent references: 2,000 independently hash-sampled Schneider50k rows, yielding 1,988 unique records; [coverage audit](research/reference_coverage_audit.json).
- Representations: substrate Morgan, signed Morgan difference, official DRFP and official RXNFP bert_ft. Existing configurations and metrics are reused; no new encoder is claimed.
- Boundaries: imported records have not passed original-experiment or earliest-date review. Unique structures are not independent discoveries. Agreement is not accuracy.

The verified suite currently contains 50 passing tests, including the local RXNFP numerical integration check. See the report for the evidence chain and limitations.

## Collection and historical ranking tools

- [Chinese walkthrough](docs/从零开始理解与使用BioReaction_Atlas.md)
- [English collection guide](docs/Collection_Guide_EN.md)
- [Single-cutoff historical ranking evaluation](docs/EVALUATION.md)
- [Earlier Chinese overview and local map instructions](README.zh-CN.md)

Older generated workbooks, maps and detailed source-derived outputs are local products excluded from initial Git tracking. Their instructions remain useful after local regeneration. Aggregate agreement results above are included.

## License and project status

Original project code is licensed under [Apache-2.0](LICENSE). See [NOTICE](NOTICE) for scope and [third-party attribution](docs/THIRD_PARTY.md) for upstream methods, data and weights. This license does not relicense third-party datasets or authorize their redistribution. Raw data, weights and detailed derived records remain local by default.

This is a research prototype with a completed descriptive computational result and an unfinished discovery-event audit. No archival DOI or peer-reviewed publication is claimed. Citation metadata will be added with verified author identity and a public release.
