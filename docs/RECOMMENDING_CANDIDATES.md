# Ranking non-enzymatic reactions for an enzyme platform

This is the project's deliverable: given the reactions an enzyme platform already performs, produce a shortlist of non-enzymatic reactions worth attempting on it, with the evidence attached.

```bash
PYTHONPATH=src .venv/bin/python scripts/recommend_candidates.py \
  --family aminoacrylate_addition --cofactor PLP
```

Output is `candidates.md` with one evidence card per candidate, plus `candidates.json`.

## How the ranking is built

**Seeds define the platform.** Every enzyme reaction with the given cofactor is a seed. A candidate's score is its best match to *any* seed, because a platform is a set of capabilities and proximity to one of them is what matters.

**Both sides are expressed at the shared reactive core.** Seeds are normalised into the intermediate their cofactor forms and both sides are reduced to the unprotected acceptor, because [that was measured](../outputs/candidate_pool/CROSS_FAMILY.md) to be the difference between retrieval working and failing below chance.

**Encoders are fused, and one is excluded on evidence.** Ranks from Morgan difference, substrate Morgan and DRFP are combined by reciprocal rank fusion. RXNFP is left out by default because it was measured at 0.53× the pool composition on this family while the other three reach 3.58×–4.30×. That exclusion is a measurement, not a preference, and `--fuse` overrides it.

**Reactions the platform already performs are dropped**, with the covering seed named. A recommendation to do what the enzyme already does is not a recommendation.

**One candidate per source paper.** Without this, a shortlist fills with substrate variations from a single publication.

## What the output does not claim

There is no feasibility score and no success probability. Candidates are ordered by structural proximity in a space measured to work for that family, and the evidence is shown so a chemist can judge. Multiplying hand-chosen factors into a number would invent precision that does not exist.

Each card ends with what remains undecided: whether the enzyme platform supplies the same activation, what the recorded catalyst or medium provides that a protein cannot, and what a first experiment would need to distinguish. Mechanism is not recorded and must be read from the primary source.

## How firm a shortlist is, and why it differs by family

A candidate is **firm** when every fused encoder ranks it in the top 10% of the pool. The two families behave completely differently:

| Platform | Family | Firm candidates |
|---|---|---:|
| haem | metal carbene | **7 of 8** |
| PLP | dehydroamino acid addition | **0 of 10** |

For carbene the shortlist can be read top-down. For PLP it cannot: the three representations agree on which *family* to search — that is the 3.58×–4.30× result — but no candidate within the family is ranked consistently high by all of them. The best PLP candidate's worst rank is 43 of 303.

The PLP shortlist is still useful, and its chemistry is right: thiophenol, naphthalenethiol and benzylamine additions to dehydroalanine, which is the transformation a cysteine synthase performs on the aminoacrylate. **Read it as a shortlist of ten papers, not as a ranking of ten.** Ten papers is an afternoon; a false ordering is a wasted experiment.

## A retrospective check

For the haem platform, the shortlist includes methyl phenyldiazoacetate reacting with phenyldimethylsilane — carbene Si–H insertion, the transformation a cytochrome c variant was engineered to perform in 2016. This is **not a prediction**: enzymatic Si–H insertions are in the seed set, so the tool ranked highly an abiotic reaction whose enzymatic counterpart exists. It is evidence that the ranking tracks real transferability, not evidence that the tool discovers new chemistry.

中文要点：这是项目的交付物——给定某酶平台已有反应，输出值得尝试的非酶反应短清单及其证据。排序融合三种经测量可用的表示（RXNFP 因在该家族测得 0.53 倍而默认排除），两侧均归约到共享反应核心，剔除平台已做过的反应，每篇论文只取一条。**不给可行性分数或成功概率。** 卡宾族 8 条里 7 条"firm"（三种表示都排进前 10%），PLP 族 0/10——三者只在**家族**层面一致，在**家族内排序**上不一致。因此 PLP 清单应当作"十篇待读论文"，而非"十个排好序的候选"。
