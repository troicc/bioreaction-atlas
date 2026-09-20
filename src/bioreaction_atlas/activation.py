"""Activation-family labels and catalytic context recovered from the agents segment.

Reaction SMILES of the form reactants>agents>products carry the catalyst, reagents
and solvent in the middle segment. `structure_view` deliberately discards it so that
net transformations can be compared across catalytic environments; this module
recovers it as structured metadata instead, so the activation layer is available
for filtering and review without changing any encoded structure.

Assignments here are lexical, not mechanistic. A detected metal is a species present
in the recorded agents, never evidence of how the reaction actually works.
"""
from functools import lru_cache
import re

from rdkit import Chem

# Families are search leads from research/activation_family_map.md. The label records
# which enzyme platform motivated importing a reaction; it is not a mechanism claim.
FAMILIES = {
    'metal_carbene': 'Metal carbene transfer (haem carbene analogue)',
    'metal_nitrene': 'Metal nitrene transfer (haem nitrene analogue)',
    'hat_oxidation': 'HAT / high-valent metal-oxo C-H oxidation (non-haem Fe analogue)',
    'metal_substituted': 'Homogeneous catalysis for an installed metal (Cu, Ni, Co, Ir)',
    'enamine_iminium': 'Enamine / iminium organocatalysis (PLP analogue)',
    'nhc_umpolung': 'NHC acyl-anion umpolung (ThDP / Breslow analogue)',
    'transfer_hydrogenation': 'Hydride transfer to activated alkenes (ene-reductase analogue)',
    'baeyer_villiger': 'Peracid / Criegee oxygen insertion (BVMO analogue)',
    'photoredox_radical': 'Photoredox, EDA and HAT radical chemistry (photoenzyme analogue)',
    'electrophilic_halogenation': 'Electrophilic halogenation (flavin halogenase analogue)',
    'cation_cyclization': 'Brønsted/Lewis acid cation-olefin cascade (terpene cyclase analogue)',
    'acyl_transfer': 'Organocatalytic acyl transfer and base-catalysed C-C bond formation (hydrolase promiscuity analogue)',
    'alkylation_sam': 'Electrophilic or radical alkylation (SAM / radical-SAM analogue)',
    'lewis_acid': 'Lewis-acid carbonyl activation (Zn enzyme analogue)',
    'background_patent': 'Routine patent chemistry retained as a negative control',
}

# Family membership screens. A reaction belongs to a family if its reactant side
# carries the diagnostic substructure OR its recorded catalyst carries a diagnostic
# metal. Either alone is sufficient: some sources annotate the catalyst but not the
# precursor, and some the reverse. Families with no clean screen are left unscreened
# rather than given a loose one that would silently drop real chemistry.
SCREENS = {
    'metal_carbene': {
        # The diazo carbon must carry a carbon substituent. Diazomethane and
        # TMS-diazomethane are methylating reagents for carboxylic acids, not
        # carbene-transfer substrates, and they are the only "diazo" chemistry a
        # medicinal-chemistry patent corpus contains.
        'reactant_smarts': {'substituted diazo': '[#6X3;$([#6](=[N+]=[N-])[#6])]=[N+]=[N-]'},
        # Pd is deliberately absent: Suzuki/Sonogashira/Buchwald steps are the most
        # common substrate-preparation contaminant in a methodology paper, and Pd is
        # not the haem-carbene analogue this family is mining for.
        'catalyst_metals': {'Rh', 'Cu', 'Co', 'Ir', 'Ru', 'Fe'},
    },
    'metal_nitrene': {
        'reactant_smarts': {'organic azide': '[NX2]=[N+]=[N-]',
                            'iminoiodinane': '[IX2]=[NX2]'},
        'catalyst_metals': {'Rh', 'Cu', 'Co', 'Ag', 'Ir', 'Mn', 'Fe'},
    },
    'hat_oxidation': {
        'reactant_smarts': {},
        'catalyst_metals': {'Fe', 'Mn', 'Cu', 'Ru'},
    },
    'metal_substituted': {
        'reactant_smarts': {},
        'catalyst_metals': {'Cu', 'Ni', 'Co', 'Ir', 'Pd', 'Ru', 'Rh'},
    },
    'photoredox_radical': {
        'reactant_smarts': {},
        'catalyst_metals': {'Ir', 'Ru'},
        'catalyst_text': ('4czipn', 'acridinium', 'eosin', 'rose bengal', 'photocatalyst'),
    },
    'enamine_iminium': {
        'reactant_smarts': {},
        'catalyst_metals': set(),
        'catalyst_text': ('proline', 'imidazolidinone', 'prolinol', 'cinchona', 'organocatalyst'),
    },
    'nhc_umpolung': {
        'reactant_smarts': {},
        'catalyst_metals': set(),
        'catalyst_text': ('thiazolium', 'triazolium', 'imidazolium', 'carbene', 'nhc'),
    },
    'transfer_hydrogenation': {
        'reactant_smarts': {},
        'catalyst_metals': set(),
        'catalyst_text': ('hantzsch', 'phosphoric acid', 'imidazolidinone'),
    },
}

