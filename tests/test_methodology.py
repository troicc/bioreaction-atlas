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
    records, _ = build_records([row(), row(source_doi='10.0000/b', family='nhc_umpolung')])
    corpus = build_corpus(records, 'export.csv', 'deadbeef', 2)
    assert corpus['family_counts'] == {'metal_carbene': 1, 'nhc_umpolung': 1}
    assert corpus['sources'][0] == {'name': 'export.csv', 'sha256': 'deadbeef', 'rows': 2}
    assert 'not_a_reviewed_benchmark' in corpus['purpose']
