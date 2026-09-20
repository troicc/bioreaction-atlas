# Activation-family map: which abiotic chemistry to mine for each enzyme platform

Working document, 2026-09-20. **This is a search-lead map, not established chemistry.** Each row proposes where to look for non-enzymatic reactions whose reactive intermediate resembles an enzyme platform's. A correspondence here licenses a literature search; it does not assert that a transformation is transferable, and every candidate still needs the per-reaction checks in [the original proposal, §4](non_natural_biocatalysis_reaction_atlas_proposal.md).

## Why activation, not bond class

Amide formation, Pd-catalysed C–N coupling and carbene N–H insertion all form a C–N bond. They share almost nothing mechanistically. A candidate pool organized by bond class or by substrate scaffold will therefore retrieve the wrong chemistry, which is the failure mode visible in the three disagreement cases of the [encoder report](../outputs/encoder_consistency/REPORT.md).

The organizing axis is instead **what generates the reactivity**: the reactive intermediate and how it is produced. This is the `mechanism` field already present in the intake schema, with `mechanism_evidence` grading whether it is experimentally supported, author-proposed, or project inference.

## The map

Confidence column: **A** = the synthetic and enzymatic systems are generally accepted to pass through the same intermediate class; **B** = plausible correspondence, needs case-by-case review; **C** = speculative, listed to avoid silently excluding it.

### Metal-dependent platforms

| Enzyme platform | Active species | Intermediate | Abiotic chemistry to mine | Conf. |
|---|---|---|---|---|
| Engineered haem (P450, cyt c, Mb, protoglobin) | Fe–porphyrin | metal carbene | Rh₂(OAc)₄ / Cu(I)–box / Co(II)– and Ir–porphyrin carbene transfer: cyclopropanation, X–H insertion (Si–H, N–H, S–H, O–H, B–H), ylide formation and Doyle–Kirmse, Stevens and Buchner rearrangements | A |
| Engineered haem (nitrene transfer) | Fe–porphyrin | metal nitrene | Rh, Cu, Co, Ag nitrene transfer from azides/iminoiodinanes: C–H amination, aziridination, sulfimidation | A |
| Non-haem Fe/αKG (hydroxylase, halogenase, desaturase) | Fe(IV)=O | HAT then rebound | Fe–PDP / Mn–salen / Mn–pdp C–H oxidation, Cu/Fe radical halogenation, HAT desaturation | A |
| Metal-substituted non-haem (Cu, Ni, Co, Ir in a protein scaffold) | installed metal | organometallic, varies by metal | the corresponding homogeneous catalysis for that metal and oxidation state: Cu C–N / C–S coupling, Ni cross-coupling and photoredox/Ni dual catalysis, Ir photocatalysis | B |
| Artificial metalloenzyme with an exogenous cofactor | anchored complex | as the free complex | the free complex's own reaction scope, read as an upper bound rather than a prediction | B |

### Non-metal platforms

This half is where the correspondences are cleanest and least exploited.

