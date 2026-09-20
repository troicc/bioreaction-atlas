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
    assert family_screen(SI_H_INSERTION, 'metal_carbene') == (True, 'reactant carries a substituted diazo group')


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
    assert records[0]['context']['family_screen'] == 'reactant carries a substituted diazo group'


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
    assert verdict is True and reason == 'reactant carries a substituted diazo group'


def test_a_sulfonyl_azide_is_not_mistaken_for_a_diazo_group():
    # TsN3 is N=[N+]=[N-]; the diazo screen requires carbon at the terminus.
    from bioreaction_atlas.activation import family_screen
    azide_only = 'Cc1ccc(S(=O)(=O)N=[N+]=[N-])cc1.CCO>>CCOC(C)=O'
    assert family_screen(azide_only, 'metal_carbene', 'triethylamine')[0] is False


def test_retracted_and_review_citations_are_not_primary_evidence():
    rows = [row(document_type='Retracted Article'),
            row(source_doi='10.0000/b', document_type='Review'),
            row(source_doi='10.0000/c', document_type='Conference Paper')]
    records, skipped = build_records(rows)
    assert not records and len(skipped) == 3
    assert all(s['reason'].startswith('document type not primary evidence') for s in skipped)


def test_articles_and_patents_are_kept_with_their_type_recorded():
    rows = [row(document_type='Article'), row(source_doi='10.0000/b', document_type='Patent')]
    records, skipped = build_records(rows)
    assert not skipped
    assert [r['document_type'] for r in records] == ['Article', 'Patent']


def test_document_type_rejection_can_be_turned_off():
    rows = [row(document_type='Review')]
    assert len(build_records(rows, reject_document_types=set())[0]) == 1


def test_diazomethane_methylation_is_not_carbene_transfer():
    """The only "diazo" chemistry a med-chem patent corpus holds is ester methylation."""
    from bioreaction_atlas.activation import family_screen
    for esterification in (
            'C#CC(C)(C)C(=O)O.C=[N+]=[N-]>>C#CC(C)(C)C(=O)OC',
            'C[Si](C)(C)C=[N+]=[N-].O=C(O)c1ccccc1>>COC(=O)c1ccccc1'):
        assert family_screen(esterification, 'metal_carbene')[0] is False


def test_substituted_diazo_reagents_are_still_admitted():
    from bioreaction_atlas.activation import family_screen
    for carbene in (
            'CCOC(=O)C=[N+]=[N-].c1ccc2[nH]ccc2c1>>CCOC(=O)Cc1c[nH]c2ccccc12',
            'COC(=O)C(=[N+]=[N-])c1ccccc1.Nc1ccccc1>>COC(=O)C(Nc1ccccc1)c1ccccc1',
            'C[C@H]1Cc2ccccc2N1.[N-]=[N+]=C1CCOC1=O>>C[C@H]1Cc2ccccc2N1[C@H]1CCOC1=O'):
        assert family_screen(carbene, 'metal_carbene')[0] is True


DEHYDROALANINE = ('C=C(NC(C)=O)C(=O)OC.CC1C(=O)Nc2ccccc21'
                  '>>CC1(CC(NC(C)=O)C(=O)OC)C(=O)Nc2ccccc21')
TRPB = ('CC1C(=O)Nc2ccccc21.N[C@@H](CO)C(=O)O'
        '>>CC1(C[C@H](N)C(=O)O)C(=O)Nc2ccccc21')


def test_dehydroamino_acid_acceptors_define_the_plp_analogue_family():
    from bioreaction_atlas.activation import family_screen
    verdict, reason = family_screen(DEHYDROALANINE, 'aminoacrylate_addition')
    assert verdict is True and 'dehydroamino acid' in reason


def test_beta_substituted_dehydroamino_acids_are_the_same_activation_mode():
    from bioreaction_atlas.activation import family_screen
    for acceptor in (
            'CC=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>CC(SCc1ccccc1)C(NC(C)=O)C(=O)OC',
            'c1ccccc1C=C(NC(C)=O)C(=O)O.OO>>c1ccccc1C(O)C(NC(C)=O)C(=O)O'):
        assert family_screen(acceptor, 'aminoacrylate_addition')[0] is True


def test_the_nitrogen_and_carbonyl_must_share_an_alkene_carbon():
    """A beta-enaminone has them on different carbons and is not this family."""
    from bioreaction_atlas.activation import family_screen
    enaminone = 'CC(=O)C=C(C)N.CI>>CC(=O)C=C(C)NC'
    acrylamide = 'C=CC(N)=O.SCc1ccccc1>>NC(=O)CCSCc1ccccc1'
    assert family_screen(enaminone, 'aminoacrylate_addition')[0] is False
    assert family_screen(acrylamide, 'aminoacrylate_addition')[0] is False


