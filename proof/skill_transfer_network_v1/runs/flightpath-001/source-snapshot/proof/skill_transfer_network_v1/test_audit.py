"""Mutation tests for separate-host and causal disconnection evidence."""
import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('network_audit',Path(__file__).with_name('audit.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class AuditTests(unittest.TestCase):
 def setUp(self):
  self.hosts={role:{'node_uid':role,'system_uuid':role,'observed':{'cpu_vendor':'GenuineIntel','os_release':'ID="rhel"'},'node_info':{'osImage':'Red Hat Enterprise Linux CoreOS'}} for role in ['central','edge']}
  self.scenario={'disconnection_before':{'task_status':'RUNNING','ticks':5},'disconnection_after':{'task_status':'RUNNING','ticks':25},'isolated_completion':{'job_state':'COMPLETE','task_status':'COMPLETE','ticks':200}}
 def test_distinct_hardware_passes(self):a.check_hosts(self.hosts)
 def test_same_node_or_system_uuid_rejects(self):
  for field in ['node_uid','system_uuid']:
   h=copy.deepcopy(self.hosts);h['edge'][field]=h['central'][field]
   with self.assertRaises(ValueError):a.check_hosts(h)
 def test_non_intel_or_non_redhat_rejects(self):
  for field,value in [('cpu_vendor','unknown'),('os_release','ID=other')]:
   h=copy.deepcopy(self.hosts);h['edge']['observed'][field]=value
   with self.assertRaises(ValueError):a.check_hosts(h)
 def test_control_continues_then_completes(self):a.check_disconnect_progress(self.scenario)
 def test_completed_before_partition_rejects(self):
  self.scenario['disconnection_after']['task_status']='COMPLETE'
  with self.assertRaises(ValueError):a.check_disconnect_progress(self.scenario)
 def test_no_post_partition_control_rejects(self):
  self.scenario['disconnection_after']['ticks']=5
  with self.assertRaises(ValueError):a.check_disconnect_progress(self.scenario)
if __name__=='__main__':unittest.main()
