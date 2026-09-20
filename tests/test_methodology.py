import pytest

from bioreaction_atlas.activation import (
    FAMILIES, TRANSITION_METALS, catalytic_context, parse_agents,
)
from bioreaction_atlas.methodology import build_corpus, build_records

CYCLOPROPANATION = 'CCOC(=O)C=[N+]=[N-].C=Cc1ccccc1>>CCOC(=O)C1CC1c1ccccc1'
WITH_AGENTS = 'CS(=O)(=O)N1CCN(Cc2ccccc2)CC1>[OH-].[Pd+2].CCO>CS(=O)(=O)N1CCNCC1'


def row(**overrides):
    return {'reaction_smiles': CYCLOPROPANATION, 'family': 'metal_carbene',
            'source_doi': '10.0000/a'} | overrides


def test_agents_segment_yields_metals_and_solvents():
    parsed = parse_agents(WITH_AGENTS)
    assert parsed['has_agents'] and parsed['metals'] == ['Pd']
    assert parsed['solvents'] == ['ethanol'] and '[OH-]' in parsed['other_agents']


def test_missing_agents_segment_is_reported_not_guessed():
    parsed = parse_agents(CYCLOPROPANATION)
    assert parsed == {'metals': [], 'solvents': [], 'other_agents': [], 'unparsed': [], 'has_agents': False}


def test_unparseable_agent_fragments_are_kept():
    parsed = parse_agents('CCO>%%%bogus%%%>CCO')
    assert parsed['unparsed'] == ['%%%bogus%%%']


def test_context_separates_transition_metals_from_salts():
    context = catalytic_context('CCO>[Pd+2].[Na+].CO>CCO', 'metal_carbene')
    assert context['metal_cofactor'] == 'Pd' and context['other_metals'] == 'Na'
    assert 'Pd' in TRANSITION_METALS


def test_context_never_claims_a_mechanism():
    context = catalytic_context(WITH_AGENTS, 'metal_carbene')
    assert context['mechanism'] is None
    assert context['mechanism_evidence'] == '未说明'
    assert context['context_source'] == 'parsed_from_agents_segment_not_read_from_primary_source'


def test_unknown_family_is_rejected():
    with pytest.raises(ValueError, match='Unknown activation family'):
        catalytic_context(CYCLOPROPANATION, 'not_a_family')


def test_import_builds_an_encodable_record():
    records, skipped = build_records([row(catalyst='Rh2(OAc)4', solvent='dichloromethane')], prefix='CARB')
    assert not skipped and len(records) == 1
    record = records[0]
    assert record['record_id'].startswith('CARB_')
    assert record['domain'] == 'nonenzymatic' and record['review_status'] == 'imported'
    assert record['activation_family'] == 'metal_carbene'
    assert record['label'] == FAMILIES['metal_carbene']


def test_explicit_columns_outrank_the_lexical_guess():
    records, _ = build_records([row(reaction_smiles=WITH_AGENTS, solvent='toluene', catalyst='Rh2(OAc)4')])
    context = records[0]['context']
    assert context['solvent'] == 'toluene'  # exported column wins over the parsed ethanol
    assert context['catalyst'] == 'Rh2(OAc)4'
    assert context['context_source'] == 'explicit_export_columns_plus_agents_segment'


def test_publication_year_is_not_promoted_to_a_verified_date():
    records, _ = build_records([row(source_year='2015')])
    assert records[0]['source_year'] == '2015'
    assert records[0]['first_public_date'] is None
    assert records[0]['date_evidence'] is None


def test_rows_are_skipped_with_a_stated_reason():
    rows = [row(source_doi=''), row(family='nope'), row(reaction_smiles='not a reaction')]
    records, skipped = build_records(rows)
    assert not records and len(skipped) == 3
    reasons = ' '.join(s['reason'] for s in skipped)
    assert 'missing source_doi' in reasons and 'unknown family nope' in reasons and 'unparseable' in reasons


def test_duplicates_within_a_source_are_flagged_not_merged():
    records, skipped = build_records([row(), row()])
    assert len(records) == 1 and 'duplicate of row 2' in skipped[0]['reason']


def test_same_reaction_from_a_different_paper_stays_separate():
    records, skipped = build_records([row(), row(source_doi='10.0000/b')])
    assert len(records) == 2 and not skipped


def test_corpus_counts_families_and_pins_the_source():
    records, _ = build_records([row(), row(source_doi='10.0000/b', family='nhc_umpolung',
                                     catalyst='triazolium salt')])
    corpus = build_corpus(records, 'export.csv', 'deadbeef', 2)
    assert corpus['family_counts'] == {'metal_carbene': 1, 'nhc_umpolung': 1}
    assert corpus['sources'][0] == {'name': 'export.csv', 'sha256': 'deadbeef', 'rows': 2}
    assert 'not_a_reviewed_benchmark' in corpus['purpose']


