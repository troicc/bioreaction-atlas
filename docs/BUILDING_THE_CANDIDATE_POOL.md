# Building the non-enzymatic candidate pool

The enzyme side already exists. What is missing is a pool of abiotic reactions that could plausibly contain an answer. This page is the loop from a Reaxys/SciFinder export to reactions retrievable in the same space as your enzyme seeds.

Read [the activation-family map](../research/activation_family_map.md) first: it decides *what* to export, which matters far more than how many rows you get.

## Why not just use a bigger public dataset

Schneider50k's 50 classes are Boc protection/deprotection, amide coupling, Suzuki, reductive amination, nitro reduction, esterification, halogenation and similar routine transformations. None corresponds to any activation family in the map, and only 7.6% of its rows carry a transition metal in the agents segment. Scaling that source up does not make the answer appear. The pool has to be selected by activation mode, which means literature search, not a bulk download.

Keep the existing patent pool as a **negative control**: a retrieval method that ranks routine patent chemistry above genuine family matches is telling you something useful.

## One family at a time

Start where you already hold enzyme seeds on both sides. The pinned V6 file is 1,194/1,342 rows haem and 117 PLP, so:

1. `metal_carbene` — Rh₂(OAc)₄, Cu(I)/bisoxazoline, Co(II)- and Ir-porphyrin carbene transfer. Handles to search on: diazo reagents, cyclopropanation, Si–H / N–H / S–H / O–H insertion, Doyle–Kirmse, Buchner.
2. `enamine_iminium` — proline and imidazolidinone organocatalysis. Handles: aldol, Mannich, Michael, aza-Michael, α-functionalization.
3. `nhc_umpolung` — the ThDP analogue. Handles: benzoin, cross-benzoin, Stetter, homoenolate, acyl azolium.

Then extend down the map. 200–500 reactions per family is enough for a first pass; family breadth beats row count, and repeated substrate series from one paper add rows without adding independent chemistry.

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

**Imported is not reviewed.** Records carry a literature identifier and have not passed primary-source review, exactly like the pinned patent references. Structural similarity to a seed is a reason to read the paper, never a feasibility claim.

## Keep family as a layer, not as geometry

Encoding every family into one space clusters by substrate scaffold, not activation mode — the failure the map opens with. Amide formation, Pd-catalysed C–N coupling and carbene N–H insertion all form a C–N bond and are not interchangeable. Use `activation_family` for colouring and filtering the map; never let it produce the coordinates.

## What makes a result

Once two or three families are in, the question becomes testable: **given an enzyme seed, does retrieval surface reactions from the chemically corresponding family above routine patent background?** That is a measurable, falsifiable claim about candidate prioritization, it uses the family labels as the ground truth you currently lack, and it needs the same-publication exclusion control from the [encoder report](../outputs/encoder_consistency/REPORT.md) so a scaffold series cannot inflate it.

中文要点：候选池必须按活化方式选，不能靠下载更大的通用数据集——Schneider50k 的 50 个类别与活化家族表无一对应。先做你两边都有种子的家族（金属卡宾、PLP/烯胺-亚胺离子、ThDP/NHC），每族 200–500 条即可，来源多样性优先于底物数量。工具强制三条：出版年份不等于已核实最早公开日期；不推断机理；imported 不等于已核对。家族标签只作为地图图层，不参与坐标计算。
