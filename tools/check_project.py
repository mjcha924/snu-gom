"""Dependency-free checks for the current biped model and purchasing budget."""
from pathlib import Path
import csv
import json
import math
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_CEILING
from generate_robot import ROOT, OUTPUT, build, load_config


def read_bom(path):
    with Path(path).open(newline='') as f:
        rows = list(csv.DictReader(f))
    seen = set()
    for row in rows:
        ident = int(row['번호'])
        if ident in seen:
            raise ValueError('Duplicate BOM row ID')
        seen.add(ident)
        q, unit, amount = [Decimal(row[k]) for k in ('수량','단가_원','금액_원')]
        if not all(v.is_finite() and v >= 0 for v in (q,unit,amount)) or q*unit != amount:
            raise ValueError(f'BOM arithmetic mismatch at {path}, row {ident}')
        if not row['구매_URL'].startswith('https://'):
            raise ValueError(f'Missing purchase URL at row {ident}')
    return rows


def budget_totals():
    folder = ROOT/'hardware/bom'
    body, bench = read_bom(folder/'body.csv'), read_bom(folder/'bench.csv')
    cfg = json.loads((folder/'budget.json').read_text())
    requested = cfg['bench_purchase_ids']
    if len(set(requested)) != len(requested) or not set(requested) <= {int(r['번호']) for r in bench}:
        raise ValueError('Invalid requested bench item IDs')
    value = lambda row: int(Decimal(row['금액_원']))
    mandatory = sum(value(r) for r in body if r['구분']=='필수')
    base = mandatory + sum(value(r) for r in bench if int(r['번호']) in requested)
    unit = Decimal(cfg['round_up_krw'])
    contingency = int((Decimal(base)*Decimal(str(cfg['contingency_rate']))/unit).to_integral_value(rounding=ROUND_CEILING)*unit)
    optional = sum(value(r) for r in body+bench if r['구분']=='선택')
    borrowed = sum(value(r) for r in bench if r['구분']=='필수' and int(r['번호']) not in requested)
    return dict(base=base,shipping=cfg['shipping_krw'],contingency=contingency,
                total=base+cfg['shipping_krw']+contingency,optional=optional,borrowed=borrowed)


def check_model():
    cfg = load_config()
    if OUTPUT.read_text() != build(cfg):
        raise ValueError('URDF is stale; run python tools/generate_robot.py')
    xml = ET.parse(OUTPUT).getroot()
    links = {e.get('name'): e for e in xml.findall('link')}
    if len(links) != len(xml.findall('link')):
        raise ValueError('Duplicate link names')
    children = set()
    for j in xml.findall('joint'):
        parent, child = j.find('parent').get('link'),j.find('child').get('link')
        if parent not in links or child not in links or child in children:
            raise ValueError('Invalid model topology')
        children.add(child)
    if set(links)-children != {'base_link'}:
        raise ValueError('Expected one base_link root')
    mass = 0
    for link in links.values():
        m = float(link.find('inertial/mass').get('value'))
        inertia = link.find('inertial/inertia')
        vals = [float(inertia.get(k)) for k in ('ixx','iyy','izz')]
        if not all(math.isfinite(v) and v > 0 for v in [m]+vals):
            raise ValueError('Invalid mass/inertia')
        if any(vals[i] > sum(vals)-vals[i]+1e-12 for i in range(3)):
            raise ValueError('Unphysical diagonal inertia')
        mass += m
    return len(cfg['joints']), mass


def main():
    count, mass = check_model()
    totals = budget_totals()
    summary = (ROOT/'hardware/bom/README.md').read_text()
    for amount in totals.values():
        if f'{amount:,}원' not in summary:
            raise ValueError(f'Update BOM summary for {amount:,} KRW')
    print(f'PASS: {count} biped joints; proxy mass {mass:.3f} kg')
    print(json.dumps(totals, ensure_ascii=False))
    print('Model contract and budget checks only; no hardware or walking validation.')


if __name__ == '__main__':
    main()
