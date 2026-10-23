"""Red-first: no promotion from tool readiness or operator intake to hardware proof."""
import json,tempfile,unittest
from pathlib import Path
from services.readiness import evaluate,write_report

class ReadinessContracts(unittest.TestCase):
 def snapshot(self):
  return {'host':{'system':'Linux','architecture':'x86_64','cpu_vendor':'GenuineIntel','cpu_model':'Intel sample','os_id':'rhel'},'source':{'commit':'a'*40,'dirty':False},'tools':{'python':'3.12.8','node':'v22.15.0','cargo':'cargo 1.90.0','lfs':'git-lfs/3.6.1'},'dependencies':{'status':'MATCH'},'artifacts':{'executor':'PRESENT','frontend':'PRESENT','plant_assets':'PRESENT'}}
 def test_ready_means_simulator_prerequisites_only(self):
  report=evaluate(self.snapshot(),1000)
  self.assertEqual(report['simulation_prerequisites'],'READY')
  self.assertFalse(report['physical_motion_authorized'])
  self.assertEqual(report['measurement_scope'],'CURRENT_PROCESS_HOST_ONLY')
  self.assertTrue(all(r['status']=='RED' for r in report['qualification']))
  self.assertEqual(report['alignment']['status'],'CANDIDATE_ONLY')
 def test_missing_old_or_unobserved_tools_block(self):
  for name,value in [('python','3.11.9'),('node','v22.11.0'),('cargo','cargo 1.89.0'),('lfs',None)]:
   with self.subTest(name=name):
    s=self.snapshot();s['tools'][name]=value;r=evaluate(s,1000)
    self.assertEqual(r['simulation_prerequisites'],'BLOCKED');self.assertTrue(any(c['status']=='RED' for c in r['checks']))
 def test_unpulled_assets_and_dependency_mismatch_block(self):
  for part in ['plant_assets','dependencies']:
   s=self.snapshot()
   if part=='dependencies':s[part]={'status':'MISMATCH'}
   else:s['artifacts'][part]='LFS_POINTER'
   self.assertEqual(evaluate(s,1000)['simulation_prerequisites'],'BLOCKED')
 def test_unknown_cpu_or_non_rhel_never_claims_alignment(self):
  for vendor,os_id in [(None,'rhel'),('GenuineIntel','darwin'),('AuthenticAMD','rhel')]:
   s=self.snapshot();s['host'].update(cpu_vendor=vendor,os_id=os_id)
   self.assertEqual(evaluate(s,1000)['alignment']['status'],'UNVERIFIED')
 def test_report_cannot_overwrite_previous_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'report.json';r=evaluate(self.snapshot(),1000);write_report(p,r)
   with self.assertRaises(FileExistsError):write_report(p,r)
   self.assertEqual(json.loads(p.read_text()),r)
