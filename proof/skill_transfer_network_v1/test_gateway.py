"""Rejection and durable-inbox tests; actual execution is a separate lab gate."""
import importlib.util,json,sqlite3,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('edge_gateway',Path(__file__).with_name('gateway.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class GatewayTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.inbox=g.Inbox(self.root/'inbox.sqlite','edge-a','f'*64)
  self.request={'schema':'evy-aeris.transfer-action.v1','action_id':'proof-1','skill_id':'inspection-positioning','release_digest':'a'*64}
 def tearDown(self):self.temp.cleanup()
 def test_duplicate_json_and_authority_fields_rejected(self):
  for raw in [b'{"action_id":"a","action_id":"b"}',json.dumps({**self.request,'command':'sh'}).encode()]:
   with self.assertRaises(ValueError):g.parse(raw)
 def test_binding_survives_restart_and_rejects_changed_request(self):
  self.inbox.submit(self.request)
  again=g.Inbox(self.root/'inbox.sqlite','edge-a','f'*64)
  self.assertEqual(again.submit(self.request)['state'],'QUEUED')
  with self.assertRaises(ValueError):again.submit({**self.request,'release_digest':'b'*64})
 def test_running_is_interrupted_on_restart_not_replayed(self):
  self.inbox.submit(self.request);self.inbox.claim()
  again=g.Inbox(self.root/'inbox.sqlite','edge-a','f'*64)
  self.assertEqual(again.get('proof-1')['state'],'INTERRUPTED');self.assertIsNone(again.claim())
 def test_same_database_cannot_change_local_authority(self):
  with self.assertRaises(ValueError):g.Inbox(self.root/'inbox.sqlite','edge-a','e'*64)
 def test_terminal_retry_cannot_requeue(self):
  self.inbox.submit(self.request);self.inbox.claim();self.inbox.finish('proof-1','FAILED',{'status':'REJECTED'})
  self.assertEqual(self.inbox.submit(self.request)['state'],'FAILED');self.assertIsNone(self.inbox.claim())
if __name__=='__main__':unittest.main()
