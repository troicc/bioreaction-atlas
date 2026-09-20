"""Read an RD File (.rdf) reaction export into plain rows.

RD Files are the standard reaction interchange format and are what Reaxys,
SciFinder and ELN systems emit for reaction data. This reader makes no
assumption about a particular vendor's data-field names: it returns whatever
$DTYPE fields the file actually carries, so the mapping can be decided by
looking at the real export rather than by guessing.
"""
import re

from rdkit import Chem
from rdkit.Chem import rdChemReactions

RECORD = re.compile(r'^\$RFMT', re.MULTILINE)


def _reaction_smiles(block):
    """Canonical reaction SMILES from an RXN block, with aromaticity re-perceived."""
    reaction = rdChemReactions.ReactionFromRxnBlock(block, sanitize=False, removeHs=False)
    if reaction is None:
        raise ValueError('RXN block could not be parsed')
    sides = []
    for getter, count in ((reaction.GetReactantTemplate, reaction.GetNumReactantTemplates()),
                          (reaction.GetAgentTemplate, reaction.GetNumAgentTemplates()),
                          (reaction.GetProductTemplate, reaction.GetNumProductTemplates())):
        parts = []
        for i in range(count):
            mol = getter(i)
            try:
                Chem.SanitizeMol(mol)
            except Exception as exc:  # noqa: BLE001 - a bad component must not kill the file
                raise ValueError(f'component {i} failed sanitization: {exc}') from exc
            # Atom maps are Reaxys bookkeeping, not chemistry; the encoders strip them anyway.
            for atom in mol.GetAtoms():
                atom.SetAtomMapNum(0)
            smiles = Chem.MolToSmiles(mol)
            if smiles:
                parts.append(smiles)
        sides.append('.'.join(parts))
    if not sides[0] or not sides[2]:
        raise ValueError('reaction has an empty reactant or product side')
    return '>'.join(sides)


def _fields(text):
    """$DTYPE/$DATUM pairs; a $DATUM may span lines until the next directive."""
    found, name, value = {}, None, []
    for line in text.splitlines():
        if line.startswith('$DTYPE'):
            if name is not None:
                found[name] = '\n'.join(value).strip()
            name, value = line[len('$DTYPE'):].strip(), []
        elif line.startswith('$DATUM'):
            value.append(line[len('$DATUM'):].strip())
        elif name is not None and not line.startswith('$'):
            value.append(line.rstrip())
    if name is not None:
        found[name] = '\n'.join(value).strip()
    return found


def read_rdf(text):
    """Return (rows, failures). Each row is {'reaction_smiles': ..., **data fields}."""
    rows, failures = [], []
    chunks = RECORD.split(text)
    for n, chunk in enumerate(chunks[1:], 1):
        if '$RXN' not in chunk:
            continue
        body = chunk[chunk.index('$RXN'):]
        cut = body.find('$DTYPE')
        block, tail = (body[:cut], body[cut:]) if cut != -1 else (body, '')
        # Strip the $RXN directive line itself; RDKit expects the block beneath it.
        block = block.split('\n', 1)[1] if '\n' in block else ''
        try:
            smiles = _reaction_smiles(block)
        except ValueError as exc:
            failures.append({'record': n, 'reason': str(exc)})
            continue
        rows.append({'reaction_smiles': smiles, **_fields(tail)})
    return rows, failures


def field_summary(rows):
    """Field name -> (how many records carry it, one example value)."""
    summary = {}
    for row in rows:
        for key, value in row.items():
            if key == 'reaction_smiles' or not value:
                continue
            count, example = summary.get(key, (0, value))
            summary[key] = (count + 1, example)
    return dict(sorted(summary.items(), key=lambda kv: -kv[1][0]))


# Concept -> field-name patterns, most specific first. A pattern beginning with
# "=" must match the whole field name; otherwise it is a substring test. Vendor
# codes need exact matching, because "rxd.t" is also a prefix of "rxd.tim".
HEURISTIC = {
    'catalyst': ('catalyst', '=rxd.cat', '=rxd_cat'),
    'solvent': ('solvent', '=rxd.sol', '=rxd_sol'),
    'reagents': ('reagent', '=rxd.rgt', '=rxd_rgt'),
    'yield_percent': ('yield', '=rxd.ypro', '=rxd_ypro', 'ypro'),
    'time_h': ('time', '=rxd.tim', '=rxd_tim'),
    'temperature_c': ('temperature', '=rxd.t', '=rxd_t'),
    'source_doi': ('doi',),
    'source_year': ('publication year', '=pub.year', '=cit.py', 'year'),
    'external_id': ('reaxys id', '=rx.id', '=rx_id', 'reaction id'),
    'source_locator': ('page', 'locator', 'citation'),
    'reaction_name': ('reaction type', 'classification', 'title'),
}


def _matches(field, pattern):
    field = field.lower()
    return field == pattern[1:] if pattern.startswith('=') else pattern in field


def guess_mapping(rows):
    """Best-effort field mapping. Always shown to the user before it is trusted."""
    available = [k for k in field_summary(rows)]
    mapping = {}
    for column, needles in HEURISTIC.items():
        for needle in needles:
            match = next((f for f in available if _matches(f, needle) and f not in mapping.values()), None)
            if match:
                mapping[column] = match
                break
    return mapping
