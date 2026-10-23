"""Bounded operator requests. No remote paths, destinations or executable input."""
import json,re
ID=re.compile(r'[A-Za-z0-9_.-]{1,80}\Z')
def need(value,message):
 if not value:raise ValueError(message)
def pairs(items):
 result={}
 for key,value in items:
  need(key not in result,'DUPLICATE_FIELD');result[key]=value
 return result
def decode(raw,limit=4096):
 need(len(raw)<=limit,'BODY_LIMIT')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'NONFINITE'))
def control(raw):
 value=decode(raw);need(type(value)is dict and set(value)=={'schema','command_id','action_id'},'CONTROL_FIELDS')
 need(value['schema']=='aeris.lab-command.v1','CONTROL_SCHEMA')
 need(all(type(value[k])is str and ID.fullmatch(value[k]) for k in ['command_id','action_id']),'CONTROL_IDENTITY');return value
def same_origin(origin,header,allowed):need(origin in allowed and header=='v1','SAME_ORIGIN_REQUIRED')
def lab_authority(config):need(config.get('simulation_only')is True and config.get('profile')=='mujoco-six-axis-goals-v1' and config.get('lab_controls')is True,'SIMULATOR_LAB_ONLY')
