"""Mutate copies of real retained proof evidence; never modify the original."""
import importlib.util,json,os,shutil,sqlite3,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('saved_network_audit',Path(__file__).with_name('audit.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
@unittest.skipUnless(os.getenv('AERIS_NETWORK_PROOF_DIR'),'requires saved separate-host evidence')
class SavedAuditTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'run';shutil.copytree(Path(os.environ['AERIS_NETWORK_PROOF_DIR']),self.root)
 def tearDown(self):self.temp.cleanup()
 def change(self,name,mutate):
  p=self.root/name;v=json.loads(p.read_bytes());mutate(v);p.write_text(json.dumps(v))
 def test_original_passes(self):self.assertEqual(a.audit(self.root)['status'],'PASS_SEPARATE_HOST_SIMULATION')
 def test_same_host_rejected(self):
  self.change('hosts.json',lambda v:v['edge'].update(system_uuid=v['central']['system_uuid']))
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_fake_completion_rejected(self):
  with sqlite3.connect(self.root/'edge/evidence/rust.snapshot') as db:
   row=db.execute("SELECT payload FROM samples WHERE task='action-rework-recovered' ORDER BY tick DESC LIMIT 1").fetchone();sample=json.loads(row[0]);sample['after']['q'][0]+=.1
   db.execute('UPDATE samples SET payload=? WHERE task=? AND tick=?',(json.dumps(sample),sample['task'],sample['tick']))
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_receipt_version_change_rejected(self):
  with sqlite3.connect(self.root/'edge/evidence/rust.snapshot') as db:
   db.execute("UPDATE tasks SET release_digest=? WHERE id='action-inspection-disconnected'",('0'*64,))
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_no_post_partition_progress_rejected(self):
  self.change('scenario.json',lambda v:v['disconnection_after'].update(ticks=v['disconnection_before']['ticks']))
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_missing_network_refusal_rejected(self):
  operations=json.loads((self.root/'operations.json').read_bytes());op=next(o for o in operations if o['label']=='central-to-edge-blocked')
  self.change(op['stdout'],lambda v:v.update(status=200))
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_source_tampering_rejected(self):
  p=self.root/'source-snapshot/proof/skill_transfer_network_v1/gateway.py';p.write_bytes(p.read_bytes()+b'\n# altered\n')
  with self.assertRaises(ValueError):a.audit(self.root)
if __name__=='__main__':unittest.main()