TRANSITION_METALS = frozenset(
    'Sc Ti V Cr Mn Fe Co Ni Cu Zn Y Zr Nb Mo Tc Ru Rh Pd Ag Cd Hf Ta W Re Os Ir Pt Au Hg'.split())
OTHER_METALS = frozenset('Li Na K Rb Cs Mg Ca Sr Ba Al Ga In Sn Pb Bi Ce La Yb Sm Eu'.split())

_SOLVENT_NAMES = {
    'ClCCl': 'dichloromethane', 'ClCCCl': '1,2-dichloroethane', 'ClC(Cl)Cl': 'chloroform',
    'C1CCOC1': 'THF', 'C1COCCO1': '1,4-dioxane', 'CCOCC': 'diethyl ether',
    'O': 'water', 'CO': 'methanol', 'CCO': 'ethanol', 'CC(C)O': 'isopropanol',
    'CCCCO': 'n-butanol', 'CC(C)(C)O': 'tert-butanol',
    'CN(C)C=O': 'DMF', 'CS(C)=O': 'DMSO', 'CN1CCCC1=O': 'NMP', 'CC#N': 'acetonitrile',
    'CCOC(C)=O': 'ethyl acetate', 'CC(C)=O': 'acetone', 'CC(=O)O': 'acetic acid',
    'Cc1ccccc1': 'toluene', 'c1ccccc1': 'benzene', 'CCCCCC': 'n-hexane',
    'CCCCC': 'n-pentane', 'C1CCCCC1': 'cyclohexane', 'OC(F)(F)F': 'trifluoromethanol',
    'OC(=O)C(F)(F)F': 'trifluoroacetic acid', 'CN(C)P(=O)(N(C)C)N(C)C': 'HMPA',
}


@lru_cache(maxsize=None)
def _canonical(smiles):
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    if mol is None:
        return None
    try:
        return Chem.MolToSmiles(mol)
    except Exception:  # noqa: BLE001 - malformed agent fragments must not abort an import
        return None


@lru_cache(maxsize=None)
def _solvent_table():
    table = {}
    for smiles, name in _SOLVENT_NAMES.items():
        key = _canonical(smiles)
        if key:
            table[key] = name
    return table


def _elements(mol):
    return {atom.GetSymbol() for atom in mol.GetAtoms()}


def agents_segment(reaction_smiles):
    """The middle segment, or '' when the record has none."""
    parts = reaction_smiles.split('>')
    return parts[1] if len(parts) == 3 else ''


def parse_agents(reaction_smiles):
    """Split the agents segment into metals, recognized solvents and everything else.

    Unparseable fragments are reported rather than dropped, so an import never
    silently loses recorded conditions.
    """
    segment = agents_segment(reaction_smiles).strip()
    result = {'metals': [], 'solvents': [], 'other_agents': [], 'unparsed': [], 'has_agents': bool(segment)}
    if not segment:
        return result
    solvents = _solvent_table()
    metals, solvent_names, others, unparsed = set(), set(), set(), []
    for fragment in segment.split('.'):
        fragment = fragment.strip()
        if not fragment:
            continue
        canonical = _canonical(fragment)
        if canonical is None:
            unparsed.append(fragment)
            continue
        mol = Chem.MolFromSmiles(fragment, sanitize=False)
        present = _elements(mol) & (TRANSITION_METALS | OTHER_METALS)
        if present:
            metals |= present
        if canonical in solvents:
            solvent_names.add(solvents[canonical])
        elif not present:
            others.add(canonical)
    result.update(metals=sorted(metals), solvents=sorted(solvent_names),
                  other_agents=sorted(others), unparsed=unparsed)
    return result


