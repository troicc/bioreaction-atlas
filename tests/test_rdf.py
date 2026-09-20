from rdkit.Chem import rdChemReactions

from bioreaction_atlas.rdf import field_summary, guess_mapping, read_rdf

CYCLOPROPANATION = 'CCOC(=O)C=[N+]=[N-].C=Cc1ccccc1>>CCOC(=O)C1CC1c1ccccc1'


def rxn_block(smiles=CYCLOPROPANATION):
    reaction = rdChemReactions.ReactionFromSmarts(smiles, useSmiles=True)
    return rdChemReactions.ReactionToRxnBlock(reaction)


def record(fields, block=None):
    # ReactionToRxnBlock already emits the $RXN header; do not double it.
    text = '$RFMT $RIREG 41267686\n' + (block if block is not None else rxn_block())
    for name, value in fields.items():
        text += f'$DTYPE {name}\n$DATUM {value}\n'
    return text


def rdf(*records):
    return '$RDFILE 1\n$DATM 2026-09-20\n' + ''.join(records)


def test_reads_reactions_and_their_data_fields():
    rows, failures = read_rdf(rdf(record({'RXD.CAT': 'Rh2(OAc)4', 'CIT.DOI': '10.1021/ja0504441'})))
    assert not failures and len(rows) == 1
    assert rows[0]['RXD.CAT'] == 'Rh2(OAc)4'
    assert rows[0]['CIT.DOI'] == '10.1021/ja0504441'


def test_aromaticity_is_reperceived_not_left_as_kekule_colons():
    rows, _ = read_rdf(rdf(record({})))
    smiles = rows[0]['reaction_smiles']
    assert 'c1ccccc1' in smiles and ':C:' not in smiles


def test_atom_maps_are_stripped():
    mapped = '[CH2:1]=[CH:2]c1ccccc1>>[CH3:1][CH2:2]c1ccccc1'
    rows, failures = read_rdf(rdf(record({}, block=rxn_block(mapped))))
    assert not failures
    assert ':' not in rows[0]['reaction_smiles']


def test_every_record_in_a_multi_record_file_is_read():
    rows, _ = read_rdf(rdf(record({'RX.ID': '1'}), record({'RX.ID': '2'}), record({'RX.ID': '3'})))
    assert [r['RX.ID'] for r in rows] == ['1', '2', '3']


def test_a_broken_record_is_reported_and_the_rest_survive():
    broken = '$RFMT $RIREG 9\n$RXN\n\n\n\nnot a molfile at all\n$DTYPE RX.ID\n$DATUM 9\n'
    rows, failures = read_rdf(rdf(record({'RX.ID': '1'}), broken, record({'RX.ID': '2'})))
    assert len(rows) == 2 and len(failures) == 1
    assert failures[0]['reason']


def test_multiline_datum_values_are_kept():
    text = rdf('$RFMT $RIREG 1\n' + rxn_block() + '$DTYPE RXD.COND\n$DATUM stirred 2 h\nthen warmed\n')
    rows, _ = read_rdf(text)
    assert rows[0]['RXD.COND'] == 'stirred 2 h\nthen warmed'


def test_field_summary_counts_only_populated_fields():
    rows, _ = read_rdf(rdf(record({'RXD.CAT': 'Rh2(OAc)4'}), record({'RXD.CAT': ''})))
    summary = field_summary(rows)
    assert summary['RXD.CAT'][0] == 1
    assert 'reaction_smiles' not in summary


def test_vendor_codes_match_exactly_so_time_is_not_read_as_temperature():
    # "rxd.t" is a prefix of "rxd.tim"; a substring rule would mis-assign it.
    rows, _ = read_rdf(rdf(record({'RXD.TIM': '2'})))
    mapping = guess_mapping(rows)
    assert mapping.get('time_h') == 'RXD.TIM'
    assert 'temperature_c' not in mapping


