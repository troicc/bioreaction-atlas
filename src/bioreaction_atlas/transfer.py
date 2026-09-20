"""What a recorded abiotic procedure would need changed to run in a protein.

This states obstacles, never verdicts. An enzyme in a water-miscible cosolvent at 30 °C
is routine; an enzyme in anhydrous dichloromethane at -78 °C is not, but it is also not
impossible, and the project's rules forbid absolute rules such as "organic solvent means
infeasible". So each axis reports what would have to be supplied or replaced, and the
count of obstacles is a sort key a reviewer can use, explicitly not a feasibility score.

Every judgement here is about what proteins tolerate, which is why it needs no
transferability labels to be defensible.
"""
import re

# A protein works in water. A water-miscible cosolvent is ordinary practice; a
# water-immiscible solvent needs a biphasic system or a solvent-tolerant scaffold.
AQUEOUS = ('water', 'buffer')
MISCIBLE = ('methanol', 'ethanol', 'isopropanol', 'acetonitrile', 'dimethyl sulfoxide',
            'dmso', 'n,n-dimethylformamide', 'dimethylformamide', 'dmf', 'dioxane',
            'tetrahydrofuran', 'acetone', 'glycerol', 'ethylene glycol')
IMMISCIBLE = ('dichloromethane', 'chloroform', 'toluene', 'benzene', 'hexane', 'heptane',
              'pentane', 'cyclohexane', 'diethyl ether', 'ethyl acetate', 'dichloroethane',
              'carbon tetrachloride', 'xylene', 'chlorobenzene')

# Metals a platform natively carries. Anything else needs installation or substitution,
# which is a real and published step, not a disqualification.
PLATFORM_METALS = {'heme': {'Fe'}, 'PLP': set(), 'Fe(II)': {'Fe'}}


def platform_metals(cofactor):
    """Metals a platform carries. A bare element symbol names a metal-substituted
    scaffold already loaded with it, so Cu means an apo scaffold holding copper."""
    if cofactor in PLATFORM_METALS:
        return PLATFORM_METALS[cofactor]
    from .activation import ELEMENT_NAMES
    return {cofactor} if cofactor in ELEMENT_NAMES else set()

# A platform whose protein *is* the ligand. For these, a reaction that depends on a
# defined external ligand is not an obstacle: supplying that coordination environment is
# the whole design premise of metal substitution. For a haem platform the porphyrin is
# already the ligand, so the same requirement is a genuine conflict.
LIGAND_SUPPLYING_PLATFORMS = {'Cu', 'Ni', 'Co', 'Ir', 'Ru', 'Rh', 'Mn', 'Pd', 'Fe(II)'}

# A protein supplies its own ligand environment. A procedure that depends on a specific
# external ligand is asking the scaffold to reproduce that function.
LIGANDS = ('phosphine', 'binap', 'bisoxazoline', 'box', 'salen', 'pybox', 'phox',
           'carbene', 'nhc', 'bipyridine', 'phenanthroline', 'josiphos', 'dppf',
           'xantphos', 'segphos', 'tolbinap', 'pdti', 'esp',
           # N-heterocyclic carbene ligands are usually written out in full.
           'imidazolylidene', 'imidazolinylidene', 'diisopropylphenyl', 'mesityl',
           'triphenylphosphine', 'cyclopentadienyl', 'porphyrin', 'corrole')