def catalytic_context(reaction_smiles, family=None):
    """A context dict in the intake schema's vocabulary, from the agents segment alone."""
    parsed = parse_agents(reaction_smiles)
    transition = [m for m in parsed['metals'] if m in TRANSITION_METALS]
    if family is not None and family not in FAMILIES:
        raise ValueError(f'Unknown activation family: {family}')
    return {
        'metal_cofactor': '/'.join(transition) or None,
        'other_metals': '/'.join(m for m in parsed['metals'] if m not in TRANSITION_METALS) or None,
        'solvent': ', '.join(parsed['solvents']) or None,
        'reagents': '.'.join(parsed['other_agents']) or None,
        'activation_family': family,
        'mechanism': None,
        # Nothing here was read from a paper, so the schema's evidence grade is explicit.
        'mechanism_evidence': '未说明',
        'context_source': 'parsed_from_agents_segment_not_read_from_primary_source',
        'unparsed_agents': parsed['unparsed'] or None,
        'has_agents': parsed['has_agents'],
    }


ELEMENT_NAMES = {
    'Rh': 'rhodium', 'Cu': 'copper', 'Co': 'cobalt', 'Ir': 'iridium', 'Ru': 'ruthenium',
    'Fe': 'iron', 'Pd': 'palladium', 'Ag': 'silver', 'Mn': 'manganese', 'Ni': 'nickel',
    'Zn': 'zinc', 'Ti': 'titanium', 'Cr': 'chromium', 'Mo': 'molybdenum', 'V': 'vanadium',
    'W': 'tungsten', 'Os': 'osmium', 'Re': 'rhenium', 'Pt': 'platinum', 'Au': 'gold',
}


def _mentions_metal(text, symbol):
    """Catalyst fields say both "Rh2(OAc)4" and "rhodium(II) acetate"."""
    # The symbol as a token: a capitalised start, not followed by a lowercase letter,
    # so "Co" matches "Co2(CO)8" and "CoCl2" but not "Copper" or "Cobalt" - those are
    # caught by the element name instead.
    if re.search(rf'(?<![A-Za-z]){symbol}(?![a-z])', text):
        return True
    name = ELEMENT_NAMES.get(symbol)
    return bool(name and name in text.lower())


def family_screen(reaction_smiles, family, catalyst_text=None):
    """Does this reaction plausibly belong to `family`?

    Returns (verdict, reason). A verdict of None means no screen is defined for the
    family, which is not the same as passing. The screen is a purity filter for bulk
    imports, never a mechanistic judgement about an individual reaction.
    """
    screen = SCREENS.get(family)
    if screen is None:
        return None, 'no screen defined for this family'
    reactants = reaction_smiles.split('>')[0]
    mol = Chem.MolFromSmiles(reactants, sanitize=False)
    if mol is not None:
        try:
            Chem.SanitizeMol(mol)
        except Exception:  # noqa: BLE001 - fall back to the catalyst evidence
            mol = None
    if mol is not None:
        for name, smarts in screen['reactant_smarts'].items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern is not None and mol.HasSubstructMatch(pattern):
                return True, f'reactant carries a {name} group'

    catalyst_metals = set(parse_agents(reaction_smiles)['metals'])
    text = (catalyst_text or '').lower()
    if catalyst_text:
        for symbol in screen['catalyst_metals']:
            if _mentions_metal(catalyst_text, symbol):
                catalyst_metals.add(symbol)
    hit = catalyst_metals & screen['catalyst_metals']
    if hit:
        return True, f"catalyst metal {'/'.join(sorted(hit))}"
    for needle in screen.get('catalyst_text', ()):
        if needle in text:
            return True, f'catalyst text matches "{needle}"'
    return False, 'no diagnostic reactant group and no diagnostic catalyst'
