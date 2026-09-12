# Nonnatural Enzyme Reaction Collection Guide

This workbook collects published nonnatural enzyme reactions and their catalytic context for reaction retrieval and research on transferring abiotic chemistry into enzyme systems. Similarity is not evidence of enzyme feasibility.

Use primary articles and their Supporting Information (SI). Unpublished laboratory data are not required. Start with a small, carefully documented batch before collecting entire mutant or substrate libraries.

## What to fill

Only two sheets are imported:

| Sheet | One row represents |
|---|---|
| **Reaction contexts** | One reaction mode, catalytic system and set of conditions |
| **Measurements** | One metric for one product in one experiment |

The workbook also contains Instructions, a Field dictionary, and Examples. **All examples are fictional formatting demonstrations.** They are separate from the empty data sheets and are not scientific records.

Amber headers mark always-required fields. Other fields can be optional or conditionally required. For example, enzymatic records need a protein scaffold, numeric results need a qualifier and unit, and mechanistic descriptions need evidence and a source location.

The English and Chinese workbooks use identical program fields. English dropdown values are converted to the same internal categories during import. You do not need to translate free-text chemical descriptions into Chinese.

## First pass

1. Choose a short curator prefix, such as `WK_`, and use it in every ID you create. Coordinate paper assignments with your colleague to reduce duplicate work.
2. In **Reaction contexts**, record the Context ID, Discovery event ID, DOI/public URL, exact source location, reaction name, catalysis type, protein scaffold, actual metal/cofactor, and conditions as reported. Select **Needs review**.
3. In **Measurements**, refer to that Context ID and record the Measurement ID, Assay ID, source location, compound labels, experimental stage, product detection status, metric, and original result. Add a numeric value, qualifier and unit where appropriate.
4. If structures are not ready, leave Reaction SMILES blank and select **Structure pending**. Accurate compound labels and source locations are sufficient for the first pass.

For the first batch, aim for about five primary papers, one or two contexts per paper, and three to six key assays. An assay can contribute several measurement rows.

## IDs and experimental granularity

| ID | Meaning | When to make a new one |
|---|---|---|
| Discovery event ID | A reported reaction capability | A distinct discovery event; cross-paper equivalence will be reviewed later |
| Context ID | Reaction mode, catalytic system and conditions | Changed metal, ligand, illumination, solvent, procedure or reaction mode |
| Assay ID | A substrate/variant experiment under those conditions | Changed substrate, variant or independent replicate |
| Measurement ID | One metric for one product in that assay | Another metric or another measured product |

For example, `WK_MU2025_A01_YIELD` and `WK_MU2025_A01_EE` may share Assay ID `WK_MU2025_A01` and Context ID `WK_MU2025_C01`.

A new variant does not by itself require a new context, unless its experimental conditions also change. A control without enzyme or without metal generally needs a separate context because the catalytic system changes.

If one assay has multiple products, use the same complete compound-label description on its measurement rows, for example `1a + 2a -> 3a, 4a`. Put the specific product structure in that row's Reaction SMILES and identify the measured product in Notes. Never combine different products' selectivities.

Fifty substrates or one hundred variants do not count as fifty or one hundred reaction discoveries.

## Prioritize informative experiments

Capture a representative transformation, the initial scaffold's activity, the best evolved variant, and informative controls such as no enzyme, no metal, or no light. Intermediate variants are useful when they explain a change in reaction capability.

Keep **initial activity** separate from **evolved outcome**. A high optimized yield does not show that the starting scaffold already performed the reaction efficiently. If the paper does not report starting activity, record that absence rather than estimating it.

## Numeric results, bounds and missing information

| Reported result | Numeric value | Qualifier | Unit | Result as reported |
|---|---:|---|---|---|
| 85% yield | 85 | = | % | 85% yield |
| <1% yield | 1 | < | % | <1% yield |
| >99% ee | 99 | > | % | >99% ee |
| 95:5 dr | Leave blank | Leave blank | ratio | 95:5 |
| n.d. | Leave blank | Leave blank | Leave blank | n.d. |
| Not reported | Leave blank | Leave blank | Leave blank | Not reported |

