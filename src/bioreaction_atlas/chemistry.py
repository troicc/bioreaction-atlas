"""Transparent, directional Morgan count-difference baseline; not RXNFP or DRFP."""

import math
from rdkit import Chem, rdBase
from rdkit.Chem import rdFingerprintGenerator

PARAMETERS = {"name": "morgan_count_difference", "radius": 2, "fp_size": 4096,
              "include_chirality": True, "agents_in_fingerprint": False,
              "similarity": "cosine_signed", "rdkit_version": rdBase.rdkitVersion}
GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=4096, includeChirality=True)


def canonical_reaction(text):
    parts = text.strip().split(">")
    if len(parts) != 3 or not parts[0] or not parts[2]:
        raise ValueError("反应需为 反应物>试剂>产物，且两端非空")
    result = []
    for i, side in enumerate(parts):
        if i == 1 and not side:
            result.append("")
            continue
        molecules = []
        for smi in side.split("."):
            mol = Chem.MolFromSmiles(smi)
            if mol is None or mol.GetNumAtoms() == 0:
                raise ValueError(f"无法解析结构：{smi[:80]}")
            for atom in mol.GetAtoms():
                atom.SetAtomMapNum(0)
            molecules.append(Chem.MolToSmiles(mol, isomericSmiles=True))
        result.append(".".join(sorted(molecules)))
    return ">".join(result)


def fingerprint(reaction):
    reactants, _, products = canonical_reaction(reaction).split(">")
    vector = {}
    for side, sign in ((reactants, -1), (products, 1)):
        for smi in side.split("."):
            fp = GENERATOR.GetCountFingerprint(Chem.MolFromSmiles(smi))
            for bit, count in fp.GetNonzeroElements().items():
                key = str(bit)
                vector[key] = vector.get(key, 0) + sign * count
    return {k: v for k, v in vector.items() if v}


def cosine(a, b):
    na, nb = sum(v*v for v in a.values()), sum(v*v for v in b.values())
    if not na or not nb:
        raise ValueError("净变化指纹为零，无法计算相似度")
    return sum(v*b.get(k, 0) for k, v in a.items()) / math.sqrt(na*nb)
