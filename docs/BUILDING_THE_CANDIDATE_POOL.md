# Building the non-enzymatic candidate pool

The enzyme side already exists. What is missing is a pool of abiotic reactions that could plausibly contain an answer. This page is the loop from a Reaxys/SciFinder export to reactions retrievable in the same space as your enzyme seeds.

Read [the activation-family map](../research/activation_family_map.md) first: it decides *what* to export, which matters far more than how many rows you get.

## Why not just use a bigger public dataset

Schneider50k's 50 classes are Boc protection/deprotection, amide coupling, Suzuki, reductive amination, nitro reduction, esterification, halogenation and similar routine transformations. None corresponds to any activation family in the map, and only 7.6% of its rows carry a transition metal in the agents segment. Scaling that source up does not make the answer appear. The pool has to be selected by activation mode, which means literature search, not a bulk download.

The published rxnfp reaction atlases do not solve this either. All three are patent-derived: the Schneider 50k atlas, the 445k-reaction [USPTO 1k TPL](https://rxn4chemistry.github.io/rxnfp/) atlas built from Lowe's USPTO database, and the Pistachio atlas built from patent text mining. Going from 50k to 445k reactions adds coverage of routine transformations, not of methodology chemistry, and Lowe's release ends in September 2016 so recent photoredox and radical methods are absent by construction.

USPTO 1k TPL is still the better **background and negative control** pool than the current 2,000-row Schneider sample: it is free, far larger and much more diverse. A retrieval method that ranks routine patent chemistry above genuine family matches is telling you something useful. Swapping it in is worthwhile; expecting it to contain the answer is not.

A cheap, decisive check before committing to any of this: run a diazo substructure query over those 445k reactions and count how many carbene-transfer reactions a large patent corpus actually holds. A small number is a quantified, citable corpus gap and a stronger argument than any amount of reasoning about it.

## One family at a time

Start where you already hold enzyme seeds on both sides. The pinned V6 file is 1,194/1,342 rows haem and 117 PLP, so:

1. `metal_carbene` — Rh₂(OAc)₄, Cu(I)/bisoxazoline, Co(II)- and Ir-porphyrin carbene transfer. Handles to search on: diazo reagents, cyclopropanation, Si–H / N–H / S–H / O–H insertion, Doyle–Kirmse, Buchner.
2. `enamine_iminium` — proline and imidazolidinone organocatalysis. Handles: aldol, Mannich, Michael, aza-Michael, α-functionalization.
3. `nhc_umpolung` — the ThDP analogue. Handles: benzoin, cross-benzoin, Stetter, homoenolate, acyl azolium.

Then extend down the map. 200–500 reactions per family is enough for a first pass; family breadth beats row count, and repeated substrate series from one paper add rows without adding independent chemistry.

## What to query on

**Aim for precision, not recall.** You need 200-500 diverse reactions per family, not every reaction of that type. One high-precision catalyst name returns a coherent set immediately; a carefully constructed comprehensive query returns tens of thousands of rows you then have to triage. The second is slower and gives a worse pool, because repeated substrate series from a handful of papers crowd out source diversity.

So: **one catalyst name, two filters, stop.**

### The recipe

In Reaxys, search Reactions with the query builder:

1. One field — **Catalyst**, **Reagent**, or **Reaction name** — set to the single handle below.
2. Filter **Document type = Journal**. This drops patents, which are your background pool, not your candidate pool.
3. Cap the set. If it returns more than about 1,000, narrow the publication-year range rather than adding query terms.

### One handle per family

| Family | Field | Query | Note |
|---|---|---|---|
| `metal_carbene` | Catalyst | `Rh2(OAc)4` | The classic dirhodium carbene catalyst; covers cyclopropanation and X–H insertion, including the Si–H chemistry of PILOT_01 |
| `nhc_umpolung` | Reaction name | `benzoin condensation`, then `Stetter reaction` | Named reactions give small, clean sets |
| `enamine_iminium` | Catalyst | `L-proline` | High precision, very large literature |
| `metal_nitrene` | Catalyst | `Rh2(esp)2` | The standard C–H amination catalyst |
| `baeyer_villiger` | Reaction name | `Baeyer-Villiger` | Named |
| `transfer_hydrogenation` | Reagent | `Hantzsch ester` | Diagnostic reagent |
| `photoredox_radical` | Catalyst | `Ir(ppy)3`, then `4CzIPN` | Mostly post-2016, so absent from any USPTO corpus |
| `hat_oxidation` | Catalyst | `Fe(PDP)` | Small, well-defined literature |
| `cation_cyclization` | — | leave for later | No single diagnostic handle; needs structure queries |
| `alkylation_sam`, `acyl_transfer`, `lewis_acid` | — | leave for later | Too broad to bound with one handle |

Each is one string. If a handle returns too little, add its obvious siblings one at a time — `Rh2(esp)2` and `Cu(MeCN)4PF6` for carbene, `Ru(bpy)3Cl2` for photoredox — rather than building a compound query up front.

### Drawing a structure query

The arrow assigns the role. Fragments **left** of the arrow are reactants, fragments **right** are products, and an empty product side means any product. Drawing a structure with no arrow leaves the role unset, which is how a diazo query returns diazo-transfer reactions that *make* the reagent instead of using it.

Several fragments on the same side are ANDed: all must be present. Resist that for a first pool. The diagnostic group is one reactant; the partner it reacts with is exactly the variety you want. Constraining a dehydroamino acid query to one carbon nucleophile collapses the family to a single substrate class.

Check that the search runs as a **substructure** query, not exact match, or N-acyl, ester and β-substituted variants are all missed. Page 1 of any export prints the query log — it states what was actually run, for example `Search as: Substructure: on all atoms`.

### Settings that silently widen a structure query

Two defaults cost precision, and one of them is catastrophic for an enamide-like query.

**Additional ring closures** lets the drawn atoms sit inside extra rings. For a dehydroamino acid skeleton `C=C(N)C(=O)` that admits every **indole-2-** and **pyrrole-2-carboxylate**, because their ring carbon carries the ring nitrogen, the ring double bond and the ester at once. A dehydroalanine query with it enabled returned 619,779 reactions whose top hit was a nitro reduction on an indole ester. Uncheck it.

**Tautomers** expands an enamine to its imine. Dehydroalanine becomes 2-iminopropanoate, so α-imino esters enter the set — electrophilic at the imine carbon, a different activation mode from conjugate addition at the β-carbon. Uncheck it.

If a query is still too broad, set the key bond's topology to **chain** rather than ring. That excludes cyclic dehydroamino acids, which is a real loss, but purity matters more than recall for a first pool.

The import screen rejects aromatic matches regardless, since its SMARTS requires aliphatic alkene carbons. Fixing the query still matters: hundreds of thousands of hits cannot be exported, and the daily export budget is small.

### When to stop

Stop at roughly 300 reactions from **at least 30 different papers**. Source diversity is the binding constraint, not row count: fifty substrate analogues from one paper are one piece of independent chemistry, and they will distort retrieval exactly the way the same-publication control in the [encoder report](../outputs/encoder_consistency/REPORT.md) showed.

**Do one family end to end before starting a second.** Import it, encode it, run retrieval against your enzyme seeds, look at what comes back. That tells you whether the handle picked up the right chemistry, and it costs one afternoon. Collecting all ten families first and discovering the loop does not work is the expensive mistake.

### If you later need more coverage

Only after the loop works is it worth the extra effort: draw the diazo group `C=[N+]=[N-]` as a reactant substructure to reach carbene chemistry beyond dirhodium; add sulfoxonium ylides and N-sulfonyl triazoles as diazo-free carbene precursors; intersect with product-side transformations (alkene to cyclopropane, X–H to X–CHR). Carbene chemistry is classified inconsistently across sources, so the reactant substructure reaches more of it than any reaction-type label. Do this to extend a working pool, never to build the first one.

## Search at the reaction level, not the document level

A text or abstract search returns **documents**. Switching that result set to its Reactions tab gives you every reaction in those papers — including all the substrate-preparation steps. A carbene methodology paper contains its carbene reactions plus the amide couplings, Boc protections, Suzuki couplings and ester hydrolyses used to make the substrates, which is exactly the routine chemistry the pool is meant to exclude.

Query the reaction record instead: in the query builder, search **Reactions** with the **Catalyst** field set to the handle. That returns only reactions whose catalyst is annotated as such, so preparation steps never enter the set. Typing the handle into quick search does a full-text lookup and gives you documents; selecting the Catalyst field gives you reactions.

The import screen below is a safety net for whatever still gets through. It is not a substitute for querying at the right level.

## Give the structure a reaction role

A bare diazo substructure query returns around 357,000 reactions, and its top facets are triethylamine, DBU, potassium carbonate and sulfonyl azides. Those are **diazo-transfer** conditions: the diazo group is the *product*, and the reaction is making the carbene precursor rather than using it.

Mark the structure as a **reactant**, by drawing it on the left of a reaction arrow in the structure editor rather than as a standalone structure. Then narrow with the result facets: `Reagent/Catalyst` lists `dirhodium tetraacetate` directly, and **Limit To** applies it without spending another query. Use `Filter by value` inside the facet to add the other carbene metals if you want breadth.

The import screen catches this class of contamination anyway — it looks for the diagnostic group on the reactant side only, so a diazo-transfer reaction fails it — but filtering in the interface saves an export.

## Exporting from Reaxys

**Export from the Reactions tab, not Documents.** A result set has separate Documents, Substances and Reactions views. The Documents view's dialog is titled *Export citations* and produces a bibliography; ticking "Include reactions" there attaches reaction information to citation records rather than giving you a reaction table. Switch to Reactions first.

**Choose `RD File`.** Of the offered formats, RD File (.rdf) is the reaction interchange format: it carries the reaction structures, the condition fields and the citation together. PDF/Word/Literature-Management outputs are for reading. Excel and tab-delimited outputs flatten or drop the structures. XML works but is more awkward to parse.

**Exports are rate-limited** — the dialog states the daily attempt count. Spend the first one on 20-30 reactions to confirm the fields are there before exporting the real batch.

Then convert. The reader makes no assumption about field names, because those differ by database and subscription:

```bash
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf --list-fields
```

That prints every data field the file actually carries, with how many records have it and an example value, plus a suggested mapping. Check the suggestion, then write the CSV:

```bash
PYTHONPATH=src .venv/bin/python scripts/rdf_to_csv.py export.rdf \
  --family metal_carbene --out carbene.csv --map source_doi="CIT.DOI"
```

`--map` overrides anything the guess got wrong. If no DOI field is mapped the converter warns, because the importer requires a literature identifier and would otherwise skip every row.

## Export settings that matter


Whatever the interface, the export must retain:

1. **Reaction SMILES, with reagents** — if the export offers a with-agents option, take it. That segment is the only bulk source of catalyst and solvent information.
2. **Catalyst, reagent and solvent as separate columns** where available. They override the parsed agents segment.
3. **DOI and year.** A year alone is fine; it is stored as `source_year` and never becomes a verified date.
4. **A locator** — scheme, table or entry number, not just the paper.

Export caps and text-and-data-mining terms differ by subscription. Systematic bulk download is restricted under most commercial database licences, so confirm the permitted scope with your librarian before exporting at scale, and record what was permitted alongside the corpus. This matters for what can later be redistributed: derived aggregate results are usually shareable when the underlying records are not.

### If you already exported as PDF

A PDF export renders structures as images, so it cannot supply reaction SMILES and cannot build a pool. It does carry a good citation layer — one row per literature condition, with the yield, the full condition sentence and a complete journal citation. Recover it rather than discarding the export:

```bash
PYTHONPATH=src .venv/bin/python scripts/reaxys_pdf_citations.py export.pdf
```

Then re-export the same query as RD File for the structures, and join the two on `reaxys_reaction_id`. The PDF's per-reference conditions and citations are often more complete than the corresponding RD File fields, and they are what the coverage protocol needs for `source_locator` and date evidence.

Note that one reaction carries several literature conditions. A 1,000-reaction export is therefore closer to 1,800 condition rows from several hundred papers — count papers, not rows, against the stop rule.

### What a Reaxys RD File actually contains

ChemDraw renders only the structures, so an RD File looks empty of conditions when opened there. The conditions are in `$DTYPE`/`$DATUM` fields alongside each reaction — a real 1,000-reaction export carried 37,755 of them.

Reaxys stores **one indexed block per literature variation**: `ROOT:RXD(1):RGT`, `ROOT:RXD(2):RGT` and so on, with `RX_NVAR` giving the count. Each variation is a different paper, catalyst, yield and year for the same transformation, so the converter explodes them into separate rows by default. A 1,000-reaction export became 2,508 variations from 1,075 distinct papers.

| Reaxys field | Meaning |
|---|---|
| `RIREG`, `RX_ID` | Reaction registry number; the join key to a PDF export's `Rx-ID` |
| `RXD(n):RGT`, `RXD(n):CAT` | Reagent and catalyst — split across two fields, so both are combined for screening |
| `RXD(n):SOL`, `:T`, `:TIM` | Solvent, temperature, time |
| `RXD(n):NYD` | **Numeric yield.** `YPRO` is the product *name* and must never be mapped to a yield |
| `RXD(n):citation` | `<docid>; <document type>; <authors>; <journal>; vol; (year); pages` |
| `RXD(n):TXT`, `:LCN` | Full experimental procedure, and its locator |

There is no DOI field, so the citation string serves as the publication identifier.

**Document type is filtered.** The citation's second field gives it. Retracted articles, reviews and conference abstracts are rejected by default: a retraction is not evidence, and the protocol treats a review as a search lead rather than a primary experimental source. The real export contained one retracted article, ten reviews and ten conference papers. Articles, patents, letters and notes are kept with their type recorded, so journal methodology can later be separated from patent background.

## Export columns

Export to CSV with these headers. `templates/methodology_export.csv` is the template, with one clearly-marked example row to delete.

| Column | Required | Notes |
|---|:--:|---|
| `reaction_smiles` | ✅ | `reactants>agents>products` or `reactants>>products`. Keep the agents segment if the export offers it — that is where the catalyst and solvent live. |
| `family` | ✅ | One id from the map. `python -c "from bioreaction_atlas.activation import FAMILIES; print(*FAMILIES)"` lists them. |
| `source_doi` | ✅ | DOI or patent number. |
| `source_year` | | Kept as a year. **Never promoted to a verified date** — see below. |
| `catalyst`, `reagents`, `solvent`, `temperature_c`, `time_h`, `loading` | | Exported condition columns override whatever the agents segment implies. |
| `yield_percent`, `reaction_name`, `source_locator`, `external_id`, `notes` | | `source_locator` should be a scheme/table/entry, not just the paper. |
| `first_public_date`, `date_evidence` | | Only fill these with an evidenced `YYYY-MM-DD`. Leave blank otherwise. |

Unrecognized columns are reported and ignored, so an oversized raw export is fine.

## Import, encode, retrieve

```bash
PYTHONPATH=src .venv/bin/python scripts/import_methodology.py carbene_export.csv \
  --out data/local/pools/carbene.json --prefix CARB --report data/local/pools/carbene_skipped.json

PYTHONPATH=src .venv/bin/python -m bioreaction_atlas.cli encode data/local/pools/carbene.json \
  --backend morgan --allow-unreviewed --out data/local/pools/carbene/morgan
```

Every rejected row is reported with a reason; nothing is dropped silently. Repeat `encode` per backend (`--model-dir data/local/public/rxnfp` for RXNFP) and the pool is queryable with `bioatlas neighbors` and the existing evidence cards.

## Three rules the tooling enforces

**A publication year is not a date.** Reaxys gives you a year; the historical test needs a verified earliest public disclosure, preprints included. `first_public_date` stays null unless you supply evidence, so a year can never silently become a cutoff.

**No mechanism is inferred.** The family label records why a reaction was imported, not how it works. `mechanism` stays empty and `mechanism_evidence` stays `未说明` until someone reads the paper. A detected metal is a species present in the recorded agents, nothing more.

**Off-family rows are rejected.** A reaction is kept when its reactant side carries the family's diagnostic group — a diazo for `metal_carbene`, an azide or iminoiodinane for `metal_nitrene` — or when its recorded catalyst carries a diagnostic metal or catalyst name. Either alone suffices, since some sources annotate the catalyst and not the precursor. Palladium is deliberately not diagnostic for carbene chemistry: Suzuki and Sonogashira steps are the commonest contaminant and Pd is not the haem analogue. Rejected rows are reported with a reason, and `--no-screen` disables the filter. Families with no clean screen are left unscreened rather than given a loose one.

**Imported is not reviewed.** Records carry a literature identifier and have not passed primary-source review, exactly like the pinned patent references. Structural similarity to a seed is a reason to read the paper, never a feasibility claim.

## Keep family as a layer, not as geometry

Encoding every family into one space clusters by substrate scaffold, not activation mode — the failure the map opens with. Amide formation, Pd-catalysed C–N coupling and carbene N–H insertion all form a C–N bond and are not interchangeable. Use `activation_family` for colouring and filtering the map; never let it produce the coordinates.

## Two pools, two purposes

Filtering a pool down to only the chemistry you were looking for is circular if that
same pool is then used to measure retrieval. The carbene pool showed it directly: once
the import screen had removed everything off-family, every encoder scored 100% at
top-10 and the number carried no information.

The fix is not to widen the filter until it feels fair. It is to build two artefacts.

**A discovery pool** is what you browse for candidates. Narrow is correct here — you
want good candidates, and selecting the reaction classes that match the activation
family is the point, not a bias.

**An evaluation pool** is what a retrieval measurement runs against, and it **must**
contain the mixture. Sample it without class filtering, so the dominant off-target
chemistry of that substrate class comes along: hydrogenations and substitutions for a
dehydroamino acid, diazo transfer for a diazo compound. Import it with `--no-screen`.
Every row is still labelled — `context.in_family` records the verdict and
`context.family_screen` its reason — so the label is assigned by a structural rule
stated in advance, never by which rows looked right.

The measurement then asks something falsifiable: does retrieval rank the in-family
reactions above the off-family ones drawn from the same substrate class? That is a
harder and more honest question than whether a pre-purified pool returns pure results.

What matters for bias is **when** the inclusion rule is fixed, not how narrow it is.
Choosing classes by eye after reading the first page of hits is post-hoc; writing the
rule down and applying it is not.

## The route a substructure query cannot see

A query for the acceptor finds only reactions where the acceptor is written as a
reactant. But an abiotic route can form it **in situ from the same precursor the
enzyme uses** — cysteine or serine eliminating to a dehydroalanine that is consumed
without ever appearing — and those reactions carry no acceptor in their reactants.
A pool built from an acceptor query misses that whole route by construction, which is
the same blind spot the enzyme side had before normalisation.

`import_methodology.py --normalize` rewrites such a precursor into the intermediate
before the family screen runs, so the reaction is admitted rather than rejected. The
stored SMILES is the normalised one and `reaction_smiles_as_reported` keeps what the
source actually said, so nothing is lost.

To find them, query the **transformation** rather than the acceptor: draw the
precursor on the left with its β-heteroatom, and the β-substituted product on the
right using the editor's any-atom **A** for the incoming nucleophile.

```
left :  X–CH2–CH(N)–C(=O)      X = OH, SH, OMs, OTs, halide
right:  A–CH2–CH(N)–C(=O)      A = any atom
```

This also picks up direct substitution at the β-carbon, which is chemically the right
call: it reaches the same product, and a cysteine synthase gets there through the
aminoacrylate regardless of how a chemist did it. The transformation is the precedent;
the route is a separate fact to record.

Reagent handles for the deliberate in-situ route, if the structural query returns too
much: 2,5-dibromohexanediamide, the standard reagent for converting cysteine to
dehydroalanine in peptides; O-mesyl or O-tosyl serine; selenocysteine oxidative
elimination.

## What makes a result

Once two or three families are in, the question becomes testable: **given an enzyme seed, does retrieval surface reactions from the chemically corresponding family above routine patent background?** That is a measurable, falsifiable claim about candidate prioritization, it uses the family labels as the ground truth you currently lack, and it needs the same-publication exclusion control from the [encoder report](../outputs/encoder_consistency/REPORT.md) so a scaffold series cannot inflate it.

中文要点：候选池必须按活化方式选，不能靠下载更大的通用数据集——Schneider50k 的 50 个类别与活化家族表无一对应。先做你两边都有种子的家族（金属卡宾、PLP/烯胺-亚胺离子、ThDP/NHC），每族 200–500 条即可，来源多样性优先于底物数量。工具强制三条：出版年份不等于已核实最早公开日期；不推断机理；imported 不等于已核对。家族标签只作为地图图层，不参与坐标计算。