| Enzyme platform | Cofactor | Intermediate | Abiotic chemistry to mine | Conf. |
|---|---|---|---|---|
| **PLP enzymes** (TrpB, transaminase, threonine aldolase, tryptophan synthase) | pyridoxal-5′-phosphate | quinonoid / stabilized α-carbanion, i.e. an imine-activated nucleophile | **enamine and iminium organocatalysis**: proline and MacMillan-type aldol, Mannich, Michael and aza-Michael; β-substitution of dehydroalanine; azomethine-ylide chemistry | A |
| **ThDP enzymes** (benzaldehyde lyase, benzoylformate decarboxylase, transketolase) | thiamine diphosphate | Breslow intermediate, an **acyl anion equivalent (umpolung)** | **NHC organocatalysis**: benzoin and cross-benzoin, Stetter, homoenolate and acyl-azolium chemistry. This is the direct synthetic counterpart of ThDP catalysis | A |
| **Flavoenzymes — ene-reductase (OYE)** | FMN | hydride transfer to an activated alkene, then protonation | transfer hydrogenation with Hantzsch esters; organocatalytic conjugate reduction | A |
| **Flavoenzymes — BVMO** | C4a-peroxyflavin | Criegee intermediate | peracid and H₂O₂/organocatalytic Baeyer–Villiger; organocatalytic epoxidation via oxaziridinium | A |
| **Photo-ene-reductases and photoenzymes** | excited flavin / EDA complex | carbon radical | organic photoredox: EDA-complex activation, HAT catalysis, radical hydroalkylation and radical cyclization | B |
| **Flavin-dependent halogenase** | HOCl / FAD | electrophilic halogenation | directed electrophilic arene halogenation, NXS chemistry | B |
| **Terpene and squalene cyclases** | none (acid) | carbocation cascade | Brønsted- and Lewis-acid polyene cyclization, cation–olefin cascades | A |
| **Hydrolase promiscuity** (lipase, esterase, protease) | Ser–His–Asp, oxyanion hole | acyl-enzyme; general base activation | organocatalytic acyl transfer (DMAP, NHC); amine- or base-catalysed aldol, Michael, Knoevenagel, Henry | B |
| **SAM methyltransferases** | SAM | methyl cation equivalent | electrophilic alkylation reagents; for radical SAM, silyl-radical HAT and radical chain alkylation | B |
| **Carbonic-anhydrase-like / Lewis-acid Zn** | Zn²⁺ | Lewis-acid activated carbonyl | Zn, Sc, Yb Lewis-acid catalysis: Mukaiyama aldol, Friedel–Crafts | C |

## How this drives the corpus build

Mine **one family at a time**, and record the family label on every imported reaction. Two reasons:

1. A reviewer can then ask "did retrieval surface the right *family*" separately from "did it surface the right *substrate*". Those are different failure modes and the current pipeline cannot distinguish them.
2. Families differ enormously in how much abiotic literature exists. Reporting a single pooled hit rate over unequal families would hide that.

Start with the family whose enzyme seeds you already hold. The pinned EnzymeEngineeringDB V6 file is 1,194/1,342 rows haem and 117 PLP, so **metal carbene transfer** and **PLP/organocatalysis** are the two families with existing seeds on both sides.

## What the current corpus cannot supply

Schneider50k is a 50-class balanced subset of patent reactions. Its classes are Boc protection and deprotection, amide coupling, Suzuki/Sonogashira/Stille, reductive amination, nitro and nitrile reduction, esterification, Mitsunobu, Williamson ether synthesis, alcohol oxidation, halogenation, nitration and methylation. **No class in it corresponds to any row of the map above.** 7.6% of its rows carry a transition metal in the agents segment, and the most frequent agents are solvents (DCM, THF, water, DMF, methanol).

It is therefore usable as a negative control and as a source of routine background chemistry, but it cannot be the candidate pool for this question. A pool that cannot contain a correct answer produces uninterpretable retrieval agreement.

## Position in the map is structure, family is a layer

If every family is encoded into one space, structural similarity will cluster by substrate scaffold, not by activation mode — exactly the C–N failure this document opens with. Keep the family label as a **separate display and filtering layer** over the structural layout, never as the thing that produces the coordinates. The existing offline map already supports a two-layer legend.

中文要点：按"靠什么产生反应性"组织候选库，而不是按成键类别或底物骨架。非金属酶这半张表的对应关系最干净也最少被利用——PLP 对应烯胺/亚胺离子有机催化，ThDP 对应 NHC 催化（Breslow 中间体就是酰基负离子等价体），黄素烯还原酶对应 Hantzsch 酯转移氢化，BVMO 对应过酸 Baeyer–Villiger。表中置信度 A/B/C 只表示"值得检索"的强度，不构成可迁移性结论，每个候选仍需逐条化学核查。当前 Schneider50k 的 50 个类别与本表**无一对应**，因此它只能作为对照，不能作为候选池。
