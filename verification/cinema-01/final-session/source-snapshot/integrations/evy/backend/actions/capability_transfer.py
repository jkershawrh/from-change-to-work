"""Durable EVY dispatch binding to a preconfigured local robot gateway.

This adapter never approves/signs a release, accepts executable paths from a
caller, or turns generated text into actuator commands. Rust retains activation
and task authority at the edge. Terminal receipts remain explicitly scoped.
"""
from __future__ import annotations
import hashlib
from contextlib import contextmanager
import hmac
import json
import os
from pathlib import Path
import re
import sqlite3
import ssl
from urllib.parse import urlsplit
import httpx

MAX_REQUEST=4096
MAX_RESPONSE=65536
ID=re.compile(r'[A-Za-z0-9_.-]{1,80}\Z')
DIGEST=re.compile(r'[a-f0-9]{64}\Z')


class ActionError(ValueError):
    def __init__(self,code,status=422):super().__init__(code);self.code=code;self.status=status


def require(value,code,status=422):
    if not value:raise ActionError(code,status)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def unique_pairs(pairs):
    result={}
    for k,v in pairs:
        require(k not in result,'DUPLICATE_FIELD')
        result[k]=v
    return result


def decode(raw,limit):
    require(len(raw)<=limit,'BODY_LIMIT',413)
    try:return json.loads(raw,object_pairs_hook=unique_pairs,parse_constant=lambda _:(_ for _ in ()).throw(ActionError('NONFINITE')))
    except (UnicodeError,json.JSONDecodeError):raise ActionError('JSON_REQUIRED') from None


def parse_intent(raw):
    value=decode(raw,MAX_REQUEST)
    require(type(value)is dict and set(value)=={'schema','action_id','edge_id','skill_id','release_digest'},'ACTION_FIELDS')
    require(value['schema']=='evy.capability-action.v1','ACTION_SCHEMA')
    require(all(type(value[k])is str and ID.fullmatch(value[k]) for k in ('action_id','edge_id','skill_id')),'ACTION_IDENTITY')
    require(type(value['release_digest'])is str and DIGEST.fullmatch(value['release_digest']),'RELEASE_DIGEST')
    return value


def local_bytes(path,limit=32768):
    p=Path(path);require(p.is_absolute() and p.is_file(),'LOCAL_CONFIG_PATH',503)
    with p.open('rb') as f:data=f.read(limit+1)
    require(len(data)<=limit,'LOCAL_CONFIG_BOUND',503)
    return data


def rust_request(request):
    return {'schema':'evy-aeris.transfer-action.v1',**{k:request[k] for k in ('action_id','skill_id','release_digest')}}


