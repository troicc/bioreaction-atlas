# Running the discovery-event evaluation

For the current primary research question, use the [event-specific precedent coverage protocol](../research/coverage_protocol_v02.md). The interface below implements a different design: fixed-date seed-to-candidate historical ranking. The [completed encoder agreement analysis](../outputs/encoder_consistency/REPORT.md) requires no event labels and is reproduced separately.

The implementation is executable, but the blank protocol intentionally cannot produce a scientific result. The public-reference demonstration is not an evaluation dataset. It lacks verified experimental dates, candidate groups and held-out discovery labels.

## Prepare a common candidate pool

Convert reviewed curator data using `bioatlas curated-corpus`, then create separate indices with `bioatlas encode --backend morgan`, `substrate`, `drfp` and `rxnfp`. Each encoder consumes the same structural view, omitting the agents segment while preserving the original context. `encode` deduplicates the same structural reaction within a domain and retains all evidence rows.

Every evaluated seed/candidate entry must be present in the selected index. Missing entries cause a failure rather than silently changing the pool between methods. Record encoder coverage separately, then freeze a common eligible pool before evaluating rankings.

Fill `templates/evaluation_protocol.json` in a separate local copy:

- `cutoff_date`: ISO date. Seed and candidate evidence must be earlier; held-out events must be on or after it.
- `candidate_pool_protocol`: candidate construction, source coverage and inclusion/exclusion rules established without selecting only later successes.
- `freeze_note`: protocol version/date, what was fixed before inspecting test rankings, and any development-set tuning.
- `seed_entry_ids`: reviewed enzymatic index entry IDs with detected-product evidence.
- `candidates`: objects with `candidate_id` and nonempty `entry_ids`. These are reaction-candidate groups defined independently of later success. An entry cannot appear in several groups.
- `events`: independent discovery events, each with `event_id`, `paper_id`, `first_public_date`, `date_evidence`, `mapping_evidence`, and `candidate_ids`. Use an empty candidate list when a discovery has no covered precedent; explain the absence in mapping evidence.
- `allow_pretrained_exploration`: explicitly set true only to report RXNFP as a separate exploratory analysis when training chronology has not been established.

Each indexed evidence row requires reviewed status, an exact experimental source location, verified earliest public date and date evidence. Source frequency counts distinct sources present in this pool; it is not total literature popularity.

## Optional condition annotations

`condition_annotations` maps an index entry ID to any of `metal`, `activation`, `light` and `medium`. Each feature is an object with:

```json
{
  "value": "a normalized chemical label",
  "source": "primary DOI or URL",
  "source_locator": "exact figure, table or page",
  "source_public_date": "YYYY-MM-DD",
  "evidence_type": "experimental_support"
}
```

`author_proposal` is also accepted; project hypotheses are excluded from this historical condition baseline. Unknown values remain absent. Choose and document the vocabulary before evaluating the test set. English and Chinese free text is not automatically translated into mechanistic facts.

The first condition baseline is deliberately simple: agreement in each of four normalized fields contributes 0.25. Missing fields contribute no agreement and are reported separately. The score is `structural similarity + weight × agreement`, maximized over the same seed/candidate-entry pairs. The default weight 0.15 is an untrained configuration, not an empirically validated optimum or probability. Fix it before test evaluation or select it on separate development events. Missing information can affect rankings; report coverage and perform ablations.

## Run

```bash
.venv/bin/bioatlas evaluate data/local/curated_morgan \
  data/local/frozen_protocol.json --k 1 5 10 --condition-weight 0.15 \
  --out data/local/evaluation_morgan.json
```

Outputs include structural and condition-augmented rankings, the source-frequency baseline, exact uniform-random hit expectations, covered-event and overall Recall@k, and candidate coverage. Tied scores use expected hit probabilities under uniform permutations within a tie, so alphabetical candidate IDs cannot inflate recall.

Confidence intervals resample paper groups, preserving within-paper event dependence. With fewer than two paper groups, intervals are unavailable. Small event sets remain exploratory even if an interval is numerically narrow.

The protocol cannot automatically establish that a date search was exhaustive, a discovery is independent, or a candidate mapping is chemically correct. Those judgments remain part of dataset curation. Unreported candidates stay unlabeled. The output measures recovery of published discoveries, not experimental success probability.