def test_a_plain_michael_acceptor_is_not_a_dehydroalanine():
    from bioreaction_atlas.activation import family_screen
    plain = 'C=CC(=O)OC.CC(=O)CC(C)=O>>COC(=O)CCC(C(C)=O)C(C)=O'
    assert family_screen(plain, 'aminoacrylate_addition')[0] is False


def test_the_enzyme_route_does_not_match_its_own_abiotic_family():
    """TrpB consumes serine; the aminoacrylate is a transient intermediate.

    The enzyme and abiotic routes share an intermediate but not a precursor, so
    enzyme seeds for this family must be selected by cofactor, not by the abiotic
    structural screen. Carbene chemistry hides this because both sides carry a diazo.
    """
    from bioreaction_atlas.activation import family_screen
    assert family_screen(TRPB, 'aminoacrylate_addition')[0] is False


def test_aromatic_heterocycles_are_not_dehydroamino_acids():
    """Indole-2-carboxylate embeds C=C(N)C(=O) inside an aromatic ring.

    A Reaxys substructure query with "additional ring closures" enabled returns
    hundreds of thousands of such reactions - nitro reductions and the like on
    indole and pyrrole esters. The screen must reject them: the SMARTS requires
    aliphatic alkene carbons, so an aromatic ring never matches.
    """
    from bioreaction_atlas.activation import family_screen
    for aromatic in (
            'CCOC(=O)c1cc2cc([N+](=O)[O-])ccc2[nH]1>>CCOC(=O)c1cc2cc(N)ccc2[nH]1',
            'COC(=O)c1cc[nH]c1>>COC(=O)c1cc[nH]c1C',
            'COC(=O)c1ccc2ccccc2[nH]1>>COC(=O)c1ccc2ccccc2n1C'):
        assert family_screen(aromatic, 'aminoacrylate_addition')[0] is False


def test_asymmetric_hydrogenation_is_not_beta_substitution():
    """The most studied reaction of dehydroamino acids adds only hydrogen.

    It forms no bond to a nucleophile, so it is not what a PLP beta-substituting
    enzyme does, and it would otherwise dominate the pool.
    """
    from bioreaction_atlas.activation import family_screen
    for reduction in (
            'C(=C/c1ccccc1)(\\NC(=O)c1ccccc1)C(=O)OC.[HH]'
            '>>COC(=O)C(Cc1ccccc1)NC(=O)c1ccccc1',
            # Transfer hydrogenation records often omit the hydrogen source entirely.
            'C(=C/c1ccccc1)(\\NC(=O)c1ccccc1)C(=O)OC'
            '>>COC(=O)C(Cc1ccccc1)NC(=O)c1ccccc1'):
        verdict, reason = family_screen(reduction, 'aminoacrylate_addition')
        assert verdict is False and 'no heavy atoms added' in reason


def test_additions_that_gain_heavy_atoms_are_kept():
    from bioreaction_atlas.activation import family_screen
    for addition in (
            'C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1',
            'C=C(NC(C)=O)C(=O)OC.CC1C(=O)Nc2ccccc21>>CC1(CC(NC(C)=O)C(=O)OC)C(=O)Nc2ccccc21',
            'C=C(NC(C)=O)C(=O)OC.O>>COC(=O)C(NC(C)=O)CO'):
        assert family_screen(addition, 'aminoacrylate_addition')[0] is True


def test_the_heavy_atom_veto_applies_only_where_configured():
    """Carbene transfer has no such rule; its families must be unaffected."""
    from bioreaction_atlas.activation import SCREENS, family_screen
    assert 'require_heavy_atom_gain' not in SCREENS['metal_carbene']
    carbene = 'CCOC(=O)C=[N+]=[N-].c1ccc2[nH]ccc2c1>>CCOC(=O)Cc1c[nH]c2ccccc12'
    assert family_screen(carbene, 'metal_carbene')[0] is True


def test_family_membership_is_labelled_even_when_nothing_is_rejected():
    """An evaluation pool needs the mixture, with every row labelled.

    A pool filtered to 100% in-family makes a later retrieval measurement
    degenerate: there is nothing for ranking to discriminate.
    """
    hydrogenation = row(
        reaction_smiles='C=C(NC(C)=O)C(=O)OC>>COC(=O)C(C)NC(C)=O',
        family='aminoacrylate_addition')
    addition = row(
        reaction_smiles='C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1',
        family='aminoacrylate_addition', source_doi='10.0000/b')

    kept, skipped = build_records([hydrogenation, addition], screen=False)
    assert len(kept) == 2 and not skipped
    assert [r['context']['in_family'] for r in kept] == [False, True]
    assert all(r['context']['family_screen'] for r in kept)

    screened, rejected = build_records([hydrogenation, addition], screen=True)
    assert [r['context']['in_family'] for r in screened] == [True]
    assert len(rejected) == 1


