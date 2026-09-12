"""Frozen structural baselines and an official-weight RXNFP inference adapter."""
from functools import lru_cache
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import numpy as np
from .chemistry import canonical_reaction, fingerprint, PARAMETERS, GENERATOR


def version(package):
    return importlib.metadata.version(package)


def structure_view(reaction):
    left, _, right = canonical_reaction(reaction).split('>')
    return left + '>>' + right


class Encoder:
    def __init__(self, backend='morgan', model_dir=None):
        if backend not in ('morgan', 'substrate', 'drfp', 'rxnfp'):
            raise ValueError('Unknown encoder: ' + backend)
        self.backend = backend
        self.parameters = {'backend': backend, 'structure_view': 'reactants_only_no_agents',
                           'rdkit_version': PARAMETERS['rdkit_version']}
        if backend in ('morgan', 'substrate'):
            self.parameters.update(radius=2, dimension=4096, chirality=True, metric='cosine')
        elif backend == 'drfp':
            from drfp import DrfpEncoder
            self.drfp = DrfpEncoder
            self.parameters.update(dimension=2048, radius=3, min_radius=0, rings=True,
                                   metric='tanimoto', drfp_version=version('drfp'))
        else:
            if model_dir is None:
                raise ValueError('RXNFP requires --model-dir pointing to pinned official weights')
            import torch
            from transformers import BertModel, BertTokenizer
            # The RXNFP public SMILES regex and CLS pooling convention are MIT-licensed.
            # Source and attribution: docs/THIRD_PARTY.md.
            pattern = re.compile(r'(\%\([0-9]{3}\)|\[[^\]]+]|Br?|Cl?|N|O|S|P|F|I|b|c|n|o|s|p|\||\(|\)|\.|=|#|-|\+|\\|\/|:|~|@|\?|>>?|\*|\$|\%[0-9]{2}|[0-9])')

            class SmilesTokenizer(BertTokenizer):
                def _tokenize(self, text, **kwargs):
                    tokens = pattern.findall(text)
                    if ''.join(tokens) != text:
                        raise ValueError('RXNFP tokenizer cannot losslessly tokenize this reaction')
                    return tokens

            folder = Path(model_dir)
            hashes = {f: hashlib.sha256((folder/f).read_bytes()).hexdigest()
                      for f in ('config.json', 'vocab.txt', 'pytorch_model.bin')}
            self.torch = torch
            torch.set_num_threads(min(4, torch.get_num_threads()))
            self.model = BertModel.from_pretrained(folder, local_files_only=True, weights_only=True).eval()
            self.tokenizer = SmilesTokenizer(str(folder/'vocab.txt'), do_lower_case=False)
            self.parameters.update(dimension=self.model.config.hidden_size, metric='cosine',
                                   weights_sha256=hashes, torch_version=version('torch'),
                                   transformers_version=version('transformers'), pooling='last_hidden_state_CLS',
                                   device='cpu', truncation=False, max_tokens=self.model.config.max_position_embeddings)

    def prepare(self, reaction):
        text = structure_view(reaction)
        if self.backend == 'rxnfp':
            tokens = self.tokenizer.tokenize(text)
            if len(tokens)+2 > self.model.config.max_position_embeddings:
                raise ValueError('RXNFP token limit exceeded; record excluded instead of truncating chemistry')
            unknown = [t for t in tokens if t not in self.tokenizer.vocab]
            if unknown:
                raise ValueError('RXNFP vocabulary lacks token(s): ' + ', '.join(sorted(set(unknown))))
        return text

    def encode(self, reactions, batch_size=32):
        if batch_size < 1:
            raise ValueError('batch_size must be positive')
        texts = [self.prepare(r) for r in reactions]
        n = len(texts)
        if not n:
            return np.zeros((0, self.parameters['dimension']), dtype=np.float32)
        if self.backend == 'drfp':
            return np.asarray(self.drfp.encode(texts, n_folded_length=2048, radius=3,
                                              min_radius=0, rings=True), dtype=np.float32)
        if self.backend == 'rxnfp':
            chunks = []
            for start in range(0, n, batch_size):
                inputs = self.tokenizer(texts[start:start+batch_size], padding=True,
                                        truncation=False, return_tensors='pt')
                with self.torch.inference_mode():
                    chunks.append(self.model(**inputs).last_hidden_state[:, 0, :].cpu().numpy())
            return np.vstack(chunks).astype(np.float32)
        matrix = np.zeros((n, 4096), dtype=np.float32)
        from rdkit import Chem
        for i, text in enumerate(texts):
            if self.backend == 'morgan':
                counts = fingerprint(text)
            else:
                counts = {}
                for smi in text.split('>')[0].split('.'):
                    fp = GENERATOR.GetCountFingerprint(Chem.MolFromSmiles(smi))
                    for bit, count in fp.GetNonzeroElements().items():
                        counts[bit] = counts.get(bit, 0) + count
            for bit, value in counts.items():
                matrix[i, int(bit)] = value
        return matrix


def pairwise_similarity(left, right, metric='cosine'):
    left, right = np.asarray(left, dtype=np.float32), np.asarray(right, dtype=np.float32)
    if left.ndim != 2 or right.ndim != 2 or left.shape[1] != right.shape[1]:
        raise ValueError('Fingerprint dimensions do not match')
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError('Non-finite fingerprint')
    dot = left @ right.T
    if metric == 'cosine':
        a, b = np.linalg.norm(left, axis=1), np.linalg.norm(right, axis=1)
        if np.any(a == 0) or np.any(b == 0):
            raise ValueError('Zero fingerprint cannot be compared')
        return np.clip(dot / (a[:, None]*b[None, :]), -1, 1)
    if metric == 'tanimoto':
        if not np.isin(left, [0, 1]).all() or not np.isin(right, [0, 1]).all():
            raise ValueError('Binary Tanimoto requires binary fingerprints')
        union = left.sum(axis=1)[:, None] + right.sum(axis=1)[None, :] - dot
        if np.any(union == 0):
            raise ValueError('Zero fingerprint cannot be compared')
        return dot / union
    raise ValueError('Unknown similarity metric')
