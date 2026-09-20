# A patent reaction corpus contains no carbene-transfer precedents

Technical note, 2026-09-20. A pool-composition measurement, not a peer-reviewed result.

## Summary

Across **278 haem-carbene enzyme reactions** from the pinned EnzymeEngineeringDB V6 file, none of four reaction representations retrieved a single carbene-transfer reaction from a 1,988-record patent reference pool, at top-10, for any seed. The cause is not the representations: a full scan of all **50,000 Schneider50k rows** finds **2 records** (0.004%) carrying a substituted diazo reactant, and neither is a carbene transfer — one is a Mitsunobu with an azodicarboxylate reagent, the other a chromium oxidation of a steroid whose diazo group is a spectator.

A literature-derived pool assembled for the same activation family holds **997 carbene-transfer reactions of 999** unique structures, drawn from **1,075 distinct papers** spanning 1888-2026.

This bears on the [encoder agreement study](../encoder_consistency/REPORT.md). Its cross-domain measurement — mean expected top-10 overlap of 0.70%-11.07% between representation pairs — was made against a candidate pool that, for the carbene chemistry dominating the enzyme seeds, contains no correct answer. Low agreement in a pool where nothing is retrievable is not evidence about representations.

## Measurement

| | Patent pool | Literature pool |
|---|---:|---:|
| Source | 2,000 hash-sampled Schneider50k rows | Reaxys export, substituted-diazo substructure ∩ Reagent/Catalyst |
| Unique reaction structures | 1,988 | 999 |
| Records (one per literature variation) | 1,988 | 2,426 |
| Distinct papers | — | 1,075 |
| In carbene family | **0** | **997** |
| Top-10 in-family, 278 seeds, Morgan difference | 0.0% | 100% |
| Top-10 in-family, substrate Morgan | 0.0% | 100% |
| Top-10 in-family, DRFP | 0.0% | 100% |
| Top-10 in-family, RXNFP | 0.0% | 100% |
| Seeds with zero in-family hit, any encoder | 278/278 | 0/278 |

Family membership requires a **substituted** diazo reactant: the diazo carbon must bear a carbon substituent. Diazomethane and TMS-diazomethane are methylating reagents for carboxylic acids, and admitting them inflates the patent pool to nine apparent matches and DRFP's top-10 family share to 46.3%. Every one of those nine records is an ester methylation. The distinction is the difference between a measured 102-fold enrichment and a measured zero.

## A retrieved example

The [encoder report's Case 1](../encoder_consistency/REPORT.md) is a haem carbene N-H functionalization of 2-methylindoline with a diazo lactone. Against the patent pool its four top neighbours were N-methylation, N-acetylation, hydrogenolysis and urea formation. Against the literature pool, RXNFP's top three are aryl diazoacetates reacting with arylamines — carbene N-H insertion, the same transformation the seed performs, at cosine similarity 0.886, 0.879 and 0.873.

Two encoder behaviours separate here and should not be conflated. Finding the right family in a corpus where it is rare is one problem; ranking within a family is another. RXNFP returned nothing in-family from the patent pool for any of 278 seeds, and produced the closest mechanistic match in the literature pool.

## Limits

A family match is **not** a verified precedent. This measures the composition of a candidate pool and what retrieval surfaces from it, not correctness, transferability or experimental feasibility. Earliest public dates have not been verified, so no historical claim follows.

The literature pool's records are `imported`: they carry a literature identifier and have not passed primary-source review. Retracted articles, reviews and conference abstracts are excluded; 278 of 2,426 records are patents rather than journal methodology and are labelled as such.

Family membership is decided by a lexical structural screen, not by mechanism. It admits reactions whose diazo reactant is a spectator and rejects carbene precursors that are not diazo compounds — sulfoxonium ylides and N-sulfonyl triazoles among them. The absence measured here is an absence of substituted-diazo chemistry, which is narrower than an absence of all carbene chemistry.

Schneider50k is a 50-class classification benchmark, not all of patent chemistry. A wider patent corpus would contain more carbene chemistry than 0.004%, though the class list — Boc protection, amide coupling, Suzuki, reductive amination, esterification, halogenation — indicates what this kind of source is built to cover.

## Reproduction

```bash
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --family metal_carbene --out carbene.csv
PYTHONPATH=src .venv/bin/python scripts/import_methodology.py carbene.csv --out data/local/pools/carbene.json --prefix CARB
for b in morgan substrate drfp rxnfp; do
  PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/carbene.json \
    --backend $b --allow-unreviewed --out data/local/pools/carbene/$b
done
PYTHONPATH=src .venv/bin/python scripts/family_match_rate.py --pools carbene=data/local/pools/carbene
PYTHONPATH=src .venv/bin/python scripts/family_match_rate.py --pools patent=data/local/reference_demo \
  --pool-domain patent_reference
```

The Reaxys export is licensed data and stays local; the aggregate counts above are shareable.

中文摘要：278 条血红素卡宾酶反应作为查询，四种表示在 1,988 条专利参考池中的 Top-10 均**未检出任何一条卡宾转移反应**。原因不是表示方法——全量 50,000 行 Schneider50k 中仅 2 行（0.004%）带取代重氮反应物，且两条都不是卡宾转移。按同一活化家族从文献构建的候选池，999 个唯一结构中 997 条属于卡宾家族，来自 1,075 篇论文。此前编码器一致性研究的跨域测量，是在一个对该化学而言不存在正确答案的候选池中做出的。同族命中不等于已核实先例。
