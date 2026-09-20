import pytest

from bioreaction_atlas.transfer import medium, obstacles


def ctx(**kwargs):
    return {'catalyst': '', 'solvent': '', 'temperature_c': None} | kwargs


def test_aqueous_and_water_miscible_media_are_compatible():
    assert medium('water')[1] is None
    assert medium('N,N-dimethylformamide')[1] is None
    assert medium('methanol')[0] == 'water-miscible'


def test_a_water_immiscible_solvent_is_an_obstacle_to_state():
    kind, note = medium('dichloromethane')
    assert kind == 'water-immiscible' and 'biphasic' in note


def test_solvent_matching_ignores_punctuation():
    """Sources write "1,2-dichloro-ethane" and "dichloroethane" for one solvent."""
    assert medium('1,2-dichloro-ethane')[0] == 'water-immiscible'
    assert medium('N,N-dimethyl-formamide')[0] == 'water-miscible'


def test_temperature_outside_the_protein_range_is_flagged():
    cold = obstacles(ctx(temperature_c='-78'), 'heme')
    hot = obstacles(ctx(temperature_c='140'), 'heme')
    fine = obstacles(ctx(temperature_c='30'), 'heme')
    assert any('below the range' in o for o in cold['obstacles'])
    assert any('above the range' in o for o in hot['obstacles'])
    assert not fine['obstacles'] and any('within protein range' in c for c in fine['compatible'])


def test_a_metal_the_platform_carries_is_compatible():
    result = obstacles(ctx(catalyst='hemin', solvent='water', temperature_c='35'), 'heme')
    assert result['catalyst_metals'] == ['Fe']
    assert not result['obstacles']
    assert any('already carries' in c for c in result['compatible'])


def test_a_metal_the_platform_lacks_is_an_obstacle_not_a_verdict():
    result = obstacles(ctx(catalyst='Rh2(OAc)4'), 'heme')
    assert any('metal substitution is a separate published step' in o for o in result['obstacles'])


def test_metal_complexes_named_without_their_element_are_recognised():
    for name, symbol in (('hemin', 'Fe'), ('ferrocene', 'Fe'), ('Grubbs catalyst', 'Ru'),
                         ('Wilkinson catalyst', 'Rh')):
        assert symbol in obstacles(ctx(catalyst=name), 'PLP')['catalyst_metals']


def test_an_external_ligand_requirement_is_stated():
    spelled_out = 'bis(acetonitrile)(2,6-bis[1-(2,6-diisopropylphenyl)imidazolylidene])copper'
    result = obstacles(ctx(catalyst=spelled_out), 'heme')
    assert any('external ligand' in o for o in result['obstacles'])


def test_protein_destroying_reagents_are_flagged():
    for reagent in ('n-butyllithium', 'titanium tetrachloride', 'osmium tetroxide'):
        result = obstacles(ctx(catalyst=reagent), 'PLP')
        assert any('denature' in o for o in result['obstacles']), reagent


def test_unrecorded_conditions_are_not_cleared_conditions():
    """Counting missing data as zero obstacles would rank empty records first."""
    result = obstacles(ctx(), 'heme')
    assert result['obstacle_count'] == 0
    assert result['unknown_count'] == 3
    assert set(result['unknown']) == {'no solvent recorded', 'no temperature recorded',
                                      'no catalyst or reagent recorded'}


def test_a_metal_free_platform_treats_metal_free_chemistry_as_compatible():
    result = obstacles(ctx(catalyst='potassium carbonate', solvent='water', temperature_c='25'), 'PLP')
    assert not result['obstacles']
    assert any('metal-free' in c for c in result['compatible'])


def test_the_count_is_never_presented_as_a_probability():
    result = obstacles(ctx(catalyst='Rh2(OAc)4', solvent='dichloromethane', temperature_c='-78'), 'heme')
    assert result['obstacle_count'] == 3
    assert 'not a feasibility estimate' in result['interpretation']


def test_a_bare_element_names_a_metal_substituted_platform():
    """Cu means an apo scaffold already loaded with copper."""
    from bioreaction_atlas.transfer import platform_metals
    assert platform_metals('Cu') == {'Cu'}
    assert platform_metals('heme') == {'Fe'}
    assert platform_metals('PLP') == set()


def test_the_installed_metal_is_not_an_obstacle_to_its_own_platform():
    loaded = obstacles(ctx(catalyst='copper(I) iodide', solvent='water', temperature_c='25'), 'Cu')
    assert not loaded['obstacles']
    assert any('already carries' in c for c in loaded['compatible'])
    # The same reaction on a haem platform still needs the substitution stated.
    haem = obstacles(ctx(catalyst='copper(I) iodide', solvent='water', temperature_c='25'), 'heme')
    assert any('does not natively carry' in o for o in haem['obstacles'])


def test_a_defined_ligand_is_the_premise_of_metal_substitution_not_an_obstacle():
    """An apo scaffold is loaded precisely to supply that coordination environment.

    On a haem platform the porphyrin is already the ligand, so the same requirement is
    a genuine conflict.
    """
    catalyst = 'copper(I) trifluoromethanesulfonate|bisoxazoline'
    on_cu = obstacles(ctx(catalyst=catalyst, solvent='water', temperature_c='25'), 'Cu')
    assert on_cu['obstacle_count'] == 0
    assert any('what an apo scaffold is being loaded to provide' in c for c in on_cu['compatible'])

    on_haem = obstacles(ctx(catalyst=catalyst, solvent='water', temperature_c='25'), 'heme')
    assert any('would have to replace it' in o for o in on_haem['obstacles'])


def test_a_different_metal_is_still_an_obstacle_on_a_substituted_platform():
    result = obstacles(ctx(catalyst='palladium diacetate', solvent='toluene',
                           temperature_c='110'), 'Cu')
    assert result['obstacle_count'] == 3
    assert any('needs Pd' in o for o in result['obstacles'])