def _flat(text):
    """Sources write "1,2-dichloro-ethane" and "dichloroethane" for the same solvent."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())

# Conditions that damage or denature a protein outright.
HARSH = {
    'strong base': ('butyllithium', 'n-buli', 'lda', 'lithium diisopropylamide',
                    'sodium hydride', 'potassium tert-butoxide', 'sodium amide',
                    'grignard', 'magnesium bromide'),
    'strong acid': ('sulfuric acid', 'trifluoromethanesulfonic', 'triflic acid',
                    'hydrogen fluoride', 'aluminium trichloride', 'aluminum trichloride',
                    'boron trifluoride', 'titanium tetrachloride', 'tin tetrachloride'),
    'strong oxidant': ('chromium', 'permanganate', 'osmium tetroxide', 'lead tetraacetate',
                       'ceric ammonium', 'dess-martin'),
}

PROTEIN_MIN_C, PROTEIN_MAX_C = 0.0, 60.0


def _number(value):
    if not value:
        return None
    match = re.search(r'-?\d+(?:\.\d+)?', str(value))
    return float(match.group()) if match else None


# Reagents whose common name does not spell out the metal they carry.
METAL_ALIASES = {
    'hemin': 'Fe', 'haemin': 'Fe', 'heme': 'Fe', 'haem': 'Fe', 'ferrocene': 'Fe',
    'ferric': 'Fe', 'ferrous': 'Fe', 'protoporphyrin': 'Fe', 'cobalamin': 'Co',
    'salcomine': 'Co', 'wilkinson': 'Rh', 'grubbs': 'Ru', 'crabtree': 'Ir',
    'vaska': 'Ir', 'schwartz': 'Zr', 'cuprate': 'Cu', 'cupric': 'Cu', 'cuprous': 'Cu',
    'argentic': 'Ag', 'plumbane': 'Pb', 'stannane': 'Sn', 'titanocene': 'Ti',
    'zirconocene': 'Zr', 'molybdate': 'Mo', 'tungstate': 'W', 'vanadate': 'V',
}


def _metals(text):
    from .activation import ELEMENT_NAMES, _mentions_metal
    found = {symbol for symbol in ELEMENT_NAMES if _mentions_metal(text or '', symbol)}
    lower = (text or '').lower()
    found |= {symbol for alias, symbol in METAL_ALIASES.items() if alias in lower}
    return found


def medium(solvent):
    """Return (class, obstacle or None)."""
    text = _flat(solvent)
    if not text:
        return 'unstated', None
    if any(_flat(k) in text for k in AQUEOUS):
        return 'aqueous', None
    if any(_flat(k) in text for k in MISCIBLE):
        return 'water-miscible', None
    if any(_flat(k) in text for k in IMMISCIBLE):
        return 'water-immiscible', f'runs in a water-immiscible solvent ({solvent}); needs a biphasic ' \
                                   'system, a cosolvent substitution or a solvent-tolerant scaffold'
    return 'other', None


def obstacles(context, cofactor, reported_results=None):
    """List what would have to change, and what already fits. Neither is a verdict."""
    blocking, compatible, unknown = [], [], []

    kind, note = medium(context.get('solvent'))
    if note:
        blocking.append(note)
    elif kind in ('aqueous', 'water-miscible'):
        compatible.append(f'medium is {kind}')
    elif kind == 'unstated':
        unknown.append('no solvent recorded')

    temperature = _number(context.get('temperature_c'))
    if temperature is None:
        unknown.append('no temperature recorded')
    else:
        if temperature < PROTEIN_MIN_C:
            blocking.append(f'runs at {temperature:g} °C, below the range a protein stays folded and active in')
        elif temperature > PROTEIN_MAX_C:
            blocking.append(f'runs at {temperature:g} °C, above the range most scaffolds tolerate')
        else:
            compatible.append(f'temperature {temperature:g} °C is within protein range')

    catalyst = context.get('catalyst') or ''
    platform = platform_metals(cofactor)
    found = _metals(catalyst)
    if found:
        shared = found & platform
        if shared:
            compatible.append(f'uses {"/".join(sorted(shared))}, which the platform already carries')
        else:
            blocking.append(f'needs {"/".join(sorted(found))}, which this platform does not natively carry; '
                            'metal substitution is a separate published step')
    elif catalyst.strip() and not platform:
        compatible.append('metal-free, like the platform')
    elif not catalyst.strip():
        unknown.append('no catalyst or reagent recorded')

    flat_catalyst = _flat(catalyst)
    ligands = [name for name in LIGANDS if _flat(name) in flat_catalyst]
    if ligands:
        named = ', '.join(sorted(set(ligands)))
        if cofactor in LIGAND_SUPPLYING_PLATFORMS:
            compatible.append(f'depends on a defined ligand ({named}), which is what an apo '
                              'scaffold is being loaded to provide')
        else:
            blocking.append(f'depends on an external ligand ({named}); the scaffold already '
                            'carries its own and would have to replace it')

    lower = catalyst.lower() + ' ' + (context.get('reagents') or '').lower()
    for label, needles in HARSH.items():
        hit = [n for n in needles if n in lower]
        if hit:
            blocking.append(f'uses a {label} ({hit[0]}) that would denature a protein')

    yield_value = _number((reported_results or {}).get('yield_percent'))
    if yield_value is not None and yield_value >= 70:
        compatible.append(f'{yield_value:g}% reported yield, so the abiotic step itself is efficient')

    return {
        'medium': kind,
        'temperature_c': temperature,
        'catalyst_metals': sorted(found),
        'obstacles': blocking,
        'compatible': compatible,
        # Unstated conditions are not compatible conditions. Counting them as zero
        # obstacles would rank records with no recorded procedure first.
        'unknown': unknown,
        # A sort key, not a score. Two obstacles are not twice one obstacle.
        'obstacle_count': len(blocking),
        'unknown_count': len(unknown),
        'interpretation': 'Obstacles are what a transfer would have to supply or replace. '
                          'None of them makes a reaction infeasible in a protein, and the count '
                          'is not a feasibility estimate.',
    }
