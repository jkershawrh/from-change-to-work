import json,unittest
from pathlib import Path
from unittest.mock import patch
from services.tests import test_console_auth
from services.readiness import evaluate

class ReadinessAPI(unittest.TestCase):
 setUp=test_console_auth.ConsoleAuth.setUp
 tearDown=test_console_auth.ConsoleAuth.tearDown
 def test_preflight_is_authenticated_read_only_and_cached(self):
  with patch('services.readiness.collect',return_value={'schema':'aeris.readiness-report.v1','measurement_scope':'CURRENT_PROCESS_HOST_ONLY','physical_motion_authorized':False}) as probe:
   self.assertEqual(self.client.get('/api/action-demo/readiness').status_code,401);probe.assert_not_called()
   self.client.post('/api/action-demo/session',headers=self.headers,json={'code':'viewer'*16})
   self.assertEqual(self.client.get('/api/action-demo/session').json()['role'],'viewer')
   self.assertEqual(self.client.get('/api/action-demo/readiness?command=install').status_code,422);probe.assert_not_called()
   for _ in range(2):
    response=self.client.get('/api/action-demo/readiness');self.assertEqual(response.status_code,200);self.assertEqual(response.headers['cache-control'],'no-store');self.assertFalse(response.json()['physical_motion_authorized'])
   self.assertEqual(probe.call_count,1)
 def test_manifest_source_map_resolves(self):
  root=Path(__file__).resolve().parents[2];m=json.loads((root/'onboarding/manifest.json').read_bytes())
  for item in m['read_order']+m['modules']:self.assertTrue((root/item['path']).exists(),item['path'])
