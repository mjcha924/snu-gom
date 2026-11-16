#!/usr/bin/env python3
"""Static OBB check. Overlap of conservative boxes is not proof of CAD collision."""
from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np
from scipy.spatial.transform import Rotation
from itertools import combinations
P=Path(__file__).resolve().parents[1]
r=E.parse(P/'urdf/snu_gom_preview_relative.urdf').getroot()
def tf(e):
 o=e.find('origin');T=np.eye(4)
 if o is not None:
  T[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ')
  T[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
 return T
T={'base_reference':np.eye(4)};pending=list(r.findall('joint'));adj=set()
while pending:
 remaining=[]
 for j in pending:
  a=j.find('parent').get('link');b=j.find('child').get('link');adj.add(frozenset([a,b]))
  if a in T:T[b]=T[a]@tf(j)
  else:remaining.append(j)
 if len(remaining)==len(pending):raise ValueError('Disconnected or cyclic tree')
 pending=remaining
boxes=[]
for l in r.findall('link'):
 for c in l.findall('collision'):
  boxes.append((l.get('name'),c.get('name'),T[l.get('name')]@tf(c),np.fromstring(c.find('geometry/box').get('size'),sep=' ')/2))
def overlap(A,a,B,b):
 axes=[*A[:3,:3].T,*B[:3,:3].T]
 axes += [np.cross(x,y) for x in A[:3,:3].T for y in B[:3,:3].T]
 d=B[:3,3]-A[:3,3]
 for x in axes:
  norm=np.linalg.norm(x)
  if norm<1e-9:continue
  x=x/norm
  if abs(d@x) >= np.sum(abs(A[:3,:3].T@x)*a)+np.sum(abs(B[:3,:3].T@x)*b)-1e-6:return False
 return True
hits=[]
for a,b in combinations(boxes,2):
 if a[0]==b[0] or frozenset([a[0],b[0]]) in adj:continue
 if overlap(a[2],a[3],b[2],b[3]):hits.append((a[0],a[1],b[0],b[1]))
out=['NEUTRAL-POSE COLLISION BOX CHECK','Adjacent and same-link boxes excluded.','Nonadjacent overlaps: '+str(len(hits))]
out += [' | '.join(h) for h in hits]
out += ['No swept collision or exact mesh collision test was performed.','Conservative box overlap can be a false positive. Do not treat this check as mechanical clearance certification.']
(P/'docs/COLLISION_CHECK.txt').write_text('\n'.join(out)+'\n');print('\n'.join(out))