def test_both_time_and_temperature_resolve_when_both_exist():
    rows, _ = read_rdf(rdf(record({'RXD.TIM': '2', 'RXD.T': '25'})))
    mapping = guess_mapping(rows)
    assert mapping['time_h'] == 'RXD.TIM' and mapping['temperature_c'] == 'RXD.T'


def test_mapping_covers_the_columns_the_importer_requires():
    rows, _ = read_rdf(rdf(record({
        'RXD.CAT': 'Rh2(OAc)4', 'RXD.SOL': 'dichloromethane', 'RXD.YPRO': '84',
        'CIT.DOI': '10.1021/ja0504441', 'Publication Year': '2004', 'RX.ID': '1234567'})))
    mapping = guess_mapping(rows)
    assert mapping['source_doi'] == 'CIT.DOI'
    assert mapping['catalyst'] == 'RXD.CAT'
    assert mapping['solvent'] == 'RXD.SOL'
    assert mapping['yield_percent'] == 'RXD.YPRO'
    assert mapping['source_year'] == 'Publication Year'
    # RIREG comes off the $RFMT line and is the registry number the PDF calls Rx-ID.
    assert mapping['external_id'] == 'RIREG'


def test_no_field_is_mapped_to_two_columns():
    rows, _ = read_rdf(rdf(record({'RXD.CAT': 'x', 'RXD.SOL': 'y'})))
    mapping = guess_mapping(rows)
    assert len(set(mapping.values())) == len(mapping)


def test_the_rfmt_registry_number_is_captured_as_the_join_key():
    rows, _ = read_rdf(rdf(record({'RXD.CAT': 'Rh2(OAc)4'})))
    assert rows[0]['RIREG'] == '41267686'


def test_variations_become_separate_records():
    from bioreaction_atlas.rdf import explode_variations
    rows = [{'reaction_smiles': 'CC>>CC', 'ROOT:RX_ID': '41267686', 'RIREG': '41267686',
             'ROOT:RXD(1):RGT': 'hemin', 'ROOT:RXD(1):citation': '67381162; Review; A, B; J; vol. 1; (2015); p. 1 - 2',
             'ROOT:RXD(2):CAT': 'dirhodium tetraacetate',
             'ROOT:RXD(2):citation': '140713506; Article; C, D; J2; vol. 2; (2019); p. 3 - 4'}]
    out = explode_variations(rows)
    assert len(out) == 2
    assert [r['variation'] for r in out] == [1, 2]
    # Shared reaction fields ride along with every variation.
    assert all(r['RX_ID'] == '41267686' for r in out)
    assert [r['document_type'] for r in out] == ['Review', 'Article']
    assert [r['citation_year'] for r in out] == ['2015', '2019']
    assert [r['citation_id'] for r in out] == ['67381162', '140713506']


def test_catalyst_fields_are_combined_because_reaxys_splits_them():
    from bioreaction_atlas.rdf import explode_variations
    rows = [{'reaction_smiles': 'CC>>CC',
             'ROOT:RXD(1):CAT': 'dirhodium tetraacetate', 'ROOT:RXD(1):RGT': 'hemin|β-cyclodextrin'}]
    assert explode_variations(rows)[0]['catalyst_all'] == 'dirhodium tetraacetate|hemin|β-cyclodextrin'


def test_a_reaction_without_variations_still_yields_one_row():
    from bioreaction_atlas.rdf import explode_variations
    out = explode_variations([{'reaction_smiles': 'CC>>CC', 'ROOT:RX_ID': '1'}])
    assert len(out) == 1 and out[0]['RX_ID'] == '1' and out[0]['variation'] == 1


def test_numeric_yield_is_mapped_not_the_product_name():
    from bioreaction_atlas.rdf import REAXYS_COLUMNS
    # YPRO is the product name; using it as a yield would be silently wrong.
    assert REAXYS_COLUMNS['yield_percent'] == 'NYD'
    assert 'YPRO' not in REAXYS_COLUMNS.values()
