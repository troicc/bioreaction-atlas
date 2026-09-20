"""Rewrite a reaction in terms of the reactive intermediate its platform forms.

An enzyme and its abiotic counterpart often share an intermediate but not a
precursor. TrpB consumes serine and forms the aminoacrylate in the active site,
while the abiotic route starts from a dehydroalanine that is already formed. The
shared object appears in neither reaction SMILES, so structural similarity cannot
see it.

Normalisation applies an explicit, auditable transformation to the precursor so
both sides are expressed at the same level. It is a stated chemical rule, not an
inference: every rule names the platform it belongs to, and a reaction that does
not match is returned unchanged and reported as such.
"""
from rdkit import Chem
from rdkit.Chem import AllChem

# Each rule is (name, reaction SMARTS). The precursor is rewritten into the
# intermediate the cofactor forms from it; the leaving group is dropped.
# Each rule is (name, reaction SMARTS). The precursor is rewritten into the
# intermediate the cofactor forms from it, and the leaving group is dropped. The
# product's hydrogen count is set explicitly, because an sp3 alpha carbon carries a
# hydrogen the sp2 intermediate must not keep.
LEAVING = '[OX2H1,$([OX2][PX4]),SX2H1,Cl,Br,I:4]'

RULES = {
    'aminoacrylate_addition': [
        (
            'beta-elimination from serine, cysteine or an activated variant to the aminoacrylate',
            f'[NX3:1][CX4H1:2]([CX4H2:3]{LEAVING})[CX3:5](=[OX1:6])[OX2H1,OX1-:7]'
            '>>[NX3:1][CH0:2](=[CH2:3])[CX3:5](=[OX1:6])[OX2:7]'
        ),
        (
            'beta-elimination from threonine to the 2-aminocrotonate',
            f'[NX3:1][CX4H1:2]([CX4H1:3]{LEAVING})[CX3:5](=[OX1:6])[OX2H1,OX1-:7]'
            '>>[NX3:1][CH0:2](=[CH1:3])[CX3:5](=[OX1:6])[OX2:7]'
        ),
    ],
}


# Applied symmetrically to both sides, and repeatedly until nothing changes.
# Protecting groups and ester choices are synthetic conveniences, not the chemistry;
# stripping them expresses the enzyme's free intermediate and the abiotic reagent's
# protected form as the same reactive core.
CANONICAL = {
    'aminoacrylate_addition': [
        (
            'remove N-acyl, N-carbamate or N-sulfonyl protection from the acceptor nitrogen',
            '[CX3:3]=[CX3:2]([NX3H1:1][$([CX3]=[OX1]),$([SX4](=O)=O)])[CX3:5](=[OX1:6])[OX2,NX3:7]'
            '>>[C:3]=[C:2]([NH2:1])[C:5](=[O:6])[*:7]'
        ),
        (
            'convert the acceptor ester or amide to the free acid',
            '[CX3:3]=[CX3:2]([NX3:1])[CX3:5](=[OX1:6])[OX2H0,NX3:7]'
            '>>[C:3]=[C:2]([N:1])[C:5](=[O:6])[OX2H]'
        ),
    ],
}


def _run(rule, mol):
    reaction = AllChem.ReactionFromSmarts(rule)
    if reaction is None:
        return None
    for products in reaction.RunReactants((mol,)):
        combined = products[0] if len(products) == 1 else None
        if combined is None:
            continue
        try:
            Chem.SanitizeMol(combined)
        except Exception:  # noqa: BLE001 - a rule that yields nonsense is simply not applied
            continue
        return Chem.MolToSmiles(combined)
    return None


def normalize_reactants(reaction_smiles, family):
    """Return (rewritten reaction, rule applied or None).

    Only the reactant side is touched; products are left alone because the
    intermediate is consumed before the product forms.
    """
    rules = RULES.get(family)
    if not rules:
        return reaction_smiles, None
    parts = reaction_smiles.split('>')
    fragments = parts[0].split('.')
    for name, rule in rules:
        rewritten, hit = [], False
        for fragment in fragments:
            mol = Chem.MolFromSmiles(fragment)
            product = _run(rule, mol) if mol is not None else None
            if product and not hit:
                rewritten.append(product)
                hit = True
            else:
                rewritten.append(fragment)
        if hit:
            parts[0] = '.'.join(rewritten)
            return '>'.join(parts), name
    return reaction_smiles, None


def canonicalize(reaction_smiles, family, max_passes=4):
    """Reduce a family's acceptor to its unprotected reactive core, on both sides.

    Protecting groups and ester choices differ between an enzyme's free intermediate
    and a chemist's bench reagent without changing the chemistry. Applied to every
    fragment on both sides, repeatedly until stable.

    Returns (rewritten reaction, list of rules applied).
    """
    rules = CANONICAL.get(family)
    if not rules:
        return reaction_smiles, []
    parts = reaction_smiles.split('>')
    applied = []
    for index in (0, len(parts) - 1):
        fragments = parts[index].split('.')
        for position, fragment in enumerate(fragments):
            for _ in range(max_passes):
                changed = False
                for name, rule in rules:
                    mol = Chem.MolFromSmiles(fragment)
                    product = _run(rule, mol) if mol is not None else None
                    if product and product != fragment:
                        fragment, changed = product, True
                        if name not in applied:
                            applied.append(name)
                if not changed:
                    break
            fragments[position] = fragment
        parts[index] = '.'.join(fragments)
    return '>'.join(parts), applied
