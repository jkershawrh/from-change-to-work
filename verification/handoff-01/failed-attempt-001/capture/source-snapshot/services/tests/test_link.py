import unittest
from services.lab_link import Gate
class LinkTests(unittest.TestCase):
 def test_command_retry_does_not_reverse_a_newer_transition(self):
  gate=Gate();cut=gate.change('cut-1','disconnect');gate.change('restore-2','reconnect');self.assertEqual(gate.change('cut-1','disconnect'),cut);self.assertTrue(gate.connected)
 def test_same_id_cannot_change_operation(self):
  gate=Gate();gate.change('one','disconnect')
  with self.assertRaises(ValueError):gate.change('one','reconnect')
 def test_unknown_operation_rejects(self):
  with self.assertRaises(ValueError):Gate().change('one','shell')
if __name__=='__main__':unittest.main()