**Enter the plain number `85` for 85 percent. Do not enter Excel `85%`, whose stored numeric value is 0.85.** The separate Unit field establishes the scale; the importer rejects Excel percentage formatting in Numeric value.

Zero must be explicitly reported. An upper bound is not zero or an exact value. Keep `n.d.` as reported and select **Not detected**; do not invent a detection limit. An experiment not described in the literature is not a negative result.

Use separate rows for yield, conversion, ee and TTN. Keep the analytical method and uncertainty: isolated versus analytical yield, GC/HPLC/NMR, chiral analysis, replicate count, and SD versus SEM when available. Relative activity can exceed 100% of its reference. Preserve a signed ee only if its definition is clear in the source.

## Structures and catalytic context

- Reaction SMILES can use `reactants>>products` or `reactants>agents>products`. Separate components with dots, retain stereochemistry, and do not add manual atom mapping.
- Keep reactants distinct from catalysts, solvents and other agents when the source permits. Do not silently discard original information to improve a similarity score.
- An undetected experiment may describe an explicitly tested target product. Mark it **Tested target**, not Observed product. Do not invent a product structure.
- Record **native metal/cofactor**, **actual experimental metal/cofactor**, and **installation method** separately. Added Cu salt does not by itself establish the active oxidation state or catalytic cycle.
- Preserve buffer, pH, temperature, solvent composition, duration, substrate concentration, enzyme/metal loading, additives, atmosphere and illumination/electron sources with units. A first-pass transcription into Conditions as reported is acceptable.
- Mechanism is optional. If included, separate **Experimental support**, **Author proposal** and **Project hypothesis**, with a precise evidence location. Do not fill a gap using an unsupported AI inference.

## Sources and dates

A DOI alone is insufficient for a measurement: add the main-text/SI page, figure/table, row and compound label needed to locate it. Store the source exactly enough for another curator to reproduce the extraction.

For Earliest public date, check preprints as well as journal publication. If you only know a year, leave the date blank and put the year in Notes. Do not invent January 1. The Date evidence URL should support the verified earliest date.

An abiotic precedent can be entered in the same workbook with catalysis type **Nonenzymatic** and no protein scaffold. Record its real conditions and experimental source; lack of an enzyme report is not a failure label.

## Save and hand over

Keep sheet names, headers and the single header row unchanged. Do not merge cells or insert calculation formulas. There are 200 prepared rows; copy the final row's formatting and dropdowns to extend the table.

Keep first-pass records as **Needs review**. They can be imported before structures are complete. Only reviewed contexts and structures enter default curated retrieval.

Send the saved workbook back through your normal collaboration channel. The project can merge English and Chinese files, retain provenance, and report conflicting IDs without silently overwriting either curator's work. Shared papers and discovery-event labels still need scientific reconciliation.

## Suggested starting literature

These are collection entry points, not pre-extracted datasets:

- [Mu et al., copper-substituted non-haem enzyme ene chemistry](https://www.nature.com/articles/s41929-025-01350-5): metal identity, starting activity, Lewis-acid evidence and controls.
- [Shen et al., copper-substituted nonheme enzyme C(sp3)–N coupling](https://pubmed.ncbi.nlm.nih.gov/40811552/): external partners and initial versus evolved activity.
- [Wang et al., nickel-catalysed enzymatic C(sp2)–S coupling](https://www.nature.com/articles/s44160-026-01003-w): coordination environment, light-driven chemistry and metal/light controls.
- [Kan et al., cytochrome c C–Si bond formation](https://pubmed.ncbi.nlm.nih.gov/27885032/): starting versus optimized variants and the abiotic precedent chain.
- [Miller et al., enzymatic aziridine-to-azetidine ring expansion](https://authors.library.caltech.edu/records/4n9cr-qyw64): competing pathways and the preprint/journal chronology.

Use articles you know well or newer primary papers from your assigned groups where they improve coverage. Always check the actual article and SI before entering experimental values.
