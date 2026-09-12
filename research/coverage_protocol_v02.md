# Abiotic precedent coverage: protocol v0.2

Date: 2026-09-12. Status: operational draft, not preregistered. This is the primary research direction. Encoder agreement is a completed descriptive companion analysis; discovery-event coverage has not yet been measured.

## Question and scope

For an explicitly selected set of independent new-to-nature biocatalytic discoveries, how often can an earlier, chemically corresponding, nonenzymatic precedent be verified in a frozen public reaction corpus? When retrieval fails, is the observed limitation in literature availability, corpus inclusion, structural representation, or ranking?

The first cohort targets 20 reviewed events, with extension to 40 only after a five-event calibration. These are targets, not completed annotations. Include engineered natural enzymes and artificial metalloenzymes; report them separately. Include new catalytic transformations, rather than counting mutants or routine substrate analogues as discoveries. A new platform implementing an already established enzymatic transformation is a platform extension, retained in a supplementary list unless it introduces a distinct reaction mode under the frozen definition. Multiple events from one paper remain clustered by paper. Closely related discovery papers must be flagged for dependence.

The five pilot papers in `coverage_pilot_intake.json` are purposively selected to expose annotation ambiguities. They are not a representative survey. Finalize event granularity, reconcile disagreements, and freeze the formal cohort before looking at its retrieval results. Report calibration events separately if their outcomes informed rule changes. No population-wide prevalence estimate follows from a purposive sample.

## Three distinct observations

1. **Literature precedent:** a primary experimental source demonstrates a corresponding nonenzymatic transformation before the enzyme discovery's earliest verified public date.
2. **Corpus inclusion:** at least one corresponding precedent record is present in the frozen corpus. A paper being cited or searchable online does not establish corpus inclusion.
3. **Retrieval success:** an eligible, verified corresponding record occurs within the stated search budget or top-k list. A similar fingerprint alone is not a verified match.

The principal event-level quantity is the **confirmed candidate coverage fraction**, C/N, where N includes every eligible event in the frozen cohort and C counts events with a verified earlier precedent in the frozen corpus. Publish C, N, and unresolved count U beside the fraction. If unresolved inclusion decisions remain, give the completion bounds C/N to (C+U)/N; these bounds describe unresolved annotations, not a statistical confidence interval. A search-negative event only becomes a resolved corpus absence if the specified corpus-level checking procedure supports that decision. Otherwise it remains unresolved and its search outcome is reported separately.

Also report verified literature precedents/N, search-observed hits/N at the frozen budget, and conditional Recall@k among confirmed covered and structurally queryable events. State all denominators. Structurally unqueryable events remain in overall event accounting and count as pipeline failures for end-to-end recovery, not as demonstrated corpus absences.

No result should be described as experimental success probability. Unreported reactions are not negative experiments. Failure to locate a precedent is not proof that no such chemistry exists.

## Matching rules

The primary match level is the transformation: reaction-center bond changes, reacting functional groups, and the chemically relevant reaction mode must correspond. Define family-specific acceptance rules during calibration. Shareable C-C or C-N bond formation alone is insufficient. Explicitly distinguish intermolecular from intramolecular variants where this changes the claimed catalytic capability.

Record exact substrate/product matches as a stricter secondary level. Record mechanism correspondence separately from transformation correspondence: an enzyme may realize the same net conversion through a different pathway. Stereoselectivity is recorded and can support a stricter endpoint, but is not silently required for the broad transformation endpoint. Mechanistic labels distinguish experimental support, author proposal, and project inference.

For every accepted precedent preserve the DOI or patent publication identifier, experiment locator (scheme/table/SI page and compound IDs), substrate/product structures, actual catalyst, evidence that the example is nonenzymatic, earliest public date and its evidence, corpus record ID, and explicit match rationale. A review citation or database class label is a search lead, not sufficient experimental evidence.

## Dates and frozen inputs

