"""Restore the exact CAD meshes offline and verify SHA-256 before writing."""
from pathlib import Path
import base64,hashlib,json,lzma
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'motion/src/snu_bear_motion/data/robot/meshes_m'
def restore():
 assets=ROOT/'assets/v06_meshes'
 manifest=json.loads((assets/'manifest.json').read_text())
 DEST.mkdir(parents=True,exist_ok=True)
 for entry in manifest['files']:
  target=DEST/entry['name']
  if target.exists():
   if hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:
    raise RuntimeError(f'{target} differs from V0.6; move your edited mesh aside before restoring.')
   continue
  encoded=''.join((assets/c).read_text() for c in entry['chunks'])
  raw=lzma.decompress(base64.b64decode(encoded,validate=True))
  if len(raw)!=entry['size_bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:
   raise RuntimeError(f'Corrupt mesh data: {entry["name"]}')
  temp=target.with_suffix('.stl.tmp');temp.write_bytes(raw);temp.replace(target)
 return DEST
if __name__=='__main__':print(f'Verified 10 meshes: {restore()}')
