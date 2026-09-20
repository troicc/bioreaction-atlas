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

---

# Normalising to the intermediate closes most of the gap

Added 2026-09-20.

If the failure above is caused by the precursor differing, then rewriting the enzyme's precursor into the intermediate its cofactor forms should repair it. That is a falsifiable prediction, and it was tested by applying one explicit chemical rule.

TrpB's serine is rewritten by β-elimination into the aminoacrylate. The rule is a reaction SMARTS covering serine, cysteine, O-phospho-serine and threonine; it touches only the reactant side, leaves other families alone, and rewrites exactly one precursor per reaction. All 31 PLP seeds normalise.

| Representation | PLP seeds, raw | PLP seeds, normalised | Carbene seeds |
|---|---:|---:|---:|
| *no-skill reference* | *25.4%* | *25.4%* | *74.6%* |
| Morgan difference | 9.3% (×0.37) | **83.5% (×3.28)** | 96.4%, unchanged |
| Substrate Morgan | 14.5% (×0.57) | 42.9% (×1.68) | 93.8%, unchanged |
| DRFP | 43.2% (×1.69) | **97.7% (×3.83)** | 99.9%, unchanged |
| RXNFP | 8.4% (×0.33) | 19.7% (**×0.77**) | 98.9%, unchanged |
| Seeds with no own-family hit | 20 / 12 / 2 / 19 | **1 / 1 / 0 / 8** | 0 for all four |

Morgan difference moves from well below the pool's composition to 3.28× it, on a one-line chemical rule and with no model, training or new data. DRFP reaches 97.7%. Carbene figures are unchanged, as they must be: no rule applies to that family.

**This is not leakage.** None of the 31 normalised seeds matches any pool entry exactly. The pool's acceptors are N-acylated esters while the normalised seed carries the free amino acid, so the gain comes from resemblance at the intermediate level rather than from identity.

## RXNFP does not recover

RXNFP improves from 0.33× to 0.77× and remains below the pool's own composition, the only representation that normalisation fails to repair. A plausible reason is that the free aminoacrylate is an unstable species largely absent from the patent corpus RXNFP was trained on, while the abiotic pool uses N-acylated esters; a learned embedding can place the two far apart where a substructure fingerprint sees a shared skeleton. That is a hypothesis about a pretrained model's coverage, not a demonstrated cause, and the direct test — normalising the abiotic side as well, by stripping N-protection — has not been run.

## What this supports and what it does not

It supports a specific, mechanistic account of when reaction-similarity retrieval fails for biocatalysis, and a concrete repair: **the failure tracks whether the enzyme and the abiotic route share a precursor, and expressing both at the level of the shared intermediate recovers most of it.**

It does not establish that this generalises. One family was normalised, by one rule, on 31 reactions from five papers. The other families in the [activation map](../../research/activation_family_map.md) — carbene and nitrene precursors, the Breslow intermediate, flavin hydride transfer, Fe(IV)=O — would each need their own rule and their own test, and the shared-precursor families cannot test the hypothesis at all because they never exhibit the failure.

Normalisation is also a chemical assertion. Writing serine as an aminoacrylate states that the enzyme forms that intermediate, which is well established for TrpB but is a claim that must be sourced for each new rule, not assumed.

中文摘要：若失效源于前体不同，则把酶的前体改写为其辅因子生成的中间体应能修复——这是可证伪的预测。用一条 β-消除 SMARTS 将丝氨酸改写为氨基丙烯酸酯后，Morgan 差分指纹从 0.37 倍升至 **3.28 倍**，DRFP 达 **97.7%（3.83 倍）**，零命中种子由 20/12/2/19 降至 1/1/0/8；卡宾家族数值不变（该族无规则适用）。31 条归一化种子与池中记录**无一完全相同**，故非泄漏。RXNFP 仅从 0.33 升至 0.77，仍低于池子构成，是唯一未被修复的表示。结论限于一个家族、一条规则、5 篇论文。
