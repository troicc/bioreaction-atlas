from bioreaction_atlas.intermediates import RULES, normalize_reactants

OXINDOLE = 'CC1C(=O)Nc2ccccc21'
PRODUCT = 'CC1(C[C@H](N)C(=O)O)C(=O)Nc2ccccc21'
FAMILY = 'aminoacrylate_addition'


def trpb(amino_acid):
    return f'{OXINDOLE}.{amino_acid}>>{PRODUCT}'


def test_serine_becomes_the_aminoacrylate():
    out, rule = normalize_reactants(trpb('N[C@@H](CO)C(=O)O'), FAMILY)
    assert 'C=C(N)C(=O)O' in out.split('>')[0]
    assert rule and 'aminoacrylate' in rule


def test_cysteine_and_phosphoserine_use_the_same_rule():
    for precursor in ('N[C@@H](CS)C(=O)O', 'N[C@@H](COP(=O)(O)O)C(=O)O'):
        out, rule = normalize_reactants(trpb(precursor), FAMILY)
        assert 'C=C(N)C(=O)O' in out.split('>')[0] and rule


def test_threonine_gives_the_beta_substituted_intermediate():
    out, rule = normalize_reactants(trpb('C[C@@H](O)[C@H](N)C(=O)O'), FAMILY)
    assert 'CC=C(N)C(=O)O' in out.split('>')[0]
    assert rule and 'crotonate' in rule


def test_an_amino_acid_without_a_leaving_group_is_untouched():
    for inert in ('C[C@H](N)C(=O)O', 'NCC(=O)O'):
        out, rule = normalize_reactants(trpb(inert), FAMILY)
        assert rule is None and out == trpb(inert)


def test_only_the_reactant_side_is_rewritten():
    """The intermediate is consumed before the product forms."""
    original = trpb('N[C@@H](CO)C(=O)O')
    out, _ = normalize_reactants(original, FAMILY)
    assert out.split('>>')[1] == original.split('>>')[1]


def test_other_families_have_no_rule_and_are_returned_unchanged():
    carbene = 'CCOC(=O)C=[N+]=[N-].c1ccc2[nH]ccc2c1>>CCOC(=O)Cc1c[nH]c2ccccc12'
    out, rule = normalize_reactants(carbene, 'metal_carbene')
    assert rule is None and out == carbene
    assert 'metal_carbene' not in RULES


def test_one_precursor_is_rewritten_not_every_fragment():
    """Two amino acids in one reaction must not both be consumed by the rule."""
    both = f'N[C@@H](CO)C(=O)O.N[C@@H](CS)C(=O)O>>{PRODUCT}'
    out, rule = normalize_reactants(both, FAMILY)
    assert rule
    reactants = out.split('>')[0].split('.')
    assert sum('C=C(N)C(=O)O' == r for r in reactants) == 1
    assert any('CS' in r for r in reactants)


def test_an_unparseable_fragment_does_not_abort_normalization():
    out, rule = normalize_reactants(f'not_a_molecule.N[C@@H](CO)C(=O)O>>{PRODUCT}', FAMILY)
    assert rule and 'C=C(N)C(=O)O' in out.split('>')[0]
