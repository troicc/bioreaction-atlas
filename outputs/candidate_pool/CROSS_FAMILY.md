# Representation choice is decisive only when the precursor differs

Technical note, 2026-09-20. A two-family retrieval measurement, not a peer-reviewed result.

## Summary

Two activation families share one candidate pool of 1,341 literature reactions: metal carbene transfer (74.6%) and conjugate addition to dehydroamino acid acceptors (25.4%). Enzyme seeds from each family query the combined pool, and the top-10 is scored for how much of it comes from the seed's own family, against that family's share of the pool as the no-skill reference.

| Representation | Carbene seeds (n=278, 17 papers) | PLP seeds (n=31, **5 papers**) |
|---|---:|---:|
| *no-skill reference* | *74.6%* | *25.4%* |
| Morgan difference | 96.4% (×1.29) | **9.3% (×0.37)** |
| Substrate Morgan | 93.8% (×1.26) | 14.5% (×0.57) |
| DRFP | 99.9% (×1.34) | **43.2% (×1.69)** |
| RXNFP | 98.9% (×1.33) | **8.4% (×0.33)** |
| Seeds with no own-family hit | 0 for all four | 20 / 12 / **2** / 19 of 31 |

When the enzyme and the abiotic route use the **same precursor**, every representation succeeds and the choice barely matters: all four land between 94% and 100%. When they share only an **intermediate**, three of the four fall **below the pool's own composition** — they rank the wrong family higher than chance would — and only DRFP stays above it.

## Why the two families differ

Carbene transfer is the easy case by construction. A haem carbene enzyme and a dirhodium catalyst both consume a diazo compound, so the diagnostic group is present in both reaction SMILES and any fingerprint sees it.

PLP β-substitution is not. TrpB consumes **serine** and forms the aminoacrylate inside the active site; the abiotic counterpart starts from a **dehydroalanine** that is already formed. The shared object is an intermediate that appears in neither reaction SMILES. Nothing in the enzyme's recorded structures points at the abiotic acceptor.

RXNFP illustrates the gap most sharply: 98.9% when the precursor matches, 8.4% when it does not, with 19 of 31 seeds returning no same-family candidate at all from a pool a quarter composed of that family.

## Why this matters for the project's question

Enzymes routinely generate their reactive intermediate in situ from a different precursor than a chemist would use. The intermediate-sharing case is therefore the normal one for new-to-nature biocatalysis, not the exception. A retrieval result measured on a shared-precursor family says almost nothing about it.

It also reframes the [encoder agreement study](../encoder_consistency/REPORT.md). Disagreement between representations is not uniformly distributed: where precursors align, all four agree and all four are right; where they do not, they diverge and most are worse than the pool's composition. Reporting one agreement figure over a mixed corpus averages these two regimes together.

## Limits

**The PLP result rests on five papers.** Thirty-one unique reactions from five DOIs is a small, dependent sample, and paper-level effects are not separable from representation effects at this size. The direction is consistent across three failing representations and the effect is large, but the number itself should not be quoted as a rate.

Family labels come from a structural screen, not from verified chemistry. A same-family candidate is not a verified precedent, and lift is measured against this pool's composition, not against chance in any wider sense. Two families in one fixed pool do not establish a general property of any representation.

Carbene seeds are selected by cofactor **and** the family's structural screen, which removes haem nitrene and C–H amination reactions that would not match a carbene pool. Without that filter the carbene figures fall to 66–87% on a seed set containing chemistry the pool does not cover. PLP seeds cannot be selected this way, because the enzyme's own reaction does not carry the acceptor; cofactor is the only available handle, and that asymmetry is the finding rather than a flaw in it.

## Reproduction

```bash
PYTHONPATH=src .venv/bin/python scripts/cross_family_retrieval.py
```

Requires both family pools imported and the combined corpus encoded with all four backends. Exact values are in [cross_family.json](cross_family.json).

中文摘要：两个活化家族共用一个 1,341 条候选池（卡宾 74.6%、脱氢氨基酸加成 25.4%）。当酶与非酶路线**共享前体**（重氮）时，四种表示全部成功（94–100%），选哪个几乎无差别；当两者**只共享中间体**（氨基丙烯酸酯，两边 SMILES 均不含）时，四种中有三种**低于池子自身构成**（0.33–0.57 倍），只有 DRFP 仍在基线之上（1.69 倍）。RXNFP 从 98.9% 跌至 8.4%。酶常在活性位点内从不同前体原位生成中间体，因此后一种情形才是常态。PLP 结果仅基于 **5 篇论文**，不应作为比率引用。
