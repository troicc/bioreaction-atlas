"""Build the English technical note from computed summaries; no invented metrics."""
import json
from pathlib import Path


def main():
    root = Path('outputs/encoder_consistency')
    report = json.loads((root / 'summary.json').read_text())
    analyses = report['analyses']
    rows = []
    for p in analyses['enzyme_to_patent']['pairs']:
        m = p['metrics']
        rows.append(f"| {p['encoder_a']} / {p['encoder_b']} | {m['expected_overlap_at_10']['mean']:.2%} | "
                    f"{m['overlap_at_10']['mean']:.2%} | {m['spearman']['mean']:.3f} | "
                    f"{m['expected_overlap_at_10']['source_macro_mean']:.2%} |")
    comparison = []
    for name, r in analyses.items():
        values = [p['metrics']['expected_overlap_at_10']['mean'] for p in r['pairs']]
        comparison.append(f"| {name} | {r['query_count']} | {r['eligible_candidate_range'][0]}-{r['eligible_candidate_range'][1]} | {min(values):.2%}-{max(values):.2%} |")
    max_rounding = max(abs(a['metrics']['expected_overlap_at_10']['mean'] - b['metrics']['expected_overlap_at_10']['mean'])
                       for rows_ in report['rounding_sensitivity'].values()
                       for a, b in zip(rows_, analyses['enzyme_to_patent']['pairs']))
    text = """# Retrieving abiotic precedents for new-to-nature biocatalysis

## A descriptive study of representation dependence

Technical note, 2026-09-12. Analysis v1.0. This is a completed computational pilot, not a peer-reviewed paper or a discovery-event coverage benchmark.

### Abstract

We compared four saved reaction representations on a common set of 639 unique enzyme-reference reactions from a pinned EnzymeEngineeringDB V6 file and 1,988 unique patent-reference reactions independently sampled from Schneider50k. Across the six encoder pairs, mean expected top-10 overlap in enzyme-to-patent retrieval ranged from 0.70% to 11.07%, and mean full-candidate Spearman correlation ranged from 0.042 to 0.217. Within the enzyme corpus, top-10 overlap ranged from 42.82% to 62.45%; excluding candidates sharing a source with the query reduced that range to 16.64%-37.71%. These observations establish representation dependence in this fixed reference collection. They do not identify the most accurate encoder or measure the fraction of discoveries with a verified abiotic precedent. Source composition, boundary ties and individual structural records warrant explicit treatment before a historical chemical benchmark can be built.

### 1. Research question

Precedent-guided biocatalysis depends on at least three distinct conditions: relevant chemistry has been reported, the chosen corpus contains an interpretable record, and the retrieval method brings it to attention. This pilot measures whether four existing representations agree about which records to inspect. It tests reproducibility across representations, not catalytic transferability.

The primary follow-up question is the confirmed fraction of independent enzyme discovery events with earlier nonenzymatic precedents in a frozen public corpus. Its [separate coverage protocol](../../research/coverage_protocol_v02.md) records literature evidence, corpus inclusion, structural eligibility and retrieval outcomes independently. No event-level coverage percentage is currently available.

### 2. Inputs and unit of analysis

The pinned EnzymeEngineeringDB V6 source contains 1,342 rows and 36 distinct DOI sources. The pre-existing importer canonicalized structures and grouped identical structural reactions within each domain, retaining all experimental evidence rows. Substrate Morgan and RXNFP indices each contain 640 enzyme entries; Morgan difference and DRFP contain 639. Eighteen source rows corresponding to the additional unique entry were excluded from the latter representations because the fingerprints were zero. The present analysis uses the intersection: 639 queries in all four methods. These are unique encoded structures, including stereochemical distinctions, not 639 independent discoveries. They represent 36 normalized publication sources.

The patent pool was formed before this study by selecting 2,000 Schneider50k rows by a fixed SHA256(seed:row) ordering with seed 17. Deduplication yields 1,988 common reference entries. The pool is a sample from a 50-class patent dataset. Patent membership does not establish nonenzymatic catalysis or a verified early precedent, and this small sample does not represent all synthetic chemistry.

Each index is loaded with vector checksum verification. The analysis requires matching corpus hashes and structural-view identifiers, aligns entries by stable IDs, and rejects conflicting common-entry provenance. The structural view removes atom-map numbers and the agents segment. Components placed in the original reactants segment remain present; no unverified assignment of solvent or reagent roles is attempted.

| Representation | Saved configuration | Similarity |
|---|---|---|
| Morgan difference | Product minus reactant counts; radius 2; 4,096 dimensions; chirality retained | Signed cosine |
| Substrate Morgan | Reactant counts only; radius 2; 4,096 dimensions; chirality retained | Cosine |
| DRFP | Official implementation; radius 3; 2,048 dimensions; rings enabled | Binary Tanimoto |
| RXNFP | Official bert_ft weights; 256-dimensional final CLS embedding | Cosine |

This comparison changes both representation and its specified similarity measure; it does not isolate the contribution of either one. RXNFP uses pretrained weights with no historical training-data exclusion claim. No model was retrained for this analysis. See [third-party attribution](../../docs/THIRD_PARTY.md), [source audit](../../research/data_source_audit.json) and [configuration](configuration.json).

### 3. Metrics and controls

For each query and encoder pair, deterministic overlap is the size of the intersection of the two top-k lists divided by k. It is not Jaccard overlap. We evaluate k = 5, 10, 20 and 50. Scores are rounded to six decimal places before ranking. Deterministic lists break ties by ascending entry ID.

Because boundary ties can make ID-based overlap arbitrary, the primary metric averages over independent uniform permutations within each encoder's boundary tie. If pA(j) and pB(j) are candidate j's top-k membership probabilities, expected overlap is sum_j pA(j)pB(j)/k. This is an expectation over tie-breaking, not a calibrated probability that a reaction is correct. Even identical tied score vectors can have expected overlap below one under independent permutations. Heatmap diagonals are therefore omitted.

Spearman correlation uses average ranks on the entire eligible candidate pool, never only the intersection of retrieved lists. Constant-score cases are undefined and counted separately. The independent uniform-list reference has expected overlap k/M for a candidate pool of size M; at k=10 and M=1,988 this is 0.503%. It is a descriptive reference, not a significance test.

We report query-weighted means and a source-macro sensitivity: calculate the mean among queries associated with each DOI, then average the DOI means. A multi-source query contributes to each of its associated source groups. Source-macro averaging is a descriptive reweighting, not an independence correction or a confidence interval. The fixed dataset is fully enumerated; no population-level inferential claims or significance tests are made.

Within-enzyme retrieval excludes the query itself. A second control removes every candidate sharing any normalized source with the query. All methods share the resulting eligibility mask. Candidate counts vary between 579 and 638 in that control. The controls have different candidate domains and sizes and must not be read as a causal estimate of domain shift or source leakage alone.

### 4. Results

| Encoder pair | Expected top-10 overlap | Deterministic top-10 overlap | Mean Spearman | Source-macro expected overlap |
|---|---:|---:|---:|---:|
""" + '\n'.join(rows) + """

![Cross-domain agreement heatmaps](enzyme_to_patent_heatmaps.png)

Figure 1. Pairwise agreement in the identical 1,988-candidate patent pool, averaged across 639 common enzyme queries. Overlap and rank correlation are different measurements; neither establishes retrieval accuracy.

![Overlap across retrieval budgets](enzyme_to_patent_overlap.png)

Figure 2. Expected overlap across top-k budgets. The dashed line is the independent uniform-list reference. All six pairwise mean top-10 overlaps exceed that reference, but no accuracy claim or statistical significance follows from this comparison.

| Retrieval analysis | Queries | Eligible candidates per query | Six-pair expected top-10 overlap range |
|---|---:|---:|---:|
""" + '\n'.join(comparison) + """

![Within-enzyme control](enzyme_to_enzyme_heatmaps.png)

![Source-excluded control](enzyme_cross_source_heatmaps.png)

Figure 3. Within-enzyme agreement before and after excluding shared publication sources. Agreement decreases for every encoder pair after source exclusion. The larger within-enzyme agreement is consistent with related substrate series affecting neighborhood composition, but the analysis does not establish a unique cause.

At top-10 in the patent pool, 43.35% of Morgan-difference query lists and 16.43% of DRFP query lists cross a boundary tie; substrate Morgan and RXNFP do not cross a boundary tie at this precision. Consequently, deterministic and expected overlap should both be retained. Changing rounding to five or seven decimals changes any pair's mean expected top-10 overlap by at most """ + f'{100 * max_rounding:.4f}' + """ percentage points in this run.

The per-query distribution is provided separately: [cumulative distribution figure](enzyme_to_patent_distribution.png). Detailed scores, pool ID orderings, per-query metrics and selected reaction cards remain in the ignored local directory `data/local/encoder_consistency/`. Aggregate machine-readable results are [summary.json](summary.json) and [pair_summary.csv](pair_summary.csv).

### 5. Three disagreement cases and a data-quality flag

Cases were chosen by increasing mean expected top-10 overlap across all six encoder pairs, with ID as a deterministic tie-break; queries sharing any source with an earlier selected case were skipped. All three selected cases have pairwise-disjoint top-10 lists. This selection deliberately emphasizes disagreement and cannot estimate the prevalence of each failure mode. The following observations describe imported structures. Primary-source experimental correspondence has not been fully adjudicated.

**Case 1: record R_02177955a1d7dfa9c6b0, V6 row 800.** The stored query connects an indoline nitrogen to the diazo-bearing carbon of a lactone reagent. Morgan difference retrieves a nitrogen-methylation record; substrate Morgan retrieves N-benzyl removal on a larger nitrogen-containing scaffold; DRFP retrieves a ketone/amine coupling record; RXNFP retrieves an isocyanate/amine record. These are different transformations even though several involve nitrogen-containing molecules or C-N bond formation. More importantly, the query's associated DOI describes intramolecular C(sp3)-H amination, whereas the encoded transformation appears to be N-H functionalization. This is a provenance/representation discrepancy requiring the original SI, not a proven database error: a downstream derivatization or a mapping mistake could explain it. The record is retained in the frozen descriptive analysis and is flagged before use as a discovery label. [Primary publication metadata](https://pubmed.ncbi.nlm.nih.gov/38161360/).

**Case 2: record R_02efe45ea2436a2da26f, V6 row 327.** The stored query transforms a Si-H substrate into a silanol, consistent with the associated silane-oxidation paper. Substrate Morgan's nearest record also contains silicon but changes a benzyl-protected nitrogen elsewhere. Morgan difference retrieves an acid-to-acid-chloride conversion and DRFP a nitro-to-amino conversion. RXNFP retrieves a record labeled as sulfur oxidation; however, its stored product contains only the acid derived from the peracid reagent and omits the sulfur-containing substrate. That record should be checked for extraction incompleteness before it is interpreted as a usable oxidation precedent. Neither a shared silicon fragment nor an oxidation-related source label is enough to establish the required Si-H transformation. [Authors' institutional publication record](https://recerca.udg.edu/en/publications/selective-enzymatic-oxidation-of-silanes-to-silanols/).

**Case 3: record R_042205093d23820bf7e9, V6 rows 345-346.** The query combines an oxindole derivative with serine and forms a quaternary carbon center with an amino-acid side chain. This is consistent with the associated TrpB study's reported focus on quaternary-carbon formation. Morgan difference's first neighbor is a carbon-methylation record, substrate Morgan retrieves amide formation on an oxindole-containing scaffold, DRFP retrieves methyl-ester hydrolysis, and RXNFP retrieves esterification. The examples show how shared scaffolds, carboxyl functionality and local substitutions can retrieve distinct net transformations. A high similarity score does not identify a serine-based carbon nucleophile/electrophile correspondence or establish a compatible catalytic mechanism. [Author manuscript](https://escholarship.org/content/qt4sm3q620/qt4sm3q620_noSplash_93cb1c0f2395a1e1e51001b61dc702e6.pdf).

These interpretations are hypotheses grounded in the visible structural records, not an attribution of a neural model's internal reasoning. Original patent procedures and enzyme SI still need chemical review. Source class labels can disagree with the actual stored structures and should not substitute for that review.

### 6. Implications and limits

The measured result is substantial representation dependence in this exact reference collection. The reduction after source exclusion makes same-paper neighborhoods a necessary control. The structural cases also reveal why a candidate-coverage study needs provenance validation in addition to geometric similarity.

Low overlap does not mean every method fails: distinct lists can contain different valid precedents. High overlap does not mean the shared hits are correct. This experiment neither proves that enzyme chemistry lacks small-molecule precedents nor ranks encoders by usefulness. It uses a narrow patent sample, an unreviewed legacy enzyme file with uneven source composition, native representation-specific metrics and pre-existing preprocessing choices. It should be described as a descriptive pilot, not as a field-wide benchmark.

The next scientific step is to finish the five-event calibration, freeze independent event selection and one expanded corpus, then annotate transformation correspondences and dates. That would turn the present representation diagnostic into an analysis of corpus coverage and conditional retrieval recall.

### 7. Reproduction and evidence trail

Run from the project root in the existing environment:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/ai4c-matplotlib .venv/bin/python scripts/analyze_encoder_consistency.py
.venv/bin/python scripts/write_consistency_report.py
.venv/bin/python -m pytest -q
```

A fresh checkout first requires the pinned source data and four indices; see [reproduction instructions](../../docs/REPRODUCIBILITY.md). Raw third-party records and weights are not bundled. Local indices are required for full regeneration; aggregate tables and figures can be read without them. No external API, GPU or model retraining is needed once the indices exist.

Evidence E1 is the source and vector provenance in `summary.json`; E2 is the pair summary and local per-query scores; E3 is the selected local reaction cards and linked publication metadata. Finding F1 (low cross-domain agreement) follows from E1/E2; F2 (lower agreement after source exclusion) follows from E2; F3 (case-specific structure/provenance concerns) follows from E3 and remains subject to source review. The reproduction path is pinned source import, shared-pool validation, score computation, tie-aware statistics and report generation. Summary metadata includes code hashes, package versions and local-artifact hashes.

中文摘要：当前固定数据中，跨域检索的 Top-10 共享比例为 0.70%-11.07%；排除同论文后，酶库内部共享比例也下降。它证明结果对表示与候选池敏感，尚未证明哪个编码器更准确，也没有测得发现事件级先例覆盖率。三个分歧案例已保留结构证据，其中一个发现了需要核查的结构与来源主题不一致问题。
"""
    # Keep specific tie percentages coupled to measured results rather than manual rounding.
    primary = analyses['enzyme_to_patent']['pairs']
    morgan_ties = primary[0]['metrics']['boundary_tie_a_at_10']['mean']
    drfp_ties = primary[1]['metrics']['boundary_tie_b_at_10']['mean']
    text = text.replace('43.35%', f'{morgan_ties:.2%}').replace('16.43%', f'{drfp_ties:.2%}')
    (root / 'REPORT.md').write_text(text, encoding='utf-8')
    print(root / 'REPORT.md')


if __name__ == '__main__':
    main()
