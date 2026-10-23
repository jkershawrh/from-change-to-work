import asyncio,json,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from services.action_console.api import Console,create_app
class ConsoleAuth(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name);self.path=p/'config.json'
  for key in ['operator','viewer']:(p/key).write_text(key*16)
  self.cfg={'schema':'aeris.action-console.config.v1','simulation_only':True,'lab_controls':True,'profile':'mujoco-six-axis-goals-v1','database':str(p/'console.sqlite'),'evy_url':'https://localhost:1','edge_url':'https://localhost:2','publisher_url':'https://localhost:3','link_url':'https://localhost:4','allowed_origins':['http://localhost:8090'],'operator_code_file':str(p/'operator'),'viewer_code_file':str(p/'viewer')}
  self.path.write_text(json.dumps(self.cfg));self.client=TestClient(create_app(self.path));self.headers={'Origin':'http://localhost:8090','X-Aeris-Action':'v1'}
 def tearDown(self):self.client.close();self.tmp.cleanup()
 def test_login_requires_same_origin_and_never_returns_code(self):
  self.assertEqual(self.client.post('/api/action-demo/session',json={'code':'operator'*16}).status_code,403)
  r=self.client.post('/api/action-demo/session',headers=self.headers,json={'code':'operator'*16});self.assertEqual(r.status_code,200);self.assertEqual(r.json()['role'],'operator');self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertIn('SameSite=strict',r.headers['set-cookie']);self.assertNotIn('operator'*16,r.text)
 def test_viewer_cannot_transfer_or_cut_link(self):
  self.client.post('/api/action-demo/session',headers=self.headers,json={'code':'viewer'*16})
  for endpoint in ['/actions','/controls/disconnect','/controls/recover']:
   self.assertEqual(self.client.post('/api/action-demo'+endpoint,headers=self.headers,json={}).status_code,403)
 def test_unauthenticated_actions_fail(self):self.assertEqual(self.client.post('/api/action-demo/actions',headers=self.headers,json={}).status_code,401)
 def test_cross_origin_request_refused_even_with_session(self):
  self.client.post('/api/action-demo/session',headers=self.headers,json={'code':'operator'*16})
  self.assertEqual(self.client.post('/api/action-demo/actions',headers={**self.headers,'Origin':'https://other.example'},json={}).status_code,403)
 def test_changed_destination_cannot_reuse_database(self):
  Console(self.path);self.cfg['edge_url']='https://elsewhere.example';self.path.write_text(json.dumps(self.cfg))
  with self.assertRaises(ValueError):Console(self.path)
 def test_browser_cannot_supply_paths_or_release_authority(self):
  c=Console(self.path)
  for request in [{'action_id':'one','skill_id':'inspection-positioning','url':'https://evil.example'},{'action_id':'one','skill_id':'inspection-positioning','release_digest':'0'*64}]:
   with self.assertRaises(ValueError):asyncio.run(c.submit(request))
 def test_uncertain_control_ack_never_claims_recovery(self):
  c=Console(self.path)
  async def state():return {'action':{'action_id':'one'},'phase':'RECOVERY_REQUIRED','task':{'ticks':20}}
  async def call(*args):return {'status':'UNCERTAIN'}
  c.state=state;c.call=call
  with self.assertRaises(ValueError):asyncio.run(c.command('recover',{'schema':'aeris.lab-command.v1','command_id':'command-one','action_id':'one'}))
if __name__=='__main__':unittest.main()
