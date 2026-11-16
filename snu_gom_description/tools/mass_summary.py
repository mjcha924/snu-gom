#!/usr/bin/env python3
"""Human-readable budget from current CSV values. Bounds are scenarios, not CIs."""
from pathlib import Path
import csv,collections,xml.etree.ElementTree as E
import numpy as np
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1]
def read(n):
 with (P/n).open() as f:return list(csv.DictReader(f))
rs=read('config/component_masses.csv');ps=[p for p in read('config/additional_masses.csv') if p['enabled']=='1']
groups=collections.defaultdict(lambda:np.zeros(3))
def add(cat,r):groups[cat]+=np.array([float(r['low_mass_kg']),float(r['mass_kg']),float(r['high_mass_kg'])])*1000
for r in rs:
 cat={'printed_part':'Existing printed CAD parts','leg_motor':'12 modeled motors (4 XC + 8 XL)','neck_motor_component':'12 modeled motors (4 XC + 8 XL)','bearing':'Bearings','electronics':'Existing electronics boards'}[r['kind']];add(cat,r)
for r in ps:
 cat={'camera':'Camera + mount + FFC','bearings':'Bearings','battery':'Battery','electronics':'Speaker + mount + cooling + microSD','power':'Regulators + distribution + protection','unmodeled_shell':'Unmodeled torso/paw shell allowances','wiring':'Wiring/connectors','fasteners':'External screws/inserts','mounts':'Battery tray/strap','optional_motors':'Optional extra motors'}.get(r['category'],r['category']);add(cat,r)
tot=sum(groups.values()); lines=['SNU GOM MASS BUDGET / 질량 예산','Units: grams. Unmeasured estimates; low/high are chosen planning scenarios, not statistical confidence limits.','',f'{"Category":48s} {"Low":>9s} {"Nominal":>9s} {"High":>9s}']
for c,v in groups.items():lines.append(f'{c:48s} {v[0]:9.1f} {v[1]:9.1f} {v[2]:9.1f}')
lines+=['-'*80,f'{"TOTAL":48s} {tot[0]:9.1f} {tot[1]:9.1f} {tot[2]:9.1f}','',f'Current skeleton (12 motors), 108g battery: {tot[1]/1000:.3f} kg',f'Current skeleton, 44g battery option: {(tot[1]-64)/1000:.3f} kg',f'14-motor plan, +2 XL motor masses only: {(tot[1]+36)/1000:.3f} kg',f'16-motor plan, +4 XL motor masses only: {(tot[1]+72)/1000:.3f} kg','The 14/16-motor numbers exclude the extra mechanisms/brackets and do not create extra motion DOFs.','Optional motors remain disabled in the delivered URDF.']
root=E.parse(P/'urdf/snu_gom_preview_relative.urdf').getroot();ts={'base_reference':np.eye(4)};pending=root.findall('joint')
def tf(e):
 o=e.find('origin');T=np.eye(4)
 if o is not None:
  T[:3,3]=np.fromstring(o.get('xyz','0 0 0'),sep=' ');T[:3,:3]=Rotation.from_euler('xyz',np.fromstring(o.get('rpy','0 0 0'),sep=' ')).as_matrix()
 return T
while pending:
 remain=[]
 for j in pending:
  a=j.find('parent').get('link');b=j.find('child').get('link')
  if a in ts:ts[b]=ts[a]@tf(j)
  else:remain.append(j)
 assert len(remain)<len(pending);pending=remain
mass=0.;weighted=np.zeros(3)
for l in root.findall('link'):
 ie=l.find('inertial')
 if ie is None:continue
 m=float(ie.find('mass').get('value'));mass+=m;weighted+=m*(ts[l.get('name')]@tf(ie))[:3,3]
assert abs(mass*1000-tot[1])<1e-6
lines+=['',f'Neutral-pose estimated whole-robot CoM in pelvis frame (mm): {weighted/mass*1000}','CoM depends on assumed payload locations; not a balance validation.','Mass allowances are combined into existing rigid bodies, with finite box inertias and the parallel-axis theorem.','Catalog full-board masses replace bare-PCB masses; no separate duplicate populated-board allowance.','Added payloads have no visual/collision mesh and do not prove packaging clearance.']
(P/'docs/MASS_BUDGET.txt').write_text('\n'.join(lines)+'\n')
with (P/'docs/mass_budget_summary.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['category','low_g','nominal_g','high_g'])
 for k,v in groups.items():w.writerow([k,*v])
 w.writerow(['TOTAL',*tot])
print('\n'.join(lines))
