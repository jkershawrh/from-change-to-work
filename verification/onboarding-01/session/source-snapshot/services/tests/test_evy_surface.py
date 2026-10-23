import sys,unittest
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).parents[2]/'integrations/evy'))
from services.evy_action_gateway import app
class EvySurface(unittest.TestCase):
 def test_handoff_exposes_only_existing_action_and_health_routes(self):
  with TestClient(app) as client:
   self.assertEqual(client.get('/health').status_code,200)
   self.assertEqual(client.get('/actions/catalog').status_code,503)
   self.assertEqual(client.get('/docs').status_code,404)
   self.assertEqual(client.post('/chat',json={'message':'do not dispatch'}).status_code,404)
if __name__=='__main__':unittest.main()
