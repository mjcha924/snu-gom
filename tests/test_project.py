"""Cross-file regression checks and intentional invalid-input cases."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from generate_robot import load_config, validate_config, build, OUTPUT
from check_project import budget_totals, check_model, read_bom


class ProjectTests(unittest.TestCase):
    def test_generated_model_matches_contract(self):
        count,mass = check_model()
        self.assertEqual(count,10)
        self.assertAlmostEqual(mass,.6)
        xml=ET.parse(OUTPUT).getroot()
        movable={j.get('name') for j in xml.findall('joint') if j.get('type')=='revolute'}
        self.assertEqual(movable,{j['name'] for j in load_config()['joints']})

    def test_duplicate_motor_id_rejected(self):
        cfg=load_config();cfg['joints'][1]['logical_motor_id']=1
        with self.assertRaises(ValueError):validate_config(cfg)

    def test_swapped_order_rejected(self):
        cfg=load_config();cfg['joints'][0],cfg['joints'][1]=cfg['joints'][1],cfg['joints'][0]
        with self.assertRaises(ValueError):validate_config(cfg)

    def test_wrong_axis_rejected(self):
        cfg=load_config();cfg['joints'][0]['axis']=[0,0,1]
        with self.assertRaises(ValueError):validate_config(cfg)

    def test_invalid_limit_rejected(self):
        cfg=load_config();cfg['joints'][0]['upper_rad']=float('nan')
        with self.assertRaises(ValueError):validate_config(cfg)

    def test_dimension_change_changes_model(self):
        cfg=load_config();original=build(cfg);cfg['dimensions_m']['thigh']=.06
        self.assertNotEqual(build(cfg),original)

    def test_budget_excludes_optional_and_borrowed(self):
        totals=budget_totals()
        self.assertEqual(totals['total'],totals['base']+totals['shipping']+totals['contingency'])
        self.assertGreater(totals['optional'],0)
        self.assertGreater(totals['borrowed'],0)

    def test_stale_bom_amount_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'wrong.csv'
            path.write_text('번호,수량,단가_원,금액_원,구매_URL\n1,10,26400,26400,https://example.com\n')
            with self.assertRaises(ValueError):read_bom(path)


if __name__ == '__main__':
    unittest.main()