def test_an_unscreened_family_reports_its_label_as_unknown():
    records, _ = build_records([row(family='background_patent')], screen=False)
    context = records[0]['context']
    assert context['in_family'] is None
    assert context['family_screen'].startswith('unscreened:')


def test_a_nitroalkene_is_not_a_dehydroamino_acid():
    """Nitro nitrogen also has three connections, but a nitroalkene is a different
    and far stronger acceptor, and its nitrogen is not an amino group."""
    from bioreaction_atlas.activation import family_screen
    nitroacrylate = ('CCOC(=O)C(=Cc1ccccc1)[N+](=O)[O-].Sc1ccccc1'
                     '>>CCOC(=O)C(C(Sc1ccccc1)c1ccccc1)[N+](=O)[O-]')
    assert family_screen(nitroacrylate, 'aminoacrylate_addition')[0] is False


def test_amide_and_carbamate_protected_nitrogens_still_qualify():
    from bioreaction_atlas.activation import family_screen
    for protected in (
            'C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1',
            'C=C(NC(=O)OCc1ccccc1)C(=O)OC.CC1C(=O)Nc2ccccc21'
            '>>CC1(CC(NC(=O)OCc1ccccc1)C(=O)OC)C(=O)Nc2ccccc21'):
        assert family_screen(protected, 'aminoacrylate_addition')[0] is True


def test_acceptor_consumption_is_a_property_not_a_membership_rule():
    """Which of these counts as the family is a chemistry judgement, so it is
    recorded and reported rather than decided by the screen."""
    from bioreaction_atlas.activation import acceptor_consumed, family_screen
    heck = ('C=C(NC(C)=O)C(=O)OC.Ic1ccccc1'
            '>>COC(=O)/C(=C/c1ccccc1)NC(C)=O')
    addition = 'C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1'
    # Both are in the family; they differ in whether the acceptor survives.
    assert family_screen(heck, 'aminoacrylate_addition')[0] is True
    assert family_screen(addition, 'aminoacrylate_addition')[0] is True
    assert acceptor_consumed(heck, 'aminoacrylate_addition') is False
    assert acceptor_consumed(addition, 'aminoacrylate_addition') is True


def test_carbene_transfer_consumes_its_diazo():
    from bioreaction_atlas.activation import acceptor_consumed
    transfer = 'CCOC(=O)C=[N+]=[N-].c1ccc2[nH]ccc2c1>>CCOC(=O)Cc1c[nH]c2ccccc12'
    # A surviving diazo means the reaction happened elsewhere in the molecule.
    elsewhere = 'CCOC(=O)C=[N+]=[N-].CO>>CCOC(=O)C=[N+]=[N-].CI'
    assert acceptor_consumed(transfer, 'metal_carbene') is True
    assert acceptor_consumed(elsewhere, 'metal_carbene') is False


def test_families_without_a_diagnostic_group_report_unknown():
    from bioreaction_atlas.activation import acceptor_consumed
    assert acceptor_consumed('CC>>CC', 'enamine_iminium') is None
    assert acceptor_consumed('CC>>CC', 'background_patent') is None


def test_the_property_is_recorded_on_every_imported_record():
    rows = [row(reaction_smiles='C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1',
                family='aminoacrylate_addition')]
    records, _ = build_records(rows)
    assert records[0]['context']['acceptor_consumed'] is True


IN_SITU = 'N[C@@H](CS)C(=O)O.SCc1ccccc1>>NC(CSCc1ccccc1)C(=O)O'


def test_an_in_situ_route_is_rejected_without_normalisation():
    """The abiotic route can form the acceptor in situ from the enzyme's own precursor.

    Such a reaction carries no acceptor in its reactants, so the family screen rejects
    it and the pool silently misses that whole route.
    """
    records, skipped = build_records([row(reaction_smiles=IN_SITU, family='aminoacrylate_addition')])
    assert not records and skipped[0]['reason'].startswith('off-family')


def test_normalisation_admits_it_and_preserves_what_was_reported():
    records, skipped = build_records(
        [row(reaction_smiles=IN_SITU, family='aminoacrylate_addition')], normalize=True)
    assert len(records) == 1 and not skipped
    record = records[0]
    assert record['reaction_smiles'].startswith('C=C(N)C(=O)O')
    assert record['reaction_smiles_as_reported'] == IN_SITU
    assert 'beta-elimination' in record['context']['intermediate_rule']


def test_a_reaction_already_at_the_acceptor_level_is_not_rewritten():
    already = 'C=C(NC(C)=O)C(=O)OC.SCc1ccccc1>>COC(=O)C(NC(C)=O)CSCc1ccccc1'
    records, _ = build_records(
        [row(reaction_smiles=already, family='aminoacrylate_addition')], normalize=True)
    assert records[0]['reaction_smiles'] == already
    assert records[0]['reaction_smiles_as_reported'] is None
    assert records[0]['context']['intermediate_rule'] is None