AMIDE = 'CC(=O)O.NCc1ccccc1>>CC(=O)NCc1ccccc1'
SI_H_INSERTION = 'CCOC(=O)C=[N+]=[N-].[SiH](CC)(CC)CC>>CCOC(=O)C[Si](CC)(CC)CC'


def test_diagnostic_reactant_group_admits_a_reaction():
    from bioreaction_atlas.activation import family_screen
    assert family_screen(SI_H_INSERTION, 'metal_carbene') == (True, 'reactant carries a diazo group')


def test_substrate_prep_steps_are_rejected():
    from bioreaction_atlas.activation import family_screen
    verdict, reason = family_screen(AMIDE, 'metal_carbene', 'EDC, HOBt')
    assert verdict is False and 'no diagnostic' in reason


def test_palladium_does_not_admit_a_reaction_to_the_carbene_family():
    # Suzuki/Sonogashira steps are the commonest contaminant in a methodology paper.
    from bioreaction_atlas.activation import family_screen
    assert family_screen(AMIDE, 'metal_carbene', 'Pd(PPh3)4')[0] is False


def test_catalyst_metals_are_recognized_as_symbol_and_as_name():
    from bioreaction_atlas.activation import family_screen
    assert family_screen(AMIDE, 'metal_carbene', 'Rh2(OAc)4') == (True, 'catalyst metal Rh')
    assert family_screen(AMIDE, 'metal_carbene', 'rhodium(II) acetate') == (True, 'catalyst metal Rh')


def test_element_symbol_does_not_fire_inside_an_unrelated_word():
    from bioreaction_atlas.activation import _mentions_metal
    assert _mentions_metal('CoCl2', 'Co') and _mentions_metal('Co2(CO)8', 'Co')
    assert not _mentions_metal('Corey-Bakshi-Shibata reagent', 'Co')


def test_organocatalyst_families_screen_on_catalyst_text():
    from bioreaction_atlas.activation import family_screen
    assert family_screen(AMIDE, 'nhc_umpolung', 'thiazolium salt')[0] is True
    assert family_screen(AMIDE, 'enamine_iminium', 'L-proline')[0] is True
    assert family_screen(AMIDE, 'enamine_iminium', 'EDC, HOBt')[0] is False


def test_families_without_a_screen_are_reported_as_unscreened():
    from bioreaction_atlas.activation import family_screen
    verdict, reason = family_screen(AMIDE, 'background_patent')
    assert verdict is None and 'no screen defined' in reason


def test_importer_drops_off_family_rows_with_a_stated_reason():
    rows = [row(reaction_smiles=SI_H_INSERTION, catalyst='Rh2(OAc)4'),
            row(reaction_smiles=AMIDE, source_doi='10.0000/b', catalyst='EDC, HOBt')]
    records, skipped = build_records(rows)
    assert len(records) == 1 and len(skipped) == 1
    assert skipped[0]['reason'].startswith('off-family')
    assert records[0]['context']['family_screen'] == 'reactant carries a diazo group'


def test_screening_can_be_disabled():
    rows = [row(reaction_smiles=AMIDE, catalyst='EDC, HOBt')]
    assert len(build_records(rows, screen=False)[0]) == 1
    assert len(build_records(rows, screen=True)[0]) == 0


# A real Reaxys hit for a diazo substructure query: the diazo is the PRODUCT.
# This is diazo-transfer, i.e. making the carbene precursor, not using it.
DIAZO_TRANSFER = ('COC(=O)Cc1ccc(Cl)cc1.Cc1ccc(S(=O)(=O)N=[N+]=[N-])cc1'
                  '>>COC(=O)C(=[N+]=[N-])c1ccc(Cl)cc1')
CARBENE_USE = ('COC(=O)C(=[N+]=[N-])c1ccc(Cl)cc1.C=Cc1ccccc1'
               '>>COC(=O)C1(c2ccc(Cl)cc2)CC1c1ccccc1')


def test_diazo_transfer_is_rejected_because_the_diazo_is_a_product():
    from bioreaction_atlas.activation import family_screen
    for base in ('1,8-diazabicyclo[5.4.0]undec-7-ene', 'triethylamine', 'potassium carbonate'):
        assert family_screen(DIAZO_TRANSFER, 'metal_carbene', base)[0] is False


def test_carbene_use_is_admitted_when_the_diazo_is_a_reactant():
    from bioreaction_atlas.activation import family_screen
    verdict, reason = family_screen(CARBENE_USE, 'metal_carbene', 'dirhodium tetraacetate')
    assert verdict is True and reason == 'reactant carries a diazo group'


def test_a_sulfonyl_azide_is_not_mistaken_for_a_diazo_group():
    # TsN3 is N=[N+]=[N-]; the diazo screen requires carbon at the terminus.
    from bioreaction_atlas.activation import family_screen
    azide_only = 'Cc1ccc(S(=O)(=O)N=[N+]=[N-])cc1.CCO>>CCOC(C)=O'
    assert family_screen(azide_only, 'metal_carbene', 'triethylamine')[0] is False