This coverage audit uses an **event-specific cutoff**: eligible precedent public date must be strictly earlier than the verified enzyme discovery public date. Search preprints and author manuscripts as well as the version of record. Where uncertain date intervals overlap, mark the comparison unresolved. Retrieval on a modern public corpus demonstrates recoverability today of older chemistry; it does not establish that the database or extraction pipeline was available at the historical date.

Freeze the event IDs, inclusion reasons, source manifest, corpus content hashes, deduplication policy, structural view, matching rules, search budget, encoder settings, and k values before formal evaluation. Save exclusions. The existing v1 ranking engine uses a single historical cutoff and reviewed seeds: do not feed this event-specific coverage audit directly into that interface or claim the two designs are interchangeable.

Start corpus expansion with complete Schneider50k as a within-source sensitivity analysis. Select one wider public source after checking accessible versions, dates, provenance and reaction roles. Keep the current 2,000-row patent sample for the fixed companion analysis. Larger corpora do not automatically become representative or nonenzymatic. The Lowe release ends in September 2016, so it cannot supply later nonenzymatic precedents; see the [original release](https://figshare.com/articles/dataset/Chemical_reactions_from_US_patents_1976-Sep2016_/5104873).

Backtracking from discovery-paper references is allowed for the literature-precedent audit. Candidates found this way must not be retroactively added to the frozen primary corpus. Report any answer-informed expansion as a separate supplemented corpus. Deduplicate records across sources and retain every original identifier.

## Search budget and decisions

Pilot budget: up to 90 active minutes per event, including primary-source checking; stop earlier only after all required positive evidence has been captured. Record actual time and incomplete steps. Formal budget may be revised once after calibration, then frozen. At the pilot setting inspect the union of top-20 candidates from four encoders, plus recorded text/identifier searches and backward references. Expansion beyond the union is logged as supplementary searching. Query construction uses the enzyme experiment, not the desired precedent answer.

Record corpus coverage as `confirmed_present`, `confirmed_absent_under_protocol`, or `unresolved`. Separately record literature precedent as `confirmed_earlier` or `unresolved`, structure eligibility as `usable` or `unusable`, and search outcome as `verified_hit`, `no_verified_hit_within_budget`, or `not_completed`. Use `confirmed_absent_under_protocol` only with the completed corpus-check rationale; a top-k miss does not qualify. Empty candidate IDs mean unresolved until a reviewer explicitly decides otherwise.

Review all positive correspondences and all claimed absences. A second chemically competent reviewer should independently check the five pilot events and disputed matches before a definitive research release. Preserve reviewer identities, disagreements, and adjudication. Automated extraction can draft records; it cannot be represented as human review.

## Stratification and uncertainty

Use separate multi-label axes: transformation/intermediate family (for example carbene transfer), energy or activation mode (for example photochemical), and platform (for example metal-substituted protein). These are not mutually exclusive. Counts across strata need not sum to N. Unknown mechanisms remain unknown. Do not infer the actual catalytic metal from the native enzyme annotation.

Show counts and denominators first, followed by exploratory uncertainty intervals with paper-level resampling when there are enough independent paper groups. For few groups, emphasize individual events and unresolved decisions rather than apparently precise percentages. Report source/laboratory and year composition. Distinguish small-sample uncertainty from selection bias, which bootstrap intervals do not repair.

## Deliverables and decision gates

The completed companion deliverable is the [encoder agreement report](../outputs/encoder_consistency/REPORT.md). The primary audit deliverables are a reviewed event registry, precedent evidence table, reproducible frozen corpus manifest, coverage accounting figure, and failure analysis. Code and document licenses do not relicense third-party reaction data or model weights.

After five pilot events, either freeze reliable rules or narrow to one family. After 20 reviewed events, decide whether additional events improve independent coverage or merely add analogues. Pause new map features, condition-model training and prospective candidate claims until this evidence chain is usable.

中文执行要点：先核查五个校准事件，再冻结正式队列。分别判断“文献先例存在”“语料收录”“检索找回”，待定项保留在分母并报告范围。当前没有发现事件级覆盖率数字；已有的编码器一致性结果属于独立的描述性分析。
