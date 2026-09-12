"""English display labels; the original v0.1 schema remains import-compatible."""
from copy import deepcopy
from .schema import TABLES, VERSION

EN = {
 'context_id': ('Context ID', 'Unique ID, e.g. WK_MU2025_C01. Create a new context when the reaction mode, metal or conditions change.'),
 'discovery_id': ('Discovery event ID', 'Group one reported reaction capability. Substrates and variants are not separate discoveries; cross-paper events will be reconciled later.'),
 'source': ('DOI or public URL', 'Original article DOI or permanent preprint URL. Prefer the primary experimental source.'),
 'source_locator': ('Source location', 'Main text or SI page, figure/table and entry. Locate the specific conditions or measurement, not only the paper.'),
 'reaction_name': ('Reaction name', 'Use the reaction name reported by the authors.'),
 'catalysis_mode': ('Catalysis type', 'Classify the catalyst actually used in this experiment.'),
 'scaffold': ('Protein scaffold', 'Required for enzymatic records; enter Not reported if unknown. Put the variant in Measurements.'),
 'metal_cofactor': ('Actual metal and cofactor', 'Record the experimental metal/cofactor or added salt. Do not infer the active oxidation state from the salt alone.'),
 'conditions_raw': ('Conditions as reported', 'Keep the reported buffer, pH, temperature, time, concentrations, additives and amounts, with units. Details can be separated later.'),
 'record_status': ('Review status', 'Use Needs review during collection. Reviewed requires checking structures, conditions and sources. Example is always excluded from retrieval.'),
 'paper_title': ('Paper title', 'Title as published.'),
 'lab': ('Research group', 'PI name and/or institution for coverage tracking.'),
 'first_public_date': ('Earliest public date', 'YYYY-MM-DD after checking preprints and journal versions. If only a year is known, leave blank and put the year in Notes.'),
 'date_evidence': ('Date evidence URL', 'Source supporting the earliest verified public date. A journal date alone does not establish that no earlier preprint exists.'),
 'bond_classes': ('Bond formation classes', 'Separate multiple labels with semicolons: C-C; C-N; C-O; C-S; C-Si; other. These labels do not establish mechanism.'),
 'native_metal_cofactor': ('Native metal and cofactor', 'Record native Fe separately from experimental Cu, for example. Leave unknown values blank.'),
 'metal_installation': ('Metal installation method', 'Describe salt addition, metal substitution, complex incorporation or reconstitution as reported.'),
 'enzyme_form': ('Enzyme preparation', 'Purified enzyme, lysate, whole cells, etc.'),
 'buffer_ph': ('Buffer and pH', 'Buffer identity, concentration and pH. Leave unreported information blank.'),
 'solvent': ('Solvent and composition', 'Water/cosolvent composition with units, e.g. volume fraction.'),
 'temperature_c': ('Temperature (C)', 'Single numerical value in degrees Celsius. Preserve room temperature or a range in the original conditions; do not guess.'),
 'time_h': ('Duration (h)', 'Numerical hours. Keep the original time and unit in Conditions as reported.'),
 'partners_light': ('Additives and light/redox setup', 'Ligands, electron donors, oxidants/reductants, wavelength/power, atmosphere and quantities.'),
 'loading': ('Substrate and catalyst loading', 'Substrate concentration, enzyme/metal loading and equivalents, with units.'),
 'mechanism': ('Activation or intermediate', 'Optional. If populated, provide evidence type and a specific source location.'),
 'mechanism_evidence': ('Mechanistic evidence type', 'Keep experimental support, the authors proposal and a project hypothesis distinct.'),
 'mechanism_locator': ('Mechanistic evidence location', 'Page, figure, table or link supporting the mechanism; explain the reasoning for a project hypothesis.'),
 'notes': ('Notes', 'Uncertainties, alternative names, provenance, scope or additional details.'),
 'measurement_id': ('Measurement ID', 'Unique per row, e.g. WK_MU2025_A01_YIELD.'),
 'assay_id': ('Assay ID', 'Share across metrics from the same experiment. Change for a different substrate, variant or independent replicate.'),
 'compound_ids': ('Reactant and product labels', 'Paper labels, e.g. 1a + 2b -> 3ab. In an undetected experiment, identify the tested target without claiming it formed.'),
 'stage': ('Experimental stage', 'Distinguish initial activity, variants during screening, evolved outcomes, substrate scope and controls.'),
 'outcome': ('Product detection status', 'Not detected applies only to the measured product in that experiment. An unreported experiment is not a negative result.'),
 'metric': ('Metric', 'One metric per row. Yield and ee use separate rows with the same Assay ID.'),
 'value': ('Numeric value', 'For 85 percent enter the plain number 85, not Excel 85%. For <1 enter 1 and qualifier <. Unknown stays blank; zero must be reported.'),
 'qualifier': ('Qualifier', 'Required when Numeric value is populated. Use ~ for an approximate value. Do not treat a bound as an exact measurement.'),
 'unit': ('Unit', 'Required for a numeric value. Use % for yield/conversion/ee and turnovers for TTN.'),
 'raw_result': ('Result as reported', 'Preserve the original expression, e.g. >99% ee, 95:5 dr or n.d. Required when Numeric value is blank.'),
 'variant': ('Enzyme variant', 'Reported variant name/mutations. Use Not reported if unspecified; may be blank for nonenzymatic controls.'),
 'reaction_smiles': ('Reaction SMILES', 'reactants>agents>products or reactants>>products. Preserve stereochemistry. Atom mapping is not required; structures can be added later.'),
 'structure_status': ('Structure status', 'Only Reviewed structures enter default retrieval. Never invent an unreported product.'),
 'product_role': ('Product role', 'Use Tested target when the structure describes an intended product in an undetected reaction or control.'),
 'measurement_method': ('Measurement method', 'Isolated yield, GC, HPLC, NMR, chiral method, standards, etc.'),
 'replicates': ('Replicate count', 'Positive integer only when reported. Individual replicate values may use separate Assay IDs.'),
 'uncertainty_raw': ('Uncertainty as reported', 'For example mean +/- SD, n=3. Keep SD and SEM distinct.'),
 'sequence_accession': ('Sequence or database accession', 'UniProt, PDB, GenBank, etc. Can be added later.'),
}

