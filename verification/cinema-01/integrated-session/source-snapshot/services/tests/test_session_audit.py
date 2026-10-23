"""Reject semantic mutations even if a corrupt artifact is re-hashed."""
import importlib.util,json,os,shutil,sqlite3,tempfile,unittest,hashlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('independent_session_audit',Path(__file__).parents[2]/'scripts/audit_action_session.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
@unittest.skipUnless(os.getenv('AERIS_SESSION_EVIDENCE_DIR'),'requires a real captured browser session')
class SessionAudit(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'session';shutil.copytree(Path(os.environ['AERIS_SESSION_EVIDENCE_DIR']),self.root)
 def tearDown(self):self.tmp.cleanup()
 def rehash(self,name):
  p=self.root/'file-identities.json';v=json.loads(p.read_bytes());v[name]=hashlib.sha256((self.root/name).read_bytes()).hexdigest();p.write_text(json.dumps(v))
 def test_real_capture_passes(self):self.assertEqual(a.audit(self.root)['status'],'PASS_LOCAL_SIMULATION_ACCOUNTING')
 def test_forged_physics_sample_rejected(self):
  with sqlite3.connect(self.root/'rust.snapshot') as db:
   task,tick,raw=db.execute('SELECT task,tick,payload FROM samples ORDER BY task,tick LIMIT 1').fetchone();v=json.loads(raw);v['after']['q'][0]+=.1;db.execute('UPDATE samples SET payload=? WHERE task=? AND tick=?',(json.dumps(v),task,tick))
  self.rehash('rust.snapshot')
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_cut_without_continued_local_completion_rejected(self):
  p=self.root/'journal.json';v=json.loads(p.read_bytes())
  for event in v:
   if event['event']=='OBSERVED' and event['payload']['central']=='UNREACHABLE':event['payload']['phase']='UNKNOWN'
  p.write_text(json.dumps(v));self.rehash('journal.json')
  with self.assertRaises(ValueError):a.audit(self.root)
 def test_lost_recovery_evidence_rejected(self):
  p=self.root/'journal.json';v=json.loads(p.read_bytes())
  for event in v:
   if event['event']=='RECOVER':event['payload']['result']['interrupted_tasks']=0
  p.write_text(json.dumps(v));self.rehash('journal.json')
  with self.assertRaises(ValueError):a.audit(self.root)
if __name__=='__main__':unittest.main()
