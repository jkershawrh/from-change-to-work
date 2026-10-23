import importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('lab_contracts',Path(__file__).parents[1]/'action_console/contracts.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class Contracts(unittest.TestCase):
 def test_unknown_fields_and_physical_scope_rejected(self):
  valid={'schema':'aeris.lab-command.v1','command_id':'test-1','action_id':'job-1'}
  self.assertEqual(c.control(json.dumps(valid).encode())['action_id'],'job-1')
  for extra in [{'command':'sh'},{'url':'https://elsewhere'},{'physical_motion_authorized':True}]:
   with self.assertRaises(ValueError):c.control(json.dumps({**valid,**extra}).encode())
 def test_duplicate_fields_rejected(self):
  with self.assertRaises(ValueError):c.decode(b'{"a":1,"a":2}')
 def test_safe_same_origin_required(self):
  for origin,header in [('https://evil.example','v1'),('null','v1'),('http://localhost:8090','')]:
   with self.assertRaises(ValueError):c.same_origin(origin,header,['http://localhost:8090'])
  c.same_origin('http://localhost:8090','v1',['http://localhost:8090'])
 def test_physical_target_cannot_enable_fault_controls(self):
  for cfg in [{'simulation_only':False,'profile':'mujoco-six-axis-goals-v1','lab_controls':True},{'simulation_only':True,'profile':'vendor-arm','lab_controls':True}]:
   with self.assertRaises(ValueError):c.lab_authority(cfg)
if __name__=='__main__':unittest.main()
