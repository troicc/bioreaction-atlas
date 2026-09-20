# Research state

Last updated 2026-09-20. This file is the handover: what has been measured, what it means, where the code is, and what is not done. Read it before continuing the project in a new session.

---

## 1. The goal

Given the reactions an enzyme platform already performs, produce a ranked shortlist of **non-enzymatic** reactions worth attempting on that platform, with evidence attached.

Everything else in this repository exists to serve that. Where a component does not yet serve it, §7 says so.

---

## 2. The project in one paragraph

Reaction-similarity retrieval was supposed to connect enzyme chemistry to its abiotic counterparts. It was measured, and it does not work by default: the candidate corpus in use contained no relevant chemistry at all, and even with a correct corpus, three of four representations ranked the *wrong* activation family higher than chance whenever the enzyme and the chemist start from different precursors — which is the normal case in biocatalysis. Rewriting both routes in terms of the intermediate they share repairs it for structural fingerprints, but not for a learned reaction embedding, because that embedding does not encode the family as a region at all. The result is a working **family filter** and a **non-working within-family ranker**.

---

## 3. Findings

### F1. The patent corpus contains no carbene-transfer precedents

Across **278** haem-carbene enzyme seeds, none of four representations retrieved a single carbene-transfer reaction from the 1,988-record patent pool at top-10. Not a representation failure: a scan of all **50,000** Schneider50k rows finds **2** records (0.004%) with a substituted diazo reactant, and neither is a carbene transfer — a Mitsunobu azodicarboxylate and a chromium oxidation whose diazo is a spectator.

All three published rxnfp reaction atlases are patent-derived (Schneider 50k; USPTO 1k TPL at 445k reactions; Pistachio). Scaling from 50k to 445k adds routine transformations, not methodology chemistry, and Lowe's release ends September 2016.

**Consequence for the earlier encoder-agreement study:** its cross-domain overlap of 0.70%–11.07% was measured against a pool containing no correct answer for this chemistry. It shows representation disagreement without establishing that any representation failed.

Report: `outputs/candidate_pool/REPORT.md`

### F2. Retrieval fails exactly when the precursor differs

Two families in one pool of 1,341 candidates (carbene 74.6%, dehydroamino acid 25.4%). Enzyme seeds query the combined pool; top-10 is scored for own-family share against the family's pool share as the no-skill reference.

| Representation | Carbene seeds (n=278, 17 papers) | PLP seeds (n=31, **5 papers**) |
|---|---:|---:|
| *no-skill reference* | *74.6%* | *25.4%* |
| Morgan difference | 96.4% (×1.29) | **9.3% (×0.37)** |
| Substrate Morgan | 93.8% (×1.26) | 14.5% (×0.57) |
| DRFP | 99.9% (×1.34) | 43.2% (×1.69) |
| RXNFP | 98.9% (×1.33) | **8.4% (×0.33)** |
| Seeds with no own-family hit | 0 for all four | 20 / 12 / 2 / 19 of 31 |

Carbene is the easy case: enzyme and chemist both consume a **diazo compound**, so the diagnostic group is in both reaction SMILES. PLP is not: TrpB consumes **serine** and forms the aminoacrylate in the active site while the abiotic route starts from a formed **dehydroalanine**. The shared object appears in neither reaction SMILES.

**Enzymes routinely generate their intermediate in situ from a different precursor, so the PLP case is the normal one.**

### F3. Normalising to the intermediate repairs it — for structural fingerprints

One reaction SMARTS rewrites serine, cysteine, O-phospho-serine and threonine into the aminoacrylate by β-elimination. Two further rules reduce both sides to the unprotected free acid, on reactants and products.