CHOICES = {
 '酶催化': 'Enzymatic', '非酶催化': 'Nonenzymatic', '无催化剂对照': 'No-catalyst control',
 '待核对': 'Needs review', '已核对': 'Reviewed', '示例': 'Example',
 '实验支持': 'Experimental support', '作者提出': 'Author proposal', '项目假设': 'Project hypothesis',
 '未说明': 'Unspecified', '初始活性': 'Initial activity', '筛选中间体': 'Screening intermediate',
 '进化后结果': 'Evolved outcome', '底物拓展': 'Substrate scope', '对照': 'Control',
 '检出': 'Detected', '未检出': 'Not detected', '未报告': 'Not reported', '不明确': 'Unclear',
 '待补结构': 'Structure pending', '观察产物': 'Observed product', '测试目标': 'Tested target',
}
EN_SHEETS = {'contexts': 'Reaction contexts', 'experiments': 'Measurements'}


def localized_metadata(language='zh'):
    if language not in ('zh', 'en'):
        raise ValueError('language must be zh or en')
    tables = deepcopy(TABLES)
    if language == 'en':
        for name, spec in tables.items():
            spec['sheet'] = EN_SHEETS[name]
            for field in spec['fields']:
                field['label'], field['description'] = EN[field['key']]
                if field['choices']:
                    field['choices'] = [CHOICES.get(v, v) for v in field['choices']]
    return {'schema_version': VERSION, 'language': language, 'tables': tables}


def canonical_choice(field, value):
    if field['choices'] and isinstance(value, str):
        inverse = {CHOICES.get(v, v).casefold(): v for v in field['choices']}
        return inverse.get(value.casefold(), value)
    return value
