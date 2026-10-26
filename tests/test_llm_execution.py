import os,sys,json
from pathlib import Path
import pytest
@pytest.fixture
def env(tmp_path,monkeypatch):
 monkeypatch.syspath_prepend(os.environ['GWA_EXECUTION_CANDIDATE'])
 for k in list(sys.modules):
  if k=='app' or k.startswith('app.'):monkeypatch.delitem(sys.modules,k,raising=False)
 from app import storage,campaigns,runs,llm_execution
 from app.config import AppConfig
 from app.llm_client import LLMResult,LLMError
 p=tmp_path/'execution.sqlite';storage.initialize(p,Path(os.environ['GWA_SCHEMA_FILE']));c=storage.connect(p);cam=campaigns.create_campaign(c,'Synthetic','AI','Goal',formats=['email']);r=runs.create_run(c,cam['id']);runs.transition_run(c,r['id'],'running','generate')
 cfg=AppConfig(host='127.0.0.1',port=8501,llm_enabled=True,model='qwen/qwen3.8-flash',api_key='SYNTHETIC-KEY-NOT-REAL',api_base='https://openrouter.ai/api/v1',max_input_tokens=12000,max_output_tokens=4096,max_total_tokens_per_run=64000,max_request_attempts_per_run=8,max_retries=2,timeout_seconds=30,budget_control='user_managed_api_key');calls=[]
 class Client:
  def complete(self,messages,*,request_id):calls.append((messages,request_id));return LLMResult(text='Synthetic draft',model=cfg.model,input_tokens=20,output_tokens=4,request_id=request_id)
 msgs=[{'role':'user','content':'Synthetic source'}]
 def call(*,client=None,messages=None,conn=None):return llm_execution.execute_call(conn or c,r['id'],'call-1',messages or msgs,stage='generator',config=cfg,client=client or Client())
 yield c,p,r,cfg,calls,Client,msgs,call,llm_execution,storage,runs,LLMError
 c.close()
def test_durable_single_call_and_restart_replay(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env;x=call();assert x.text=='Synthetic draft' and len(calls)==1
 other=s.connect(p)
 try:y=call(conn=other);assert y==x and len(calls)==1
 finally:other.close()
 v=runs.get_run(c,r['id']);assert v['metrics']['attempts']==1 and v['metrics']['llm_calls']['call-1']['status']=='completed';assert 'SYNTHETIC-KEY-NOT-REAL' not in v['metrics_json']
def test_same_id_changed_message_rejected_even_same_length(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env;call()
 with pytest.raises(ValueError):call(messages=[{'role':'user','content':'Synthetic danger'}])
 assert len(calls)==1
def test_timeout_unknown_never_repeated(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env
 class Bad:
  def complete(self,*a,**kw):calls.append('bad');raise E('provider_transport',outcome_unknown=True)
 with pytest.raises(E):call(client=Bad())
 with pytest.raises(e.CallOutcomeUnknown):call()
 assert calls==['bad'] and runs.get_run(c,r['id'])['metrics']['llm_calls']['call-1']['status']=='uncertain'
def test_crash_after_reservation_never_repeats_on_restart(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env
 class Crash:
  def complete(self,*a,**kw):raise KeyboardInterrupt()
 with pytest.raises(KeyboardInterrupt):call(client=Crash())
 other=s.connect(p)
 try:
  with pytest.raises(e.CallOutcomeUnknown):call(conn=other)
 finally:other.close()
 assert calls==[] and runs.get_run(c,r['id'])['metrics']['attempts']==1
def test_known_failure_replayed_without_new_call(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env
 class Bad:
  def complete(self,*a,**kw):calls.append('bad');raise E('provider_auth')
 with pytest.raises(E):call(client=Bad())
 with pytest.raises(E) as ex:call()
 assert ex.value.code=='provider_auth' and calls==['bad']
def test_input_validation_precedes_reservation(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env
 with pytest.raises(ValueError):call(messages=[{'role':'tool','content':'X'}])
 assert calls==[] and runs.get_run(c,r['id'])['metrics']['attempts']==0
def test_no_network_under_caller_transaction(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env;c.execute('BEGIN IMMEDIATE')
 try:
  with pytest.raises(ValueError):call()
 finally:c.rollback()
 assert calls==[]
def test_billing_metadata_survives_replay_and_persistence(env):
 c,p,r,cfg,calls,C,msgs,call,e,s,runs,E=env
 from app.llm_client import LLMResult
 class Metadata:
  def complete(self,messages,*,request_id):calls.append(1);return LLMResult(text='Synthetic draft',model=cfg.model,input_tokens=20,output_tokens=4,request_id=request_id,provider='Synthetic provider',reported_cost='0.00002',response_id='gen-synthetic')
 x=call(client=Metadata());assert x.provider=='Synthetic provider' and x.reported_cost=='0.00002' and x.response_id=='gen-synthetic'
 other=s.connect(p)
 try:y=call(conn=other);assert y==x and calls==[1]
 finally:other.close()
 assert runs.get_run(c,r['id'])['metrics']['llm_calls']['call-1']['result']['reported_cost']=='0.00002'
