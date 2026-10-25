import os,sys,json,sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
@pytest.fixture
def db(tmp_path,monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_BUDGET_CANDIDATE'])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app import storage,campaigns,runs,run_budget
 from app.config import AppConfig
 p=tmp_path/'budget.sqlite';storage.initialize(p,Path(os.environ['GWA_SCHEMA_FILE']));c=storage.connect(p)
 cam=campaigns.create_campaign(c,'Synthetic','Training','Goal',formats=['email']);r=runs.create_run(c,cam['id']);runs.transition_run(c,r['id'],'running','generate')
 def cfg(**kw):
  d=dict(host='127.0.0.1',port=8501,llm_enabled=True,model='qwen/qwen3.8-flash',api_key='SYNTHETIC-KEY-NOT-REAL',api_base='https://openrouter.ai/api/v1',max_input_tokens=100,max_output_tokens=40,max_total_tokens_per_run=200,max_request_attempts_per_run=2,max_retries=2,timeout_seconds=30,budget_control='user_managed_api_key');d.update(kw);return AppConfig(**d)
 def reserve(rid='req-1',**kw):
  d=dict(stage='generator',input_tokens=30,max_output_tokens=40,config=cfg());d.update(kw);return run_budget.reserve_call(c,r['id'],rid,**d)
 yield c,cam,r,cfg,reserve,runs,run_budget,storage,p
 c.close()
def test_reserve_persists_and_freezes_sources(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;x=reserve();v=runs.get_run(c,r['id']);assert x['request_id']=='req-1' and x['reserved_tokens']==70 and x['status']=='reserved';assert v['metrics']['attempts']==1 and v['metrics']['llm_budget']['reserved_tokens']==70
 with pytest.raises(ValueError):runs.set_snapshots(c,r['id'],[],{'changed':True})
 other=s.connect(p)
 try:assert runs.get_run(other,r['id'])['metrics']==v['metrics']
 finally:other.close()
def test_same_request_is_idempotent_and_mismatch_rejected(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;a=reserve();assert reserve()==a
 with pytest.raises(ValueError):reserve(input_tokens=31)
 assert runs.get_run(c,r['id'])['metrics']['attempts']==1
def test_attempt_limit_no_reset(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;reserve();reserve('req-2')
 with pytest.raises(ValueError):reserve('req-3')
 assert runs.get_run(c,r['id'])['metrics']['attempts']==2
def test_total_limit_and_failed_attempt_rollback(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;reserve(input_tokens=100);before=runs.get_run(c,r['id'])['metrics']
 with pytest.raises(ValueError):reserve('req-2')
 assert runs.get_run(c,r['id'])['metrics']==before
def test_limits_cannot_change_after_first_reservation(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;reserve()
 with pytest.raises(ValueError):reserve('req-2',config=cfg(max_request_attempts_per_run=5))
 assert runs.get_run(c,r['id'])['metrics']['attempts']==1
@pytest.mark.parametrize('kw',[{'input_tokens':True},{'input_tokens':101},{'max_output_tokens':41},{'stage':'publish'}])
def test_invalid_request_does_not_mutate(db,kw):
 c,cam,r,cfg,reserve,runs,b,s,p=db
 with pytest.raises(ValueError):reserve(**kw)
 assert runs.get_run(c,r['id'])['metrics']=={'attempts':0}
def test_stale_brief_and_nonrunning_rejected(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db;runs.transition_run(c,r['id'],'waiting_input','ask')
 with pytest.raises(ValueError):reserve()
 runs.transition_run(c,r['id'],'running','generate');c.execute('UPDATE campaign SET config_revision=config_revision+1 WHERE id=?',(cam['id'],))
 with pytest.raises(ValueError):reserve()
 assert runs.get_run(c,r['id'])['metrics']['attempts']==0
def test_concurrent_reservations_cannot_exceed_limit(db):
 c,cam,r,cfg,reserve,runs,b,s,p=db
 def worker(n):
  con=s.connect(p)
  try:
   try:return b.reserve_call(con,r['id'],'request-'+str(n),stage='generator',input_tokens=30,max_output_tokens=40,config=cfg(max_request_attempts_per_run=1))
   except ValueError:return None
  finally:con.close()
 with ThreadPoolExecutor(max_workers=2) as ex:results=list(ex.map(worker,[1,2]))
 assert sum(x is not None for x in results)==1 and runs.get_run(c,r['id'])['metrics']['attempts']==1
 assert 'SYNTHETIC-KEY-NOT-REAL' not in c.execute('SELECT metrics_json FROM generation_run WHERE id=?',(r['id'],)).fetchone()[0]
