# Third-party methods and data

RXNFP is the work of Schwaller and colleagues. This project uses its official `bert_ft` weights, the published SMILES tokenization pattern and final-layer CLS pooling. The inference adapter uses current Transformers/PyTorch without importing the old training stack. This is reuse of RXNFP, not a new representation model.

- Official repository: https://github.com/rxn4chemistry/rxnfp
- Pinned commit: `6fd48f4927c2178555cc5d71dbfb225fb178f43c`
- Tokenization: https://github.com/rxn4chemistry/rxnfp/blob/6fd48f4927c2178555cc5d71dbfb225fb178f43c/rxnfp/tokenization.py
- Fingerprint extraction: https://github.com/rxn4chemistry/rxnfp/blob/6fd48f4927c2178555cc5d71dbfb225fb178f43c/rxnfp/transformer_fingerprints.py
- License: https://github.com/rxn4chemistry/rxnfp/blob/6fd48f4927c2178555cc5d71dbfb225fb178f43c/LICENSE

The public reference implementation truncates long inputs. Here, unsupported vocabulary and overlength reactions are explicitly excluded and counted. Agents are deliberately omitted from the common structural view for all encoders; the original reaction and conditions remain available. Therefore, fingerprints correspond to this stated input convention, not necessarily every fingerprint precomputed upstream.

DRFP is used through the official package, with 2048 dimensions, radius 3, rings enabled, and binary Tanimoto similarity. It is a distinct, published method: https://github.com/reymond-group/drfp.

The Schneider50k reference table comes from the pinned RXNFP repository. It is used as a local patent reaction reference pool. Inclusion is not proof that every row is nonenzymatic, that its catalytic conditions are known, or that an enzyme implementation is absent. Its reaction labels are source annotations. Patent dates and experimental provenance need separate verification before strict historical evaluation.

EnzymeEngineeringDB V6 is a local imported reference. A legacy cofactor label does not establish the actual metal oxidation state or catalytic mechanism. Raw legacy rows remain unreviewed. Code licensing must not be assumed to grant redistribution rights for every underlying data source.

Raw source files, model weights and detailed local indices are stored under ignored `data/local/`. Downloaded RXNFP assets are verified against pinned Git blob hashes and recorded with SHA256 hashes. Authoritative publication references and limitations are also discussed in the research proposal.