| Representation | Raw | Reactant normalised | Acceptor canonical | **Both sides canonical** |
|---|---:|---:|---:|---:|
| Morgan difference | ×0.37 | ×3.28 | ×3.87 | **×4.82 (98.1%)** |
| Substrate Morgan | ×0.57 | ×1.68 | ×3.58 | ×3.95 |
| DRFP | ×1.69 | ×3.83 | ×4.30 | **×4.92 (100.0%)** |
| RXNFP | ×0.33 | ×0.77 | ×0.53 | ×0.78 |
| PLP seeds with no own-family hit | 20/12/2/19 | 1/1/0/8 | 1/0/0/21 | **0/0/0/8** |

No model, no training, no new data. Carbene figures are unaffected, as they must be — no rule applies there. **Not leakage:** none of the 31 normalised seeds matches a pool entry exactly.

### F4. RXNFP does not recover, because the family is not a region in its space

Two explanations were offered and **both refuted** by measurement: acceptor protecting groups (canonicalising made it worse, 0.77→0.53) and product protecting groups (full canonicalisation returned it to 0.78, still below baseline).

Measuring the space instead of the query:

| Representation | carbene within/across/**sep** | dehydroamino acid within/across/**sep** |
|---|---|---|
| Morgan difference | 0.123 / 0.009 / **+0.114** | 0.148 / 0.009 / **+0.139** |
| Substrate Morgan | 0.554 / 0.434 / **+0.120** | 0.503 / 0.434 / **+0.069** |
| DRFP | 0.087 / 0.017 / **+0.070** | 0.102 / 0.017 / **+0.085** |
| RXNFP | 0.700 / 0.347 / **+0.352** | 0.363 / 0.347 / **+0.015** |

For a normalised PLP seed, RXNFP's mean similarity to the **carbene** family is 0.629 and to its **own** family 0.391; its top six neighbours are one dehydroamino acid reaction and five cyclopropanations.

> **Normalisation aligns a query to a family. It cannot create a neighbourhood the representation does not encode.**

`scripts/family_cohesion.py` runs this as a pre-flight check — no seeds, no retrieval, only an encoded pool.

Untested hypothesis for *why*: RXNFP was trained to classify patent reactions, so its geometry follows patent class. Carbene maps to coherent classes; conjugate addition to a dehydroamino acid spans thioether synthesis, N-alkylation and Heck coupling.

### F5. The shortlist is a filter, not a ranker

A candidate is **firm** when every fused encoder ranks it in the top 10% of the pool.

| Platform | Family | Firm |
|---|---|---:|
| haem | metal carbene | **7 of 8** |
| PLP | dehydroamino acid addition | **0 of 10** |

The representations agree on which family to search and disagree on the ordering within it. The best PLP candidate's worst rank is 43 of 303. **The PLP shortlist's chemistry is right** — thiophenol, naphthalenethiol and benzylamine additions to dehydroalanine, which is cysteine synthase chemistry — so it is read as ten papers, not as a ranking of ten.

Retrospective check: the carbene shortlist includes carbene Si–H insertion, the transformation a cytochrome c variant was engineered to perform in 2016. Enzymatic Si–H insertions are in the seed set, so this is evidence the ranking tracks transferability, **not a prediction**.

### F6. Exact-match ground truth does not exist

Of **639** enzyme reactions, **1** has a ≥0.95 structural match in the abiotic pool (cyclopropenation of 1-phenylpropyne). Transferability lives at the transformation-type level, not the substrate level, so labels cannot be harvested automatically. Ground truth requires human adjudication of discovery events.

### F7. Data-quality findings, made while building

- Same-publication leakage inflates apparent retrieval quality: within-enzyme top-10 agreement falls from 42.8–62.5% to 16.6–37.7% once candidates sharing a source DOI are excluded.
- Two provenance defects in the pinned EnzymeEngineeringDB V6 file: a record whose encoded transformation (N–H functionalization) disagrees with its publication's subject (intramolecular C(sp3)–H amination), and one omitting its sulfur substrate from the stored product.
- 79% of Schneider50k rows carry catalytic context in the agents segment that `structure_view` discards; only 7.6% carry a transition metal.
- A Reaxys export contained one **retracted article**, ten reviews and ten conference papers.

---

## 4. Code map

### Library — `src/bioreaction_atlas/`

| Module | Purpose |
|---|---|
| `activation.py` | Activation families, membership screens, agents-segment parsing, `acceptor_consumed`, `family_screen` |
| `intermediates.py` | `normalize_reactants` (precursor → intermediate), `canonicalize` (both sides → unprotected core) |
| `methodology.py` | Bulk intake of literature reactions; screening, document-type filter, family labelling |
| `rdf.py` | RD File reader; per-variation explosion; Reaxys field mapping |
| `reaxys_pdf.py` | Citation and condition layer from a Reaxys PDF export |
| `coverage.py` | Protocol v0.2 four-state machine and C/N accounting (**built, never run on real events**) |
| `corpus.py`, `encoders.py`, `consistency.py` | Pre-existing: corpora, four representations, agreement metrics |
| `cards.py`, `maps.py`, `map_view.py` | Evidence cards and offline maps |
| `evaluation.py` | Pre-existing v1 single-cutoff ranking design. **Separate from `coverage.py`; do not conflate.** |

### Scripts — `scripts/`

| Script | What it does |
|---|---|
| `rdf_to_csv.py` | RD File → import CSV. `--list-fields` first, always |
| `import_methodology.py` | CSV → corpus. `--normalize` admits in-situ routes, `--no-screen` keeps a labelled mixture |
| `reaxys_pdf_citations.py` | Recover citations from a PDF export |
| `recommend_candidates.py` | **The deliverable.** Ranked shortlist for a platform |
| `cross_family_retrieval.py` | F2/F3 measurement |
| `family_cohesion.py` | F4 pre-flight check |
| `family_match_rate.py` | F1 measurement |
| `coverage_status.py`, `event_worksheet.py`, `seed_coverage_registry.py` | Coverage audit (unused) |

### Documents

| Path | Contents |
|---|---|
| `research/activation_family_map.md` | Which abiotic chemistry to mine per enzyme platform; shared-precursor vs shared-intermediate |
| `docs/BUILDING_THE_CANDIDATE_POOL.md` | Reaxys search and export, one handle per family, the settings that silently widen a query |
| `docs/RECOMMENDING_CANDIDATES.md` | How the shortlist is built and what it does not claim |
| `docs/COVERAGE_AUDIT.md` | Per-event loop for the unexecuted audit |
| `outputs/candidate_pool/REPORT.md` | F1 |
| `outputs/candidate_pool/CROSS_FAMILY.md` | F2, F3, F4 |
| `outputs/encoder_consistency/REPORT.md` | The earlier encoder-agreement study; CI regenerates it from `summary.json` |

### Local data — `data/local/` (gitignored, licensed)

| Path | Contents |
|---|---|
| `pools/carbene.json` | 2,426 records, 999 structures, 1,075 papers, 1888–2026 |
| `pools/plp.json` | 359 records, 347 structures, ~148 papers, 1932–2026 |
| `pools/combined_full/` | Both families, fully canonicalised, encoded with four backends. **Use this one.** |
| `reference_demo/` | Enzyme seeds: 639 reactions, 36 DOIs, cofactors heme 1194 / PLP 117 / Fe(II) 13 |
| `candidates/` | Generated shortlists |

---

## 5. How to rebuild from scratch

```bash
# 1. Export from Reaxys: Reactions tab, RD File. See docs/BUILDING_THE_CANDIDATE_POOL.md
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --list-fields
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --family metal_carbene --out pool.csv
PYTHONPATH=src .venv/bin/python scripts/import_methodology.py pool.csv --out data/local/pools/x.json --prefix X

# 2. Canonicalise both sides, then encode
#    (see the inline snippet in the CROSS_FAMILY report for the canonicalisation pass)
for b in morgan substrate drfp; do
  PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/combined_full.json \
    --backend $b --allow-unreviewed --out data/local/pools/combined_full/$b
done
PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/combined_full.json \
  --backend rxnfp --model-dir data/local/public/rxnfp --allow-unreviewed --out data/local/pools/combined_full/rxnfp

# 3. Check the family is a region before trusting any encoder on it
PYTHONPATH=src .venv/bin/python scripts/family_cohesion.py

# 4. Produce the shortlist
PYTHONPATH=src .venv/bin/python scripts/recommend_candidates.py --family aminoacrylate_addition --cofactor PLP
```

---

## 6. Rules this project holds itself to

These are enforced in code and in tests, not just stated.

- **No feasibility score, no success probability.** Candidates carry evidence and an order, never a number that implies calibrated likelihood.
- **Imported is not reviewed.** A literature identifier is not a checked procedure.
- **A publication year is not a verified public date.**
- **No mechanism is inferred.** `mechanism_evidence` stays `未说明` until someone reads the paper.
- **A top-k miss is not a corpus absence.**
- **Contested judgements are recorded as properties, not written into membership.** `acceptor_consumed` is the worked example: whether a Heck coupling counts as a PLP precedent is left reportable both ways.
- **Unresolved stays in the denominator.**
- **Labels are an answer key, not training data.** A label that is a deterministic function of structure teaches a model the rule, not the chemistry.

---

## 7. What is not done

Ordered by how much it blocks the goal.

**① There is no definition of "worth trying" beyond "same family."** F6 shows labels cannot be harvested automatically. The only path is human adjudication of ~20 discovery events — `research/coverage_protocol_v02.md` and `docs/COVERAGE_AUDIT.md` define it completely, `src/bioreaction_atlas/coverage.py` implements the accounting, and **zero events have been annotated**. Current state: C=0, U=5, N=5.

**② Within-family ranking has no signal.** F5. The unused signal is already in the pool — catalyst, solvent, temperature, time, yield, `acceptor_consumed`, year — and reranking by catalytic context was the original proposal's central idea, never implemented. **This is the next task (A).**

**③ No baselines.** A top-10 means nothing without comparison to random-in-family, most-cited and most-recent. Part of task A.

**④ Two families of about fourteen.** `research/activation_family_map.md` lists the rest. ThDP↔NHC is blocked: the pinned V6 file has no ThDP seeds, so seeds must be curated from the literature first (Huang Xiaoqiang's group at NJU is the most active on repurposed ThDP chemistry).

**⑤ The PLP seed set is 31 reactions from 5 papers.** Paper-level n=5 is the single hardest limit on publishing F2–F4. Carbene is 278 from 17.

**⑥ A known pool gap.** An abiotic route can form the acceptor in situ from the enzyme's own precursor, and an acceptor substructure query misses that route entirely. `import_methodology.py --normalize` now admits such reactions, and the query that finds them is documented, but **the export has not been run**.

**⑦ No archival DOI.** The repository is public with green CI; Zenodo has not been connected and `CITATION.cff` carries only a GitHub handle.

---

## 8. Reproducibility

156 tests, 155 in CI on Python 3.11 and 3.12 from the checkout alone. CI separately regenerates `outputs/encoder_consistency/REPORT.md` from its `summary.json` and fails if the committed note differs, so no reported metric in that report can be hand-edited. Raw Reaxys exports, model weights and source-rich derived records stay in `data/local/`; only aggregates are committed.

中文要点：本文件是交接说明。**目标**是给定酶平台输出值得尝试的非酶反应清单。**已完成**：专利语料中无卡宾先例（F1）；检索失效发生在酶与化学家前体不同时（F2）；归一化到共享中间体可修复结构指纹但修不好 RXNFP（F3）；原因是该家族在 RXNFP 空间中不成区域（F4）；当前产物是**筛子而非排序器**（F5）；精确匹配标签不存在（F6）。**未完成**按阻塞程度排序见 §7，其中①需人工裁定 20 个发现事件，②③是下一步任务 A。
