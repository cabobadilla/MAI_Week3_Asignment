import os,sys,uuid,json,hashlib
from pathlib import Path
import pytest
@pytest.fixture
def ctx(tmp_path):
 root=Path(os.environ['GWA_DEMO_GENERATION_CANDIDATE']);sys.path.insert(0,str(root))
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):sys.modules.pop(k,None)
 from app import storage,campaigns,versions,runs,demo_generation
 p=tmp_path/'demo.sqlite';storage.initialize(p,Path(os.environ['GWA_SCHEMA_FILE']),organizations=True);conn=storage.connect(p);cam=campaigns.create_campaign(conn,'Prueba sintética','Formación','Presentar propósito',academic_suite=True)
 yield conn,cam,campaigns,versions,runs,demo_generation,p
 conn.close();sys.path.remove(str(root))
def test_suite_six_pieces_four_formats_and_simulated(ctx):
 c,cam,ca,v,r,m,p=ctx;x=m.generate_demo(c,cam['id']);assert x['mode']=='demo' and x['generation']=='simulated';assert x['run']['status']=='needs_review';assert len(x['versions'])==6;assert {i['format'] for i in x['versions']}=={'linkedin','email','article','ad'};assert len({i['variant'] for i in x['versions'] if i['format']=='ad'})==3
 assert all('DEMO' in i['body'] and i['run_id']==x['run']['id'] for i in x['versions'])
def test_never_autoapprove_export_or_distribute(ctx):
 c,cam,ca,v,r,m,p=ctx;x=m.generate_demo(c,cam['id'])
 for t in ['approval','export_record','distribution_record']:assert c.execute('SELECT count(*) FROM '+t).fetchone()[0]==0
 assert x['run']['metrics']['attempts']==0
def test_sources_and_history_are_explicitly_synthetic_and_untrusted(ctx):
 c,cam,ca,v,r,m,p=ctx;x=m.generate_demo(c,cam['id']);assert x['run']['sources'][0]['source_id']=='demo-fixture';assert x['run']['context']['untrusted'] is True;assert len(x['source_hash'])==len(x['context_hash'])==64;assert any('LLM' in y for y in x['warnings'])
def test_request_retry_idempotent_same_run(ctx):
 c,cam,ca,v,r,m,p=ctx;id=str(uuid.uuid4());a=m.generate_demo(c,cam['id'],run_id=id);b=m.generate_demo(c,cam['id'],run_id=id);assert {x['id'] for x in a['versions']}=={x['id'] for x in b['versions']};assert len(v.list_versions(c,cam['id']))==6
 assert a['source_hash']==b['source_hash'] and a['context_hash']==b['context_hash']
def test_run_cannot_move_campaign(ctx):
 c,cam,ca,v,r,m,p=ctx;id=str(uuid.uuid4());m.generate_demo(c,cam['id'],run_id=id);other=ca.create_campaign(c,'Otra','Tema','Objetivo')
 with pytest.raises(ValueError):m.generate_demo(c,other['id'],run_id=id)
 assert v.list_versions(c,other['id'])==[]
def test_history_current_campaign_before_generation(ctx):
 c,cam,ca,v,r,m,p=ctx;v.create_version(c,cam['id'],'email','Texto histórico sintético',origin='manual_external');x=m.generate_demo(c,cam['id']);history=x['run']['context']['previous_pieces'];assert any(i['body']=='Texto histórico sintético' for i in history);assert len(history)==1;assert len(x['warnings'])>=2
 other=ca.create_campaign(c,'Otra','Tema','Objetivo');y=m.generate_demo(c,other['id']);assert y['run']['context']['previous_pieces']==[]
def test_only_selected_format(ctx):
 c,cam,ca,v,r,m,p=ctx;one=ca.create_campaign(c,'Solo email','Tema','Objetivo',formats=['email']);x=m.generate_demo(c,one['id']);assert len(x['versions'])==1 and x['versions'][0]['format']=='email'
def test_stale_prepared_run_does_not_generate(ctx):
 c,cam,ca,v,r,m,p=ctx;x=r.create_run(c,cam['id']);ca.update_campaign(c,cam['id'],objective='Cambio')
 with pytest.raises(ValueError):m.generate_demo(c,cam['id'],run_id=x['id'])
 assert v.list_versions(c,cam['id'])==[]
def test_atomic_versions_on_failure(ctx,monkeypatch):
 c,cam,ca,v,r,m,p=ctx;original=v.create_version;calls=[]
 def fail(*a,**kw):
  calls.append(1)
  if len(calls)==3:raise ValueError('synthetic failure')
  return original(*a,**kw)
 monkeypatch.setattr(v,'create_version',fail)
 # The service contract uses the module function so the fault represents DB/write failure.
 if hasattr(m,'create_version'):monkeypatch.setattr(m,'create_version',fail)
 with pytest.raises(ValueError):m.generate_demo(c,cam['id'])
 assert v.list_versions(c,cam['id'])==[]
def test_restart_preserves_review_and_versions(ctx):
 c,cam,ca,v,r,m,p=ctx;x=m.generate_demo(c,cam['id']);from app.storage import connect
 d=connect(p)
 try:assert r.get_run(d,x['run']['id'])['status']=='needs_review';assert len(v.list_versions(d,cam['id']))==6
 finally:d.close()

def test_read_bundle_is_pure_and_survives_newer_run(ctx):
 c,cam,ca,v,r,m,p=ctx;a=m.generate_demo(c,cam['id']);b=m.generate_demo(c,cam['id']);got=m.get_demo_bundle(c,a['run']['id']);assert {x['id'] for x in got['versions']}=={x['id'] for x in a['versions']};assert len(v.list_versions(c,cam['id']))==12
 with pytest.raises(ValueError):m.get_demo_bundle(c,'missing')

def test_outer_transaction_is_not_committed(ctx):
 c,cam,ca,v,r,m,p=ctx;c.execute('BEGIN');m.generate_demo(c,cam['id']);assert c.in_transaction;c.rollback();assert r.list_runs(c,cam['id'])==[] and v.list_versions(c,cam['id'])==[]

def test_history_count_database_failure_is_not_empty_context(ctx):
 c,cam,ca,v,r,m,p=ctx
 import sqlite3
 def authorize(action,table,column,*rest):
  if action==sqlite3.SQLITE_READ and table=='distribution_record':return sqlite3.SQLITE_DENY
  return sqlite3.SQLITE_OK
 c.set_authorizer(authorize)
 try:
  with pytest.raises(ValueError):m.generate_demo(c,cam['id'])
 finally:c.set_authorizer(None)
 assert v.list_versions(c,cam['id'])==[]
 assert all(x['status']=='failed' for x in r.list_runs(c,cam['id']))

def test_history_count_uses_actual_distribution_record_table(ctx):
 c,cam,ca,v,r,m,p=ctx
 from app.distribution import record_publication
 a=m.generate_demo(c,cam['id']);li=next(x for x in a['versions'] if x['format']=='linkedin');record_publication(c,cam['id'],li['id'],'linkedin','2026-10-25T12:00:00+00:00',str(uuid.uuid4()),confirmed=True)
 b=m.generate_demo(c,cam['id']);assert b['run']['context']['manual_distribution_count']==1
