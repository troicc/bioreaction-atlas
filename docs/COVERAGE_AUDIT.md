# Running the discovery-event coverage audit

Operational companion to [protocol v0.2](../research/coverage_protocol_v02.md). The protocol defines the rules; this page is the loop you actually run.

The audit answers one question per event: **can an earlier, chemically corresponding, nonenzymatic precedent be verified in the frozen corpus?** It records four independent states so that a failure can be attributed to literature availability, corpus inclusion, structural representation or ranking.

## Current status

No event-level coverage number exists yet. Check at any time:

```bash
PYTHONPATH=src .venv/bin/python scripts/coverage_status.py
```

This prints C, U, N, the completion bounds, and the open checks per event. It runs at any completeness and never fills an unresolved decision with a guess.

## The per-event loop

Budget is 90 active minutes per event at the pilot setting. Steps 1–2 are irreducible human chemistry; the tooling exists so the budget is spent there rather than on bookkeeping.

**1. Extract the transformation from the primary source.** Read the paper and SI. Record in `research/coverage_registry.json`:

| Field | Requirement |
|---|---|
| `reaction_smiles` | The event's net transformation. One transformation per event, not one per mutant or substrate analogue. |
| `event_experiment_locator` | Scheme/table/SI page and compound IDs. |
| `event_earliest_public_date` | Earliest **verified** disclosure, preprint included — not the journal issue date. |
| `event_date_evidence` | Where that date came from. |
| `strata` | Separate `transformation`, `activation` and `platform` labels; these axes overlap and need not sum to N. |

Then set `structure_eligibility` to `usable`. A structurally unqueryable event stays in the denominator and counts as a pipeline failure for end-to-end recovery — it is **not** a corpus absence.

**2. Generate the candidate worksheet.**

```bash
PYTHONPATH=src .venv/bin/python scripts/event_worksheet.py PILOT_01
```

This retrieves each encoder's top-20 from the frozen pool, takes the union, and writes `data/local/coverage/<event_id>/worksheet.md` with every candidate's structure, provenance and a four-point check list, plus a blank adjudication block. Expect the union to approach 4×20: the encoders largely disagree, so the reading load per event is close to the sum rather than the maximum of their lists.

The worksheet decides nothing. Retrieval order is not chemical relevance, and a candidate's absence from it is not a corpus absence.

**3. Adjudicate.** For each accepted precedent, fill the block and copy it into that event's `precedents`. Every field is mandatory: a review citation or database class label is a search lead, not experimental evidence. The precedent's `first_public_date` must strictly predate the event's.

**4. Set the four states.** The validator enforces the protocol, so an overstated annotation fails rather than propagating:

| State | Values |
|---|---|
| `literature_precedent` | `confirmed_earlier`, `unresolved` |
| `corpus_coverage` | `confirmed_present`, `confirmed_absent_under_protocol`, `unresolved` |
| `structure_eligibility` | `usable`, `unusable` |
| `search_outcome` | `verified_hit`, `no_verified_hit_within_budget`, `not_completed` |

Rules the validator will not let you break:

- `confirmed_present` needs at least one fully evidenced precedent, and cannot coexist with an unresolved literature precedent.
- `confirmed_absent_under_protocol` needs both `corpus_check_procedure` and `corpus_absence_rationale`, and a completed search. **A top-k miss does not qualify.**
- `verified_hit` must name the corpus record it matched.
- Any resolved decision must name its reviewer. A wholly unresolved row needs none — that is the honest default.

**5. Record time and incomplete steps** in `search_minutes` and `notes`.

## After five events

Either freeze reliable rules or narrow to one family. Report calibration outcomes **separately** if they informed rule changes, then freeze the formal cohort *before* looking at its retrieval results. A purposive sample supports conclusions about that cohort only, never a prevalence estimate for non-natural enzyme chemistry.

## What the resulting number is not

`C/N` is a confirmed candidate coverage fraction over this cohort. It is not an experimental success rate, not a retrieval accuracy, and not a probability that any candidate reaction will work. Unreported reactions are unlabeled, not failed experiments. Completion bounds `C/N` to `(C+U)/N` describe unresolved annotations, not statistical confidence.
