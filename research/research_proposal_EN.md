# Retrieving abiotic precedents for new-to-nature biocatalysis

Research direction revised 2026-09-12. The immediate objective is to measure verifiable precedent coverage and representation dependence. This supersedes the earlier emphasis on condition reranking and prospective reaction recommendations.

## Motivation and contribution

Reaction similarity offers a practical route from existing chemistry to candidate biocatalytic transformations. Its value depends on whether relevant nonenzymatic precedents are present in the reference corpus and whether the chosen representation retrieves chemically useful correspondences. Those two conditions should be measured separately.

The proposed contribution is an evidence-linked audit of a defined discovery-event cohort, with reproducible corpus membership, dates, reaction correspondence and retrieval outcomes. It does not depend on obtaining a positive reranking result. Documented corpus gaps and specific retrieval failures can be findings, provided their scope and uncertainty are explicit.

Reaction maps, reaction fingerprints, similarity-based enzyme recommendation and historical evaluation already have precedents. Relevant work includes [enzymatic reaction prediction and mapping](https://pubs.rsc.org/en/content/articlehtml/2021/sc/d1sc02362d), [EnzEngDB](https://academic.oup.com/nar/article/54/D1/D564/8373944), [EC-BLAST](https://www.nature.com/articles/nmeth.2803) and [BridgIT](https://pubmed.ncbi.nlm.nih.gov/30910961/). Their existence rules out presenting a new map or the use of RXNFP as the central novelty. This project makes no priority claim that precedent coverage has never been measured; a focused related-work review remains necessary before publication.

## Current measured result

A completed comparison uses 639 common enzyme-reference structures and 1,988 common patent-reference structures. Across six representation pairs, expected top-10 agreement is 0.70%-11.07% for enzyme-to-patent retrieval. Within-enzyme agreement is 42.82%-62.45%, decreasing to 16.64%-37.71% after shared-source exclusion. This is a descriptive result about the fixed imported reference collection, not encoder accuracy or verified discovery coverage. The [technical report](../outputs/encoder_consistency/REPORT.md) gives methods, exact tables, controls, figures and three structurally inspected cases.

The practical implication is that selecting one representation can materially change which patent records a researcher sees. Establishing whether the differences are helpful requires independent chemical correspondence labels. One selected case also exhibits a mismatch between its encoded transformation and associated publication theme, illustrating why input provenance needs adjudication.

## Primary study design

Use five calibration events to settle discovery granularity, correspondence criteria, date handling and a realistic checking budget. Then freeze a cohort of 20 independent discoveries before inspecting formal retrieval results. Expand toward 40 only if it adds independent chemistry or improves evidence quality. A purposive cohort supports conclusions about that cohort, not an unbiased prevalence estimate for all non-natural enzyme chemistry.

For each event record four separate states: earlier literature precedent, frozen-corpus inclusion, structural eligibility and retrieval outcome. Accepted correspondences require primary experimental locators, catalyst identity, source dates and corpus record IDs. Use transformation-level matching as the primary endpoint and exact substrate matching as a stricter secondary endpoint. Record mechanistic correspondence separately, since the same net transformation can arise through different catalytic pathways.

The main quantity is confirmed candidate coverage C/N, with unresolved U reported and completion bounds C/N to (C+U)/N. A top-k miss is not a demonstrated corpus absence. Conditional Recall@k is calculated only after covered events have been established, while end-to-end accounting retains unqueryable and uncovered events. Stratify by separate transformation, activation and platform labels; these axes may overlap.

Freeze an event-specific temporal rule: the precedent must predate the discovery's earliest verified public disclosure. A modern corpus containing an older reaction supports present-day recovery of historical chemistry, not a claim that the corpus existed at the discovery date. A later single-cutoff historical ranking experiment would require separate seed construction and leakage controls.

## Corpus strategy

The current 2,000-row patent sample is retained for the companion analysis. Complete Schneider50k supplies a within-source expansion, and one wider public source can test whether observed gaps depend on the narrow source selection. Inspect provenance, data roles, dates and preprocessing before encoding at scale. Database size alone does not establish nonenzymatic coverage.

Discovery-paper citations can help verify earlier literature. Any answer-informed supplementation is reported separately from the primary frozen corpus. Public source licenses do not automatically apply to all underlying papers, figures or derived records; source-rich local artifacts remain separate from shareable aggregate results.

## Execution and decision gates

| Stage | Deliverable | Decision |
|---|---|---|
| Completed computational pilot | Common-pool metrics, source controls, figures, code and report | Use disagreement cases to prioritize evidence checks |
| Five-event calibration | Adjudicable event and precedent records | Freeze rules or narrow to one family |
| Twenty-event audit | Confirmed/unresolved coverage accounting and failure categories | Expand only if independent coverage improves |
| Research release | English report, reproducible code, shareable annotations and explicit limits | Seek chemical review before broader claims |

The bottleneck is original-source chemical and chronological checking. A two-week first audit is a working target, not a promised publication deadline. Additional map features, new encoder training, condition scoring and prospective claims are outside the immediate scope. Existing collection, retrieval and visualization code is reused.

## Interpretation and success criteria

A useful result explains what fraction of the selected discoveries have verifiable precedents in the specified corpus, which failures reflect corpus construction or structure processing, and how much retrieval outcomes depend on representation. Success does not require a favored encoder to win. If most cases remain unresolved, the result is an incomplete audit and the appropriate next step is better evidence, not a stronger headline.

The project can then support a specific research statement with measured denominators, reproducible figures and defensible chemical examples. It does not yet support claims of improved experimental success or discovery of new enzyme reactions.

Operational rules are in [coverage_protocol_v02.md](coverage_protocol_v02.md). Earlier Chinese literature reasoning remains available in [the original proposal](non_natural_biocatalysis_reaction_atlas_proposal.md) and [the catalytic-context novelty audit](catalytic_context_novelty_check.md).
