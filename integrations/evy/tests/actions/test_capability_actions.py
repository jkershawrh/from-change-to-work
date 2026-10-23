import json
import sqlite3
from pathlib import Path
import httpx
import pytest
from backend.actions.capability_transfer import ActionDispatcher, ActionError, parse_intent


def intent(**updates):
    return dict(schema='evy.capability-action.v1',action_id='job-001',edge_id='cell-a',skill_id='inspection-positioning',release_digest='a'*64,**updates)


def test_request_rejects_remote_paths_urls_and_duplicate_authority():
    for extra in ({'config':'/tmp/override'},{'url':'https://evil.test'},{'command':'sh'}):
        with pytest.raises(ActionError):parse_intent(json.dumps({**intent(),**extra}).encode())
    with pytest.raises(ActionError):parse_intent(b'{"schema":"evy.capability-action.v1","action_id":"x","action_id":"y"}')


def test_config_requires_https_and_known_edge(tmp_path):
    config=configuration(tmp_path)
    config['targets'][0]['base_url']='http://untrusted.test'
    with pytest.raises(ActionError):ActionDispatcher(config)


def configuration(tmp_path):
    for name in ('operator','viewer','edge'):(tmp_path/name).write_text(name*16)
    return dict(schema='evy.capability-actions.config.v1',database=str(tmp_path/'actions.sqlite'),operator_token_file=str(tmp_path/'operator'),viewer_token_file=str(tmp_path/'viewer'),targets=[dict(id='cell-a',base_url='https://cell-a.test',ca_file=str(tmp_path/'ca.pem'),token_file=str(tmp_path/'edge'),profile='mujoco-six-axis-goals-v1',allowed_skills=['inspection-positioning','rework-positioning'],simulation_only=True)])


def test_read_credentials_cannot_submit_actions(tmp_path):
    dispatcher=ActionDispatcher(configuration(tmp_path))
    dispatcher.authorize('viewer'*16,write=False)
    with pytest.raises(ActionError):dispatcher.authorize('viewer'*16,write=True)
    dispatcher.authorize('operator'*16,write=True)


def test_same_id_is_bound_across_restart(tmp_path):
    cfg=configuration(tmp_path);dispatcher=ActionDispatcher(cfg);request=parse_intent(json.dumps(intent()).encode())
    dispatcher.bind(request)
    restarted=ActionDispatcher(cfg);restarted.bind(request)
    changed={**request,'release_digest':'b'*64}
    with pytest.raises(ActionError):restarted.bind(changed)


def test_unknown_or_unapproved_capability_never_binds(tmp_path):
    dispatcher=ActionDispatcher(configuration(tmp_path))
    for key,value in [('edge_id','unknown'),('skill_id','unapproved')]:
        with pytest.raises(ActionError):dispatcher.bind({**intent(),key:value})
    with sqlite3.connect(tmp_path/'actions.sqlite') as db:assert db.execute('select count(*) from actions').fetchone()[0]==0


def test_receipt_cannot_promote_another_version_or_physical_execution(tmp_path):
    dispatcher=ActionDispatcher(configuration(tmp_path));request=intent()
    response={'schema':'evy-aeris.edge-action.v1','edge_id':'cell-a','action':{k:v for k,v in request.items() if k!='edge_id'},'state':'COMPLETE','result':{},'simulation_only':True,'physical_motion_authorized':False}
    response['action']['schema']='evy-aeris.transfer-action.v1'
    with pytest.raises(ActionError):dispatcher.validate_remote(request,response)


def test_target_reroute_cannot_rebind_existing_job(tmp_path):
    cfg=configuration(tmp_path);request=intent();ActionDispatcher(cfg).bind(request)
    cfg['targets'][0]['base_url']='https://other-cell.test'
    with pytest.raises(ActionError):ActionDispatcher(cfg).bind(request)


def test_missing_local_auth_file_is_scoped_configuration_error(tmp_path):
    cfg=configuration(tmp_path)
    (tmp_path/'operator').unlink()
    dispatcher=ActionDispatcher(cfg)
    with pytest.raises(ActionError,match='LOCAL_CONFIG_PATH'):
        dispatcher.authorize('operator'*16,write=True)


def test_malformed_nested_receipt_is_rejected_without_crash(tmp_path):
    dispatcher=ActionDispatcher(configuration(tmp_path));request=intent()
    from backend.actions.capability_transfer import rust_request
    result=dict(schema='evy-aeris.transfer-action-result.v1',status='COMPLETE',action_id=request['action_id'],skill_id=request['skill_id'],release_digest=request['release_digest'],simulation_only=True,physical_motion_authorized=False)
    for receipt in [None,[],17,{'idempotent':True,'result':None}]:
        body=dict(schema='evy-aeris.edge-action.v1',edge_id='cell-a',action=rust_request(request),state='COMPLETE',result={**result,'receipt':receipt},simulation_only=True,physical_motion_authorized=False)
        with pytest.raises(ActionError):dispatcher.validate_remote(request,body)


def test_database_connection_closes_after_transaction(tmp_path):
    dispatcher=ActionDispatcher(configuration(tmp_path))
    with dispatcher.connect() as db:db.execute('SELECT 1')
    with pytest.raises(sqlite3.ProgrammingError):db.execute('SELECT 1')


def test_actual_evy_gateway_registers_disabled_action_routes(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.api_gateway.main import app
    monkeypatch.delenv('EVY_ACTION_CONFIG',raising=False)
    with TestClient(app) as client:
        response=client.get('/actions/catalog')
        assert response.status_code==503
        assert response.json()['detail']=='ACTIONS_DISABLED'
        assert client.post('/actions/capability-transfer',json=intent()).status_code==503


def test_actual_evy_gateway_enforces_operator_and_viewer(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from backend.api_gateway.main import app
    cfg=configuration(tmp_path);path=tmp_path/'local.json';path.write_text(json.dumps(cfg))
    monkeypatch.setenv('EVY_ACTION_CONFIG',str(path))
    with TestClient(app) as client:
        assert client.get('/actions/catalog').status_code==401
        headers={'Authorization':'Bearer '+'viewer'*16}
        response=client.get('/actions/catalog',headers=headers)
        assert response.status_code==200
        assert response.json()['actions'][0]['edge_id']=='cell-a'
        assert 'token_file' not in response.text
        assert client.post('/actions/capability-transfer',headers=headers,json=intent()).status_code==403
        headers={'Authorization':'Bearer '+'operator'*16}
        response=client.post('/actions/capability-transfer',headers=headers,json={**intent(),'edge_id':'not-enrolled'})
        assert response.status_code==422
        assert response.json()['detail']=='UNKNOWN_EDGE'