class ActionDispatcher:
    def __init__(self,config,*,transport=None):
        require(type(config)is dict and set(config)=={'schema','database','operator_token_file','viewer_token_file','targets'},'CONFIG_FIELDS',503)
        require(config['schema']=='evy.capability-actions.config.v1','CONFIG_SCHEMA',503)
        require(Path(config['database']).is_absolute(),'LOCAL_DATABASE',503)
        require(type(config['targets'])is list and 1<=len(config['targets'])<=32,'TARGETS',503)
        self.config=config;self.targets={};self.transport=transport
        for target in config['targets']:
            require(type(target)is dict and set(target)=={'id','base_url','ca_file','token_file','profile','allowed_skills','simulation_only'},'TARGET_FIELDS',503)
            require(type(target['id'])is str and ID.fullmatch(target['id']) and target['id'] not in self.targets,'TARGET_ID',503)
            url=urlsplit(target['base_url'])
            require(url.scheme=='https' and url.hostname and not url.username and not url.password and not url.query and not url.fragment and url.path in ('','/'),'TLS_TARGET_REQUIRED',503)
            require(target['profile']=='mujoco-six-axis-goals-v1' and target['simulation_only']is True,'UNQUALIFIED_PROFILE',503)
            require(type(target['allowed_skills'])is list and 1<=len(target['allowed_skills'])<=32 and all(type(s)is str and ID.fullmatch(s) for s in target['allowed_skills']),'SKILL_ALLOWLIST',503)
            self.targets[target['id']]=target
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, request TEXT NOT NULL,target_sha TEXT NOT NULL,observed TEXT)')

    @classmethod
    def from_environment(cls):
        path=os.environ.get('EVY_ACTION_CONFIG','')
        require(bool(path),'ACTIONS_DISABLED',503)
        return cls(decode(local_bytes(path),32768))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.config['database'],timeout=2)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def authorize(self,token,*,write):
        require(type(token)is str and len(token)<=256,'AUTH_REQUIRED',401)
        choices=['operator_token_file'] if write else ['operator_token_file','viewer_token_file']
        valid=False
        for field in choices:
            expected=local_bytes(self.config[field],256).decode().strip()
            require(len(expected)>=32,'AUTH_CONFIG',503)
            valid |= hmac.compare_digest(token,expected)
        require(valid,'AUTH_REQUIRED',403)

    def target(self,request):
        target=self.targets.get(request['edge_id']);require(target is not None,'UNKNOWN_EDGE')
        require(request['skill_id']in target['allowed_skills'],'SKILL_NOT_ENABLED')
        return target

    def bind(self,request):
        # Parsing here also protects callers using the Python API instead of HTTP.
        request=parse_intent(canonical(request).encode())
        target=self.target(request)
        target_sha=hashlib.sha256(canonical(target).encode()).hexdigest()
        encoded=canonical(request)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO actions VALUES(?,?,?,NULL)',(request['action_id'],encoded,target_sha))
            saved=db.execute('SELECT request,target_sha FROM actions WHERE id=?',(request['action_id'],)).fetchone()
            require(saved==(encoded,target_sha),'ACTION_ID_OR_TARGET_CHANGED',409)
        return request,target

    def validate_remote(self,request,body):
        require(type(body)is dict and body.get('schema')=='evy-aeris.edge-action.v1','EDGE_CONTRACT',502)
        require(body.get('edge_id')==request['edge_id'] and body.get('action')==rust_request(request),'EDGE_BINDING',502)
        require(body.get('simulation_only')is True and body.get('physical_motion_authorized')is False,'UNQUALIFIED_AUTHORITY',502)
        require(body.get('state')in ('QUEUED','RUNNING','COMPLETE','FAILED','INTERRUPTED'),'EDGE_STATE',502)
        if body['state']=='COMPLETE':
            result=body.get('result')
            require(type(result)is dict and result.get('schema')=='evy-aeris.transfer-action-result.v1' and result.get('status')=='COMPLETE','TERMINAL_RECEIPT_REQUIRED',502)
            require(all(result.get(k)==request[k] for k in ('action_id','skill_id','release_digest')),'RESULT_BINDING',502)
            require(result.get('simulation_only')is True and result.get('physical_motion_authorized')is False,'RESULT_AUTHORITY',502)
            receipt=result.get('receipt',{})
            require(type(receipt)is dict,'EXECUTION_RECEIPT_REQUIRED',502)
            if receipt.get('idempotent')is True:
                receipt=receipt.get('result',{})
                require(type(receipt)is dict,'EXECUTION_RECEIPT_REQUIRED',502)
            require(receipt.get('schema')=='evy-aeris.sim-transfer-receipt.v2' and receipt.get('status')=='COMPLETE' and receipt.get('release_digest')==request['release_digest'],'EXECUTION_RECEIPT_REQUIRED',502)
        return body

    async def exchange(self,method,request,target):
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=target['ca_file'])
        token=local_bytes(target['token_file'],256).decode().strip()
        require(len(token)>=32,'EDGE_AUTH_CONFIG',503)
        path='/v1/actions' if method=='POST' else '/v1/actions/'+request['action_id']
        try:
            async with httpx.AsyncClient(verify=context,transport=self.transport,follow_redirects=False,trust_env=False,timeout=httpx.Timeout(5,connect=2)) as client:
                async with client.stream(method,target['base_url'].rstrip('/')+path,headers={'Authorization':'Bearer '+token},json=rust_request(request) if method=='POST' else None) as response:
                    require(response.status_code in (200,202),'EDGE_REFUSED',502)
                    data=bytearray()
                    async for block in response.aiter_bytes():
                        data.extend(block);require(len(data)<=MAX_RESPONSE,'EDGE_RESPONSE_BOUND',502)
            body=self.validate_remote(request,decode(bytes(data),MAX_RESPONSE))
        except (httpx.HTTPError,OSError,ssl.SSLError):raise ActionError('EDGE_UNAVAILABLE',502) from None
        with self.connect() as db:db.execute('UPDATE actions SET observed=? WHERE id=?',(canonical(body),request['action_id']))
        return {'schema':'evy.capability-action-result.v1','action_id':request['action_id'],'edge_id':request['edge_id'],'state':body['state'],'observation':body,'source':'EDGE_OBSERVED','simulation_only':True,'physical_motion_authorized':False}

    async def dispatch(self,request):
        request,target=self.bind(request)
        return await self.exchange('POST',request,target)

    async def status(self,action_id):
        require(type(action_id)is str and ID.fullmatch(action_id),'ACTION_IDENTITY')
        with self.connect() as db:row=db.execute('SELECT request FROM actions WHERE id=?',(action_id,)).fetchone()
        require(row is not None,'ACTION_NOT_FOUND',404)
        request,target=self.bind(json.loads(row[0]))
        return await self.exchange('GET',request,target)

    def catalog(self):
        return {'schema':'evy.action-catalog.v1','actions':[{'id':'capability-transfer','request_contract':'evy.capability-action.v1','edge_id':t['id'],'profile':t['profile'],'capabilities':t['allowed_skills'],'simulation_only':True,'physical_motion_authorized':False} for t in self.targets.values()]}
