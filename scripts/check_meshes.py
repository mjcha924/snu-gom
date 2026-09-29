"""Check the externally supplied V0.6 meshes before opening the simulator."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'motion/src/snu_bear_motion/data/robot/meshes_m'
def check_meshes():
 expected=json.loads((ROOT/'docs/V06_MESH_SHA256.json').read_text())
 missing=[]
 for name,sha in expected.items():
  target=DEST/Path(name).name
  if not target.is_file():missing.append(target.name)
  elif hashlib.sha256(target.read_bytes()).hexdigest()!=sha:
   raise RuntimeError(f'{target} differs from V0.6; use matching meshes or update the model deliberately.')
 if missing:
  raise RuntimeError('Missing CAD meshes: '+', '.join(missing)+'. Copy meshes_m from SNU_Bear_v06_URDF.zip into '+str(DEST)+'. See docs/SIMULATION_ASSETS.md.')
 return DEST
if __name__=='__main__':print(f'Verified 10 meshes: {check_meshes()}')
