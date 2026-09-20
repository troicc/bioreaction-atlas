# Catalytic context reorders the shortlist, and how much depends on the family

Technical note, 2026-09-20.

## What was asked

Structural proximity produces a shortlist whose ordering is not trustworthy: for the PLP platform no candidate is ranked in the top 10% by all three working representations. The project's original proposal argued that **catalytic context** — what supplies the reactivity, in what medium, at what temperature — should carry the missing signal. This tests that.

## What could not be done, and why

The intended test was a labelled one: define candidates that are "known transferable" by their similarity to real enzyme reactions, then ask whether context predicts that label. It does not survive contact with the data. At a 0.3 similarity threshold the carbene pool yields 23 positives and the dehydroamino acid pool **3**, and the counts move several-fold with the threshold. Any result would be an artefact of where the line was drawn. This is the same finding as the exact-match check: 1 of 639 enzyme reactions has a ≥0.95 abiotic match, so transferability lives at the transformation level and labels cannot be harvested.

So context is not scored against transfer outcomes. It is reported as **obstacles**: what a recorded procedure would have to change to run in a protein. Each is a statement about what proteins tolerate, which needs no transferability labels to be defensible.

## What is measured

`src/bioreaction_atlas/transfer.py` reports per candidate: medium class, temperature against a 0–60 °C protein range, whether the catalyst's metal is one the platform already carries, whether an external ligand supplies coordination the scaffold would have to replace, and reagents that denature proteins. Unrecorded conditions are counted **separately** as unknown, never as cleared, because counting missing data as zero obstacles ranks empty records first.

The count is a sort key, explicitly not a feasibility score. No axis disqualifies a reaction: the project's rules forbid absolutes such as "organic solvent means infeasible".

## Result: the answer is family-dependent

Mean obstacles in the top-10 under each ordering, against the pool's own mean:

| Ordering | PLP platform | haem platform |
|---|---:|---:|
| *pool average* | *0.9* | *2.0* |
| Structure (fused encoders) | **0.1** | **1.9** |
| Fewest obstacles | 0.0 | 0.0 |
| Most literature variations | 1.4 | 2.2 |
| Most recent | 0.8 | 1.9 |
| Random | 1.0 | 1.6 |

**For PLP, structural ranking already finds context-compatible chemistry without being told to** — 0.1 obstacles against a pool average of 0.9. Half that pool (49.0%) is obstacle-free to begin with, because PLP chemistry is metal-free, aqueous and mild, and so are its closest abiotic analogues. Context reranking adds almost nothing.

**For carbene it adds a great deal.** Structural ranking returns 1.9 obstacles, indistinguishable from the pool average of 2.0: it surfaces the rhodium-in-dichloromethane chemistry the pool is mostly made of. Only 5.4% of that pool is obstacle-free. Ordering by obstacles surfaces entirely different reactions — the two top-10 lists share **0 of 10**.

## What the obstacle ordering surfaces for a haem platform

| # | Obstacles | Reaction | Conditions |
|---:|---:|---|---|
| 1 | **0** | Doyle–Kirmse S-ylide rearrangement | **hemin, water, 20 °C** |
| 2 | 0 | S–H insertion, 97% | Bu₄NI, DMF, 60 °C — **metal-free** |
| 3 | 0 | S–H insertion, 79% | B(C₆F₅)₃, neat, 20 °C — **metal-free** |
| 5 | 0 | diazo to ketone, 84% | Bu₄NI, MeCN, 20 °C — **metal-free** |
| 6 | 1 | S–H insertion | Rh₂(OAc)₄, dioxane, 20 °C |

The first is an **iron porphyrin catalysing carbene transfer in water at room temperature** — the platform's own cofactor, already operating under conditions a protein lives in. Three more are **metal-free** carbene chemistry, meaning the transformation does not require the metal the chemist used and a haem scaffold is not being asked to reproduce it. Structure-only ranking surfaced none of these.

## Limits

Obstacles are read from recorded fields, not from the primary procedure. Coverage is 83–98% for catalyst, 82–90% for solvent and 54–83% for temperature; the rest is unknown and reported as such. A reaction with few obstacles is not thereby transferable, and one with several is not thereby impossible — enzymes work in cosolvents, metals are substituted into scaffolds, and both are published routine.

The comparison is between orderings of the same filtered shortlist, on two families and two platforms. Nothing here measures whether any candidate would actually work.

中文摘要：原计划用"已知可迁移"标签检验催化环境是否有用，但标签构造不成立——0.3 阈值下卡宾池仅 23 个正样本、PLP 池仅 **3 个**，且随阈值成倍变化。因此改为报告**迁移障碍**：一条已记录的操作要在蛋白体系中运行需要改变什么。结果**依家族而异**：PLP 平台上结构排序本身已给出 0.1 障碍（池均值 0.9），环境信息几乎无增益；**卡宾平台上结构排序给出 1.9，与池均值 2.0 无异**，而按障碍排序浮出完全不同的 10 条（重叠 0/10），首位是 **hemin 在水中 20°C 催化的卡宾转移**，另有三条**无金属**卡宾化学。障碍数是排序键，**不是可行性分数**。
