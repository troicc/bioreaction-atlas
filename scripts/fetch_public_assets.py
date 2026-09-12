"""Fetch pinned official RXNFP assets. No credentials, uploads or paid services."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

COMMIT = '6fd48f4927c2178555cc5d71dbfb225fb178f43c'
BASE = f'https://raw.githubusercontent.com/rxn4chemistry/rxnfp/{COMMIT}/'
ASSETS = {
 'rxnfp/config.json': ('rxnfp/models/transformers/bert_ft/config.json', 495, 'efa1d4cef29bf0c4c1fd37f7e907fcd4b4e9ceef'),
 'rxnfp/pytorch_model.bin': ('rxnfp/models/transformers/bert_ft/pytorch_model.bin', 26743150, 'e89e648340cb3229b7e39907790eecf36a0d0b1e'),
 'rxnfp/vocab.txt': ('rxnfp/models/transformers/bert_ft/vocab.txt', 3525, 'aef4e92087b2a4ea91420f38ba938e7ead9f4dbd'),
 'schneider50k.tsv': ('data/schneider50k.tsv', 25635610, '5d7faad69a75f539a50e5d254feee7c69bac3e8f'),
 'rxnclass2name.json': ('data/rxnclass2name.json', 2824, 'f5867fdcdd9e3c38023a501a14019a46cc310ca3'),
}


def verify(raw, size, git_blob):
    digest = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    if len(raw) != size or digest != git_blob:
        raise ValueError('Pinned size/Git blob mismatch; refusing unverified asset')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', default='data/local/public')
    a = p.parse_args()
    folder = Path(a.out)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {'repository': 'rxn4chemistry/rxnfp', 'commit': COMMIT, 'assets': []}
    for name, (remote, size, blob) in ASSETS.items():
        target = folder/name
        if target.exists():
            raw = target.read_bytes()
        else:
            with urllib.request.urlopen(BASE+remote, timeout=60) as response:
                raw = response.read(size+1)
        verify(raw, size, blob)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix(target.suffix+'.part')
            temp.write_bytes(raw)
            temp.replace(target)
        manifest['assets'].append({'path': name, 'url': BASE+remote, 'bytes': len(raw),
                                   'git_blob': blob, 'sha256': hashlib.sha256(raw).hexdigest()})
        print(f'Verified {name}: {len(raw)} bytes', flush=True)
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    main()
